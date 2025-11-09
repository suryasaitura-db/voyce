"""
Data synchronization service between PostgreSQL and Databricks.
Handles bidirectional sync of voice submissions and AI analysis results.
"""
import logging
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import pandas as pd
from sqlalchemy import select, and_, or_, update, insert, text
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.database import engine, async_session_maker
from app.config import settings
from models.submission import VoiceSubmission
from models.analysis import Analysis
from services.databricks_client import get_databricks_client, DatabricksClient

logger = logging.getLogger(__name__)


class SyncMetadata:
    """Track sync metadata for incremental syncing."""

    @staticmethod
    async def create_metadata_table():
        """Create sync_metadata table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS sync_metadata (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            sync_type VARCHAR(50) NOT NULL,
            table_name VARCHAR(100) NOT NULL,
            last_sync_timestamp TIMESTAMP WITH TIME ZONE,
            last_sync_id VARCHAR(36),
            records_synced INTEGER DEFAULT 0,
            sync_status VARCHAR(50) DEFAULT 'pending',
            error_message TEXT,
            sync_duration_seconds FLOAT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            UNIQUE(sync_type, table_name)
        );

        CREATE INDEX IF NOT EXISTS idx_sync_metadata_type_table
        ON sync_metadata(sync_type, table_name);
        """

        if engine:
            async with engine.begin() as conn:
                await conn.execute(text(create_table_sql))
                logger.info("Sync metadata table created/verified")

    @staticmethod
    async def get_last_sync_timestamp(
        sync_type: str,
        table_name: str,
        session: AsyncSession
    ) -> Optional[datetime]:
        """Get the timestamp of the last successful sync."""
        query = text("""
            SELECT last_sync_timestamp
            FROM sync_metadata
            WHERE sync_type = :sync_type
            AND table_name = :table_name
            AND sync_status = 'completed'
            ORDER BY updated_at DESC
            LIMIT 1
        """)

        result = await session.execute(
            query,
            {"sync_type": sync_type, "table_name": table_name}
        )
        row = result.fetchone()
        return row[0] if row else None

    @staticmethod
    async def update_sync_metadata(
        sync_type: str,
        table_name: str,
        records_synced: int,
        sync_status: str,
        session: AsyncSession,
        last_sync_id: Optional[str] = None,
        error_message: Optional[str] = None,
        sync_duration: Optional[float] = None
    ):
        """Update sync metadata after a sync operation."""
        now = datetime.utcnow()

        upsert_query = text("""
            INSERT INTO sync_metadata
            (sync_type, table_name, last_sync_timestamp, last_sync_id,
             records_synced, sync_status, error_message, sync_duration_seconds, updated_at)
            VALUES
            (:sync_type, :table_name, :last_sync_timestamp, :last_sync_id,
             :records_synced, :sync_status, :error_message, :sync_duration, :updated_at)
            ON CONFLICT (sync_type, table_name)
            DO UPDATE SET
                last_sync_timestamp = EXCLUDED.last_sync_timestamp,
                last_sync_id = EXCLUDED.last_sync_id,
                records_synced = EXCLUDED.records_synced,
                sync_status = EXCLUDED.sync_status,
                error_message = EXCLUDED.error_message,
                sync_duration_seconds = EXCLUDED.sync_duration_seconds,
                updated_at = EXCLUDED.updated_at
        """)

        await session.execute(upsert_query, {
            "sync_type": sync_type,
            "table_name": table_name,
            "last_sync_timestamp": now,
            "last_sync_id": last_sync_id,
            "records_synced": records_synced,
            "sync_status": sync_status,
            "error_message": error_message,
            "sync_duration": sync_duration,
            "updated_at": now
        })
        await session.commit()


class DataSyncService:
    """Main service for synchronizing data between PostgreSQL and Databricks."""

    def __init__(
        self,
        batch_size: int = 1000,
        sync_interval_minutes: int = 60,
        max_retries: int = 3,
        databricks_client: Optional[DatabricksClient] = None
    ):
        """
        Initialize sync service.

        Args:
            batch_size: Number of records to process in each batch
            sync_interval_minutes: How often to sync (for reference)
            max_retries: Maximum retry attempts for failed operations
            databricks_client: Optional Databricks client instance
        """
        self.batch_size = batch_size
        self.sync_interval_minutes = sync_interval_minutes
        self.max_retries = max_retries
        self.db_client = databricks_client or get_databricks_client()

        # Track sync statistics
        self.stats: Dict[str, Any] = {
            "total_synced": 0,
            "submissions_to_databricks": 0,
            "analyses_to_postgres": 0,
            "errors": 0,
            "last_sync": None
        }

    async def initialize(self):
        """Initialize sync service and create required tables."""
        logger.info("Initializing Data Sync Service")

        # Create sync metadata table
        await SyncMetadata.create_metadata_table()

        # Ensure Databricks tables exist
        await self._create_databricks_tables()

        logger.info("Data Sync Service initialized successfully")

    async def _create_databricks_tables(self):
        """Create Delta tables in Databricks if they don't exist."""
        logger.info("Creating Databricks tables if not exist")

        # Voice submissions table
        submissions_schema = """
            id STRING NOT NULL,
            user_id STRING NOT NULL,
            file_path STRING,
            file_name STRING,
            file_size BIGINT,
            file_format STRING,
            mime_type STRING,
            duration DOUBLE,
            sample_rate INT,
            channels INT,
            title STRING,
            description STRING,
            tags STRING,
            category STRING,
            source STRING,
            source_url STRING,
            user_agent STRING,
            status STRING,
            is_processed BOOLEAN,
            is_transcribed BOOLEAN,
            is_analyzed BOOLEAN,
            is_public BOOLEAN,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            processed_at TIMESTAMP,
            error_message STRING,
            retry_count INT,
            synced_at TIMESTAMP
        """

        self.db_client.create_table_if_not_exists(
            "voice_submissions",
            submissions_schema
        )

        # AI analyses table
        analyses_schema = """
            id STRING NOT NULL,
            submission_id STRING NOT NULL,
            transcription_id STRING NOT NULL,
            sentiment STRING,
            sentiment_score DOUBLE,
            sentiment_confidence DOUBLE,
            sentiment_breakdown STRING,
            emotions STRING,
            dominant_emotion STRING,
            emotion_confidence DOUBLE,
            intent STRING,
            intent_confidence DOUBLE,
            sub_intents STRING,
            summary STRING,
            key_points STRING,
            action_items STRING,
            topics STRING,
            categories STRING,
            tags STRING,
            entities STRING,
            keywords STRING,
            clarity_score DOUBLE,
            urgency_score DOUBLE,
            importance_score DOUBLE,
            is_actionable BOOLEAN,
            requires_follow_up BOOLEAN,
            is_complaint BOOLEAN,
            is_positive_feedback BOOLEAN,
            model STRING,
            model_version STRING,
            provider STRING,
            processing_time DOUBLE,
            prompt_tokens INT,
            completion_tokens INT,
            total_tokens INT,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            error_message STRING,
            synced_at TIMESTAMP
        """

        self.db_client.create_table_if_not_exists(
            "ai_analyses",
            analyses_schema
        )

        logger.info("Databricks tables created/verified")

    async def sync_submissions_to_databricks(
        self,
        incremental: bool = True,
        force_full_sync: bool = False
    ) -> Dict[str, Any]:
        """
        Sync voice submissions from PostgreSQL to Databricks.

        Args:
            incremental: Only sync new/updated records since last sync
            force_full_sync: Force a full sync regardless of last sync time

        Returns:
            Dictionary with sync statistics
        """
        start_time = datetime.utcnow()
        sync_type = "pg_to_databricks"
        table_name = "voice_submissions"

        logger.info(f"Starting sync: {table_name} (incremental: {incremental})")

        try:
            async with async_session_maker() as session:
                # Get last sync timestamp
                last_sync = None
                if incremental and not force_full_sync:
                    last_sync = await SyncMetadata.get_last_sync_timestamp(
                        sync_type, table_name, session
                    )

                # Build query for records to sync
                query = select(VoiceSubmission)

                if last_sync:
                    # Only sync records updated since last sync
                    query = query.where(VoiceSubmission.updated_at > last_sync)
                    logger.info(f"Incremental sync from {last_sync}")
                else:
                    logger.info("Full sync - no previous sync found")

                # Order by updated_at for incremental processing
                query = query.order_by(VoiceSubmission.updated_at)

                # Execute query
                result = await session.execute(query)
                submissions = result.scalars().all()

                total_records = len(submissions)
                logger.info(f"Found {total_records} records to sync")

                if total_records == 0:
                    await SyncMetadata.update_sync_metadata(
                        sync_type, table_name, 0, "completed", session,
                        sync_duration=(datetime.utcnow() - start_time).total_seconds()
                    )
                    return {
                        "status": "completed",
                        "records_synced": 0,
                        "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
                    }

                # Process in batches
                synced_count = 0
                last_id = None

                for i in range(0, total_records, self.batch_size):
                    batch = submissions[i:i + self.batch_size]
                    batch_df = self._submissions_to_dataframe(batch)

                    # Add sync timestamp
                    batch_df['synced_at'] = datetime.utcnow()

                    # Write to Databricks
                    self.db_client.write_to_delta(
                        batch_df,
                        table_name,
                        mode="merge",
                        merge_keys=["id"]
                    )

                    synced_count += len(batch)
                    last_id = str(batch[-1].id)

                    logger.info(f"Synced batch {i // self.batch_size + 1}: {synced_count}/{total_records} records")

                # Update sync metadata
                duration = (datetime.utcnow() - start_time).total_seconds()
                await SyncMetadata.update_sync_metadata(
                    sync_type, table_name, synced_count, "completed", session,
                    last_sync_id=last_id,
                    sync_duration=duration
                )

                # Update stats
                self.stats["submissions_to_databricks"] += synced_count
                self.stats["total_synced"] += synced_count
                self.stats["last_sync"] = datetime.utcnow()

                logger.info(f"Sync completed: {synced_count} records in {duration:.2f}s")

                return {
                    "status": "completed",
                    "records_synced": synced_count,
                    "duration_seconds": duration,
                    "last_id": last_id
                }

        except Exception as e:
            logger.error(f"Error syncing submissions to Databricks: {e}", exc_info=True)

            # Update metadata with error
            async with async_session_maker() as session:
                await SyncMetadata.update_sync_metadata(
                    sync_type, table_name, 0, "failed", session,
                    error_message=str(e),
                    sync_duration=(datetime.utcnow() - start_time).total_seconds()
                )

            self.stats["errors"] += 1

            return {
                "status": "failed",
                "error": str(e),
                "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
            }

    async def sync_analyses_to_postgres(
        self,
        incremental: bool = True,
        force_full_sync: bool = False
    ) -> Dict[str, Any]:
        """
        Sync AI analyses from Databricks back to PostgreSQL.

        Args:
            incremental: Only sync new/updated records
            force_full_sync: Force full sync

        Returns:
            Dictionary with sync statistics
        """
        start_time = datetime.utcnow()
        sync_type = "databricks_to_pg"
        table_name = "ai_analyses"

        logger.info(f"Starting sync: {table_name} (incremental: {incremental})")

        try:
            async with async_session_maker() as session:
                # Get last sync timestamp
                last_sync = None
                if incremental and not force_full_sync:
                    last_sync = await SyncMetadata.get_last_sync_timestamp(
                        sync_type, table_name, session
                    )

                # Build query for Databricks
                where_clause = None
                if last_sync:
                    where_clause = f"synced_at > '{last_sync.isoformat()}'"
                    logger.info(f"Incremental sync from {last_sync}")
                else:
                    logger.info("Full sync - no previous sync found")

                # Read from Databricks
                df = self.db_client.read_from_delta(
                    table_name,
                    where=where_clause
                )

                total_records = len(df)
                logger.info(f"Found {total_records} records to sync")

                if total_records == 0:
                    await SyncMetadata.update_sync_metadata(
                        sync_type, table_name, 0, "completed", session,
                        sync_duration=(datetime.utcnow() - start_time).total_seconds()
                    )
                    return {
                        "status": "completed",
                        "records_synced": 0,
                        "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
                    }

                # Process in batches
                synced_count = 0
                last_id = None

                for i in range(0, total_records, self.batch_size):
                    batch_df = df.iloc[i:i + self.batch_size]

                    # Convert to Analysis objects
                    for _, row in batch_df.iterrows():
                        analysis_data = self._dataframe_row_to_analysis(row)

                        # Upsert into PostgreSQL
                        await self._upsert_analysis(session, analysis_data)

                    synced_count += len(batch_df)
                    last_id = str(batch_df.iloc[-1]['id'])

                    await session.commit()

                    logger.info(f"Synced batch {i // self.batch_size + 1}: {synced_count}/{total_records} records")

                # Update sync metadata
                duration = (datetime.utcnow() - start_time).total_seconds()
                await SyncMetadata.update_sync_metadata(
                    sync_type, table_name, synced_count, "completed", session,
                    last_sync_id=last_id,
                    sync_duration=duration
                )

                # Update stats
                self.stats["analyses_to_postgres"] += synced_count
                self.stats["total_synced"] += synced_count
                self.stats["last_sync"] = datetime.utcnow()

                logger.info(f"Sync completed: {synced_count} records in {duration:.2f}s")

                return {
                    "status": "completed",
                    "records_synced": synced_count,
                    "duration_seconds": duration,
                    "last_id": last_id
                }

        except Exception as e:
            logger.error(f"Error syncing analyses to PostgreSQL: {e}", exc_info=True)

            # Update metadata with error
            async with async_session_maker() as session:
                await SyncMetadata.update_sync_metadata(
                    sync_type, table_name, 0, "failed", session,
                    error_message=str(e),
                    sync_duration=(datetime.utcnow() - start_time).total_seconds()
                )

            self.stats["errors"] += 1

            return {
                "status": "failed",
                "error": str(e),
                "duration_seconds": (datetime.utcnow() - start_time).total_seconds()
            }

    async def full_bidirectional_sync(self) -> Dict[str, Any]:
        """
        Perform full bidirectional sync.

        Returns:
            Combined sync statistics
        """
        logger.info("Starting full bidirectional sync")
        start_time = datetime.utcnow()

        # Sync submissions to Databricks
        submissions_result = await self.sync_submissions_to_databricks()

        # Sync analyses back to PostgreSQL
        analyses_result = await self.sync_analyses_to_postgres()

        duration = (datetime.utcnow() - start_time).total_seconds()

        result = {
            "status": "completed" if submissions_result["status"] == "completed" and analyses_result["status"] == "completed" else "partial",
            "submissions_to_databricks": submissions_result,
            "analyses_to_postgres": analyses_result,
            "total_duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat()
        }

        logger.info(f"Bidirectional sync completed in {duration:.2f}s")

        return result

    async def validate_sync(self) -> Dict[str, Any]:
        """
        Validate sync by comparing record counts.

        Returns:
            Validation results
        """
        logger.info("Validating sync")

        async with async_session_maker() as session:
            # Count submissions in PostgreSQL
            pg_count_query = select(VoiceSubmission).count()
            pg_count = await session.scalar(pg_count_query)

            # Count submissions in Databricks
            db_stats = self.db_client.get_table_stats("voice_submissions")
            db_count = db_stats["row_count"]

            validation = {
                "voice_submissions": {
                    "postgresql_count": pg_count,
                    "databricks_count": db_count,
                    "difference": abs(pg_count - db_count),
                    "in_sync": pg_count == db_count
                }
            }

            logger.info(f"Validation: PG={pg_count}, DB={db_count}")

            return validation

    def _submissions_to_dataframe(self, submissions: List[VoiceSubmission]) -> pd.DataFrame:
        """Convert list of VoiceSubmission objects to pandas DataFrame."""
        data = []
        for submission in submissions:
            record = {
                "id": str(submission.id),
                "user_id": str(submission.user_id),
                "file_path": submission.file_path,
                "file_name": submission.file_name,
                "file_size": submission.file_size,
                "file_format": submission.file_format,
                "mime_type": submission.mime_type,
                "duration": submission.duration,
                "sample_rate": submission.sample_rate,
                "channels": submission.channels,
                "title": submission.title,
                "description": submission.description,
                "tags": str(submission.tags) if submission.tags else None,
                "category": submission.category,
                "source": submission.source,
                "source_url": submission.source_url,
                "user_agent": submission.user_agent,
                "status": submission.status,
                "is_processed": submission.is_processed,
                "is_transcribed": submission.is_transcribed,
                "is_analyzed": submission.is_analyzed,
                "is_public": submission.is_public,
                "created_at": submission.created_at,
                "updated_at": submission.updated_at,
                "processed_at": submission.processed_at,
                "error_message": submission.error_message,
                "retry_count": submission.retry_count
            }
            data.append(record)

        return pd.DataFrame(data)

    def _dataframe_row_to_analysis(self, row: pd.Series) -> Dict[str, Any]:
        """Convert DataFrame row to Analysis dictionary."""
        import json

        def safe_json_loads(value):
            if pd.isna(value) or value is None:
                return None
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except:
                    return None
            return value

        return {
            "id": row.get("id"),
            "submission_id": row.get("submission_id"),
            "transcription_id": row.get("transcription_id"),
            "sentiment": row.get("sentiment"),
            "sentiment_score": row.get("sentiment_score"),
            "sentiment_confidence": row.get("sentiment_confidence"),
            "sentiment_breakdown": safe_json_loads(row.get("sentiment_breakdown")),
            "emotions": safe_json_loads(row.get("emotions")),
            "dominant_emotion": row.get("dominant_emotion"),
            "emotion_confidence": row.get("emotion_confidence"),
            "intent": row.get("intent"),
            "intent_confidence": row.get("intent_confidence"),
            "sub_intents": safe_json_loads(row.get("sub_intents")),
            "summary": row.get("summary"),
            "key_points": safe_json_loads(row.get("key_points")),
            "action_items": safe_json_loads(row.get("action_items")),
            "topics": safe_json_loads(row.get("topics")),
            "categories": safe_json_loads(row.get("categories")),
            "tags": safe_json_loads(row.get("tags")),
            "entities": safe_json_loads(row.get("entities")),
            "keywords": safe_json_loads(row.get("keywords")),
            "clarity_score": row.get("clarity_score"),
            "urgency_score": row.get("urgency_score"),
            "importance_score": row.get("importance_score"),
            "is_actionable": row.get("is_actionable"),
            "requires_follow_up": row.get("requires_follow_up"),
            "is_complaint": row.get("is_complaint"),
            "is_positive_feedback": row.get("is_positive_feedback"),
            "model": row.get("model"),
            "model_version": row.get("model_version"),
            "provider": row.get("provider"),
            "processing_time": row.get("processing_time"),
            "prompt_tokens": row.get("prompt_tokens"),
            "completion_tokens": row.get("completion_tokens"),
            "total_tokens": row.get("total_tokens"),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
            "error_message": row.get("error_message")
        }

    async def _upsert_analysis(self, session: AsyncSession, analysis_data: Dict[str, Any]):
        """Upsert analysis into PostgreSQL."""
        # Check if exists
        existing = await session.get(Analysis, analysis_data["id"])

        if existing:
            # Update existing
            for key, value in analysis_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
        else:
            # Insert new
            analysis = Analysis(**analysis_data)
            session.add(analysis)

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status and statistics."""
        async with async_session_maker() as session:
            query = text("""
                SELECT sync_type, table_name, last_sync_timestamp,
                       records_synced, sync_status, sync_duration_seconds
                FROM sync_metadata
                ORDER BY updated_at DESC
            """)

            result = await session.execute(query)
            rows = result.fetchall()

            sync_history = [
                {
                    "sync_type": row[0],
                    "table_name": row[1],
                    "last_sync_timestamp": row[2].isoformat() if row[2] else None,
                    "records_synced": row[3],
                    "sync_status": row[4],
                    "sync_duration_seconds": row[5]
                }
                for row in rows
            ]

            return {
                "current_stats": self.stats,
                "sync_history": sync_history
            }

    def cleanup(self):
        """Clean up resources."""
        if self.db_client:
            self.db_client.close()
        logger.info("Sync service cleaned up")


# Global sync service instance
_sync_service: Optional[DataSyncService] = None


async def get_sync_service(
    batch_size: int = 1000,
    sync_interval_minutes: int = 60
) -> DataSyncService:
    """Get or create sync service instance."""
    global _sync_service

    if _sync_service is None:
        _sync_service = DataSyncService(
            batch_size=batch_size,
            sync_interval_minutes=sync_interval_minutes
        )
        await _sync_service.initialize()

    return _sync_service
