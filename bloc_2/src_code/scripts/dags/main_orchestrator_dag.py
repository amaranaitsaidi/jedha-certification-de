"""
Main Orchestrator DAG
=====================
Orchestrates the complete Amazon Review ETL pipeline:
1. Setup connections (optional, can be done manually)
2. Initialize MongoDB collections
3. Initialize Snowflake tables
4. Trigger the extraction and transformation pipeline

This DAG can be run manually or scheduled.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.hooks.base import BaseHook
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def setup_mongodb_task():
    """Initialize MongoDB collections and indexes."""
    from pymongo import MongoClient, ASCENDING, DESCENDING

    logger.info("Setting up MongoDB collections...")

    # Get MongoDB connection from Airflow
    conn = BaseHook.get_connection("mongo")
    mongo_uri = conn.get_uri()

    client = MongoClient(mongo_uri)
    db = client['amazon_reviews']

    logger.info(f"Connected to MongoDB: {db.name}")

    # Create rejected_reviews collection
    if 'rejected_reviews' not in db.list_collection_names():
        db.create_collection('rejected_reviews')
        rejected_collection = db['rejected_reviews']
        rejected_collection.create_index([('review_id', ASCENDING)], name='idx_rejected_review_id')
        rejected_collection.create_index([('rejection_reason', ASCENDING)], name='idx_rejection_reason')
        rejected_collection.create_index([('rejected_at', DESCENDING)], name='idx_rejected_at_desc')
        logger.info("Created rejected_reviews collection with indexes")
    else:
        logger.info("rejected_reviews collection already exists")

    # Create pipeline_metadata collection
    if 'pipeline_metadata' not in db.list_collection_names():
        db.create_collection('pipeline_metadata')
        metadata_collection = db['pipeline_metadata']
        metadata_collection.create_index([('execution_timestamp', DESCENDING)], name='idx_execution_timestamp_desc')
        metadata_collection.create_index([('run_id', ASCENDING)], name='idx_run_id')
        logger.info("Created pipeline_metadata collection with indexes")
    else:
        logger.info("pipeline_metadata collection already exists")

    # Create airflow_logs collections for logging
    if 'airflow_logs' not in db.list_collection_names():
        db.create_collection('airflow_logs')
        logger.info("Created airflow_logs database")

    client.close()
    logger.info("[OK] MongoDB setup completed")

    return "MongoDB setup successful"


def setup_snowflake_task():
    """Initialize Snowflake database, schema, and tables."""
    import snowflake.connector

    logger.info("Setting up Snowflake database and tables...")

    # Get Snowflake connection from Airflow
    conn_hook = BaseHook.get_connection("snowflake_conn")

    # Parse connection details
    schema_raw = conn_hook.extra_dejson.get("schema") or conn_hook.schema or ""
    database, schema = schema_raw.split("/", 1) if "/" in schema_raw else (schema_raw, "PUBLIC")

    # Connect to Snowflake
    conn = snowflake.connector.connect(
        user=conn_hook.login,
        password=conn_hook.password,
        account=conn_hook.extra_dejson.get("account") or conn_hook.host,
        warehouse=conn_hook.extra_dejson.get("warehouse"),
        role=conn_hook.extra_dejson.get("role"),
    )

    cursor = conn.cursor()

    # Create database and schema if they don't exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
    cursor.execute(f"USE DATABASE {database}")
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    cursor.execute(f"USE SCHEMA {schema}")

    logger.info(f"Using database: {database}, schema: {schema}")

    # Create reviews table
    cursor.execute("""
        CREATE OR REPLACE TABLE reviews (
            review_id VARCHAR(50) PRIMARY KEY,
            buyer_id VARCHAR(100),
            p_id VARCHAR(50),
            product_name VARCHAR(500),
            category VARCHAR(100),
            title VARCHAR(500),
            description TEXT,
            rating SMALLINT NOT NULL,
            text_length INTEGER,
            has_image BOOLEAN DEFAULT FALSE,
            has_orders BOOLEAN DEFAULT FALSE,
            review_img VARCHAR(500),
            ingestion_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            pipeline_version VARCHAR(20)
        )
    """)

    logger.info("Created or verified reviews table")

    cursor.close()
    conn.close()

    logger.info("[OK] Snowflake setup completed")

    return "Snowflake setup successful"


# Create the DAG
with DAG(
    dag_id='main_orchestrator',
    default_args=default_args,
    description='Main orchestrator for Amazon Review ETL pipeline',
    schedule_interval=None,  # Manual trigger or set to '@daily' for daily runs
    catchup=False,
    tags=['orchestrator', 'etl', 'amazon'],
) as dag:

    # Task 1: Setup MongoDB
    setup_mongo = PythonOperator(
        task_id='setup_mongodb',
        python_callable=setup_mongodb_task,
    )

    # Task 2: Setup Snowflake
    setup_snowflake = PythonOperator(
        task_id='setup_snowflake',
        python_callable=setup_snowflake_task,
    )

    # Task 3: Trigger the extraction pipeline
    trigger_extraction = TriggerDagRunOperator(
        task_id='trigger_extraction_pipeline',
        trigger_dag_id='extract_postgres_to_s3',
        wait_for_completion=False,
        reset_dag_run=True,
    )

    # Define task dependencies
    # Setup tasks run in parallel, then trigger extraction
    [setup_mongo, setup_snowflake] >> trigger_extraction
