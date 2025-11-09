"""
Databricks connection utilities for data synchronization.
Provides JDBC connections, Delta Lake operations, Unity Catalog management, and Volume file operations.
"""
from databricks import sql
from databricks.sdk import WorkspaceClient
from databricks.sdk.core import Config
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType, BooleanType, TimestampType
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
import os
from contextlib import contextmanager
import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)


class DatabricksClient:
    """Client for interacting with Databricks SQL, Delta Lake, and Unity Catalog."""

    def __init__(
        self,
        profile: str = "DEFAULT",
        server_hostname: Optional[str] = None,
        http_path: Optional[str] = None,
        access_token: Optional[str] = None,
        catalog: Optional[str] = None,
        schema: Optional[str] = None
    ):
        """
        Initialize Databricks client.

        Args:
            profile: Databricks profile name from ~/.databrickscfg
            server_hostname: Databricks server hostname (overrides profile)
            http_path: Databricks HTTP path (overrides profile)
            access_token: Databricks access token (overrides profile)
            catalog: Unity Catalog name
            schema: Schema name within catalog
        """
        self.profile = profile
        self.server_hostname = server_hostname or settings.DATABRICKS_SERVER_HOSTNAME
        self.http_path = http_path or settings.DATABRICKS_HTTP_PATH
        self.access_token = access_token or settings.DATABRICKS_ACCESS_TOKEN
        self.catalog = catalog or settings.DATABRICKS_CATALOG
        self.schema = schema or settings.DATABRICKS_SCHEMA

        # Initialize connection (lazy - will connect on first use)
        self._connection = None
        self._workspace_client = None
        self._spark = None

    def _get_connection_params(self) -> Dict[str, str]:
        """Get connection parameters, using profile or explicit credentials."""
        params = {}

        # If explicit credentials provided, use them
        if self.server_hostname and self.http_path and self.access_token:
            params = {
                "server_hostname": self.server_hostname,
                "http_path": self.http_path,
                "access_token": self.access_token
            }
        else:
            # Use profile from ~/.databrickscfg
            config = Config(profile=self.profile)
            params = {
                "server_hostname": config.host.replace("https://", ""),
                "http_path": self.http_path or config.http_path,
                "access_token": config.token
            }

        return params

    @contextmanager
    def get_connection(self):
        """
        Get a database connection using context manager.

        Usage:
            with client.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM table")
        """
        params = self._get_connection_params()

        connection = sql.connect(
            server_hostname=params["server_hostname"],
            http_path=params["http_path"],
            access_token=params["access_token"]
        )

        try:
            yield connection
        finally:
            connection.close()

    def get_workspace_client(self) -> WorkspaceClient:
        """Get Databricks Workspace client for SDK operations."""
        if self._workspace_client is None:
            params = self._get_connection_params()
            self._workspace_client = WorkspaceClient(
                host=f"https://{params['server_hostname']}",
                token=params["access_token"]
            )
        return self._workspace_client

    def get_spark_session(self) -> SparkSession:
        """
        Get or create Spark session for PySpark operations.
        Note: This requires running on a Databricks cluster or with Spark installed.
        """
        if self._spark is None:
            params = self._get_connection_params()

            self._spark = (
                SparkSession.builder
                .appName("VoyceDataSync")
                .config("spark.databricks.service.server.enabled", "true")
                .config("spark.databricks.service.address", params["server_hostname"])
                .config("spark.databricks.service.token", params["access_token"])
                .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
                .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
                .getOrCreate()
            )
        return self._spark

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        catalog: Optional[str] = None,
        schema: Optional[str] = None
    ) -> List[tuple]:
        """
        Execute a SQL query and return results.

        Args:
            query: SQL query to execute
            parameters: Query parameters for prepared statements
            catalog: Catalog to use (defaults to instance catalog)
            schema: Schema to use (defaults to instance schema)

        Returns:
            List of result tuples
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Set catalog and schema
            if catalog:
                cursor.execute(f"USE CATALOG {catalog}")
            if schema:
                cursor.execute(f"USE SCHEMA {schema}")

            # Execute query
            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)

            # Fetch results
            try:
                results = cursor.fetchall()
                return results
            except Exception:
                # Query might not return results (INSERT, UPDATE, etc.)
                return []
            finally:
                cursor.close()

    def execute_statement(
        self,
        statement: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None
    ) -> None:
        """
        Execute a SQL statement without returning results.

        Args:
            statement: SQL statement to execute
            catalog: Catalog to use
            schema: Schema to use
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema

        with self.get_connection() as conn:
            cursor = conn.cursor()

            try:
                if catalog:
                    cursor.execute(f"USE CATALOG {catalog}")
                if schema:
                    cursor.execute(f"USE SCHEMA {schema}")

                cursor.execute(statement)
                logger.info(f"Executed statement successfully")
            finally:
                cursor.close()

    def write_to_delta(
        self,
        df: pd.DataFrame,
        table_name: str,
        mode: str = "append",
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
        partition_by: Optional[List[str]] = None,
        merge_keys: Optional[List[str]] = None
    ) -> None:
        """
        Write DataFrame to Delta Lake table using PySpark.

        Args:
            df: Pandas DataFrame to write
            table_name: Target table name
            mode: Write mode ('append', 'overwrite', 'merge')
            catalog: Catalog name
            schema: Schema name
            partition_by: Columns to partition by
            merge_keys: Keys to use for merge operations
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema
        full_table_name = f"{catalog}.{schema}.{table_name}"

        logger.info(f"Writing {len(df)} records to {full_table_name} (mode: {mode})")

        # Convert pandas DataFrame to Spark DataFrame
        spark = self.get_spark_session()
        spark_df = spark.createDataFrame(df)

        if mode == "merge" and merge_keys:
            # Perform merge operation
            self._merge_into_delta(spark_df, full_table_name, merge_keys)
        else:
            # Standard write operation
            writer = spark_df.write.format("delta").mode(mode)

            if partition_by:
                writer = writer.partitionBy(*partition_by)

            writer.saveAsTable(full_table_name)

        logger.info(f"Successfully wrote data to {full_table_name}")

    def _merge_into_delta(
        self,
        df: DataFrame,
        table_name: str,
        merge_keys: List[str]
    ) -> None:
        """
        Perform a merge (upsert) operation into Delta table.

        Args:
            df: Spark DataFrame with new data
            table_name: Full table name (catalog.schema.table)
            merge_keys: Columns to match on for merge
        """
        # Create temp view
        temp_view = f"temp_{table_name.replace('.', '_')}_{int(datetime.now().timestamp())}"
        df.createOrReplaceTempView(temp_view)

        # Build merge condition
        merge_condition = " AND ".join([f"target.{key} = source.{key}" for key in merge_keys])

        # Build update set clause
        columns = df.columns
        update_set = ", ".join([f"target.{col} = source.{col}" for col in columns])

        # Build insert values clause
        insert_columns = ", ".join(columns)
        insert_values = ", ".join([f"source.{col}" for col in columns])

        # Execute merge
        merge_query = f"""
        MERGE INTO {table_name} AS target
        USING {temp_view} AS source
        ON {merge_condition}
        WHEN MATCHED THEN
            UPDATE SET {update_set}
        WHEN NOT MATCHED THEN
            INSERT ({insert_columns})
            VALUES ({insert_values})
        """

        logger.info(f"Executing merge into {table_name}")
        self.execute_statement(merge_query)

    def read_from_delta(
        self,
        table_name: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
        where: Optional[str] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Read data from Delta Lake table.

        Args:
            table_name: Table name
            catalog: Catalog name
            schema: Schema name
            where: WHERE clause filter
            limit: Maximum number of rows to return

        Returns:
            Pandas DataFrame with results
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema
        full_table_name = f"{catalog}.{schema}.{table_name}"

        query = f"SELECT * FROM {full_table_name}"

        if where:
            query += f" WHERE {where}"

        if limit:
            query += f" LIMIT {limit}"

        logger.info(f"Reading from {full_table_name}")
        results = self.execute_query(query)

        # Convert to pandas DataFrame
        if results:
            # Get column names
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DESCRIBE TABLE {full_table_name}")
                columns = [row[0] for row in cursor.fetchall()]
                cursor.close()

            df = pd.DataFrame(results, columns=columns)
            logger.info(f"Read {len(df)} records from {full_table_name}")
            return df
        else:
            return pd.DataFrame()

    def table_exists(
        self,
        table_name: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None
    ) -> bool:
        """
        Check if a table exists.

        Args:
            table_name: Table name
            catalog: Catalog name
            schema: Schema name

        Returns:
            True if table exists, False otherwise
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema

        try:
            query = f"SHOW TABLES IN {catalog}.{schema} LIKE '{table_name}'"
            results = self.execute_query(query)
            return len(results) > 0
        except Exception as e:
            logger.warning(f"Error checking if table exists: {e}")
            return False

    def create_table_if_not_exists(
        self,
        table_name: str,
        schema_ddl: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None
    ) -> None:
        """
        Create a table if it doesn't exist.

        Args:
            table_name: Table name
            schema_ddl: Table schema DDL (columns definition)
            catalog: Catalog name
            schema: Schema name
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema
        full_table_name = f"{catalog}.{schema}.{table_name}"

        if not self.table_exists(table_name, catalog, schema):
            create_query = f"""
            CREATE TABLE {full_table_name} (
                {schema_ddl}
            )
            USING DELTA
            """

            logger.info(f"Creating table {full_table_name}")
            self.execute_statement(create_query)
            logger.info(f"Table {full_table_name} created successfully")
        else:
            logger.info(f"Table {full_table_name} already exists")

    def optimize_table(
        self,
        table_name: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None,
        z_order_by: Optional[List[str]] = None
    ) -> None:
        """
        Optimize Delta table (compaction and Z-ordering).

        Args:
            table_name: Table name
            catalog: Catalog name
            schema: Schema name
            z_order_by: Columns to Z-order by
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema
        full_table_name = f"{catalog}.{schema}.{table_name}"

        logger.info(f"Optimizing table {full_table_name}")

        optimize_query = f"OPTIMIZE {full_table_name}"

        if z_order_by:
            z_order_cols = ", ".join(z_order_by)
            optimize_query += f" ZORDER BY ({z_order_cols})"

        self.execute_statement(optimize_query)
        logger.info(f"Table {full_table_name} optimized successfully")

    def vacuum_table(
        self,
        table_name: str,
        retention_hours: int = 168,  # 7 days default
        catalog: Optional[str] = None,
        schema: Optional[str] = None
    ) -> None:
        """
        Vacuum Delta table to remove old files.

        Args:
            table_name: Table name
            retention_hours: Retention period in hours
            catalog: Catalog name
            schema: Schema name
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema
        full_table_name = f"{catalog}.{schema}.{table_name}"

        logger.info(f"Vacuuming table {full_table_name} (retention: {retention_hours}h)")

        vacuum_query = f"VACUUM {full_table_name} RETAIN {retention_hours} HOURS"
        self.execute_statement(vacuum_query)

        logger.info(f"Table {full_table_name} vacuumed successfully")

    def write_file_to_volume(
        self,
        local_path: str,
        volume_path: str
    ) -> str:
        """
        Upload a file to Databricks Volume.

        Args:
            local_path: Local file path
            volume_path: Volume path (e.g., /Volumes/catalog/schema/volume/file.txt)

        Returns:
            Volume file path
        """
        logger.info(f"Uploading {local_path} to {volume_path}")

        workspace = self.get_workspace_client()

        with open(local_path, 'rb') as f:
            content = f.read()
            workspace.files.upload(volume_path, content, overwrite=True)

        logger.info(f"File uploaded to {volume_path}")
        return volume_path

    def read_file_from_volume(
        self,
        volume_path: str,
        local_path: str
    ) -> str:
        """
        Download a file from Databricks Volume.

        Args:
            volume_path: Volume path
            local_path: Local destination path

        Returns:
            Local file path
        """
        logger.info(f"Downloading {volume_path} to {local_path}")

        workspace = self.get_workspace_client()

        # Create directory if needed
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Download file
        content = workspace.files.download(volume_path).contents

        with open(local_path, 'wb') as f:
            f.write(content.read())

        logger.info(f"File downloaded to {local_path}")
        return local_path

    def list_volume_files(
        self,
        volume_path: str
    ) -> List[str]:
        """
        List files in a Databricks Volume directory.

        Args:
            volume_path: Volume directory path

        Returns:
            List of file paths
        """
        workspace = self.get_workspace_client()

        files = workspace.files.list(volume_path)
        file_paths = [f.path for f in files]

        logger.info(f"Found {len(file_paths)} files in {volume_path}")
        return file_paths

    def get_table_stats(
        self,
        table_name: str,
        catalog: Optional[str] = None,
        schema: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get statistics for a Delta table.

        Args:
            table_name: Table name
            catalog: Catalog name
            schema: Schema name

        Returns:
            Dictionary with table statistics
        """
        catalog = catalog or self.catalog
        schema = schema or self.schema
        full_table_name = f"{catalog}.{schema}.{table_name}"

        # Get table details
        details_query = f"DESCRIBE DETAIL {full_table_name}"
        details = self.execute_query(details_query)

        # Get row count
        count_query = f"SELECT COUNT(*) as count FROM {full_table_name}"
        count_result = self.execute_query(count_query)
        row_count = count_result[0][0] if count_result else 0

        stats = {
            "table_name": full_table_name,
            "row_count": row_count,
            "details": details[0] if details else None
        }

        return stats

    def close(self):
        """Close all connections."""
        if self._spark:
            self._spark.stop()
            self._spark = None

        self._connection = None
        self._workspace_client = None

        logger.info("Databricks client connections closed")


# Global client instance (can be configured via settings)
_default_client: Optional[DatabricksClient] = None


def get_databricks_client() -> DatabricksClient:
    """Get or create default Databricks client."""
    global _default_client

    if _default_client is None:
        _default_client = DatabricksClient(
            profile="DEFAULT",
            server_hostname=settings.DATABRICKS_SERVER_HOSTNAME,
            http_path=settings.DATABRICKS_HTTP_PATH,
            access_token=settings.DATABRICKS_ACCESS_TOKEN,
            catalog=settings.DATABRICKS_CATALOG,
            schema=settings.DATABRICKS_SCHEMA
        )

    return _default_client
