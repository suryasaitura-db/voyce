# Databricks notebook source
"""
Example Databricks Notebook for Voyce
Uses [DEFAULT] profile and serverless compute
"""

# COMMAND ----------

# MAGIC %md
# MAGIC # Voyce - Example Notebook
# MAGIC
# MAGIC This notebook demonstrates:
# MAGIC - Using Databricks serverless compute
# MAGIC - SQL Serverless for analytics
# MAGIC - Integration with the Voyce application

# COMMAND ----------

# MAGIC %md
# MAGIC ## Setup and Configuration

# COMMAND ----------

import os
from databricks import sql
from databricks.sdk import WorkspaceClient

# Initialize Databricks client using DEFAULT profile
w = WorkspaceClient()

print(f"Connected to workspace: {w.config.host}")
print(f"Using serverless compute: True")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Example Data Processing

# COMMAND ----------

# MAGIC %sql
# MAGIC -- Example SQL query using SQL Serverless
# MAGIC SELECT 'Voyce' as app_name,
# MAGIC        current_timestamp() as timestamp,
# MAGIC        'serverless' as compute_type;

# COMMAND ----------

# MAGIC %md
# MAGIC ## Sample Data Operations

# COMMAND ----------

import pandas as pd
from pyspark.sql import SparkSession

# Create sample data
data = {
    'id': range(1, 11),
    'name': [f'Item_{i}' for i in range(1, 11)],
    'value': [i * 10 for i in range(1, 11)]
}

df = pd.DataFrame(data)
display(df)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Integration with Voyce Application

# COMMAND ----------

# Example: Process data and prepare for application
spark_df = spark.createDataFrame(df)
spark_df.createOrReplaceTempView("voyce_data")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT * FROM voyce_data
# MAGIC WHERE value > 50
# MAGIC ORDER BY value DESC

# COMMAND ----------

# MAGIC %md
# MAGIC ## End of Notebook
