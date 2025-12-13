import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
import sys
import os
import hashlib
import io
from utils.mongo_handler import MongoHandler
from dotenv import load_dotenv

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.hooks.base import BaseHook
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from utils.email_alerter import EmailAlerter



# Load environment variables
load_dotenv()


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# get Airflow connection "mongodb"
logger.info("Starting MongoDB logging handler setup...")
conn = BaseHook.get_connection("mongo")

# Get l'URI
mongo_uri = conn.get_uri()
logger.info(f"Using Mongo URI: {mongo_uri}")

# Add MongoDB handler to logger
mongo_handler = MongoHandler(
    uri=mongo_uri,
    db_name="airflow_logs",
    collection="extract_to_s3_logs"
)

mongo_handler.setLevel(logging.INFO)

# Avoid duplicate logs
if not any(isinstance(h, MongoHandler) for h in logger.handlers):
    logger.addHandler(mongo_handler)

class PostgresToS3Extractor:
    """Extract tables from PostgreSQL to S3"""
    def __init__(self, postgres_conn_id: str, aws_conn_id: str):
        self.pg_hook = PostgresHook(postgres_conn_id=postgres_conn_id)
        self.s3_hook = S3Hook(aws_conn_id=aws_conn_id)
        self.s3_conn = None
        self.salt = "default_salt"  

    """# Initiatlise S3 connection
    def _init_s3(self):

        conn = self.s3_hook # Get Airflow S3 hook
        # get credentials from Airflow connection
        aws_access_key = None
        aws_secret_key = None
        region = None

        # 2. Extract credentials debug
        extra = conn.extra_dejson or {}
        aws_access_key = extra.get("aws_access_key_id", aws_access_key)
        aws_secret_key = extra.get("aws_secret_access_key", aws_secret_key)
        region = extra.get("region_name", "eu-west-3")  # default region if missing
        bucket_name = extra.get("bucket_name")

        logger.info(f"S3 bucket: {bucket_name}")
        logger.info(f"AWS region: {region}")
        logger.info(f"AWS access key: {aws_access_key}")

        # 3. Init S3 client via boto3 (via hook)
        self.s3_conn = self.s3_hook.get_conn()
        if aws_access_key:
            logger.info(f"Using AWS Access Key: {aws_access_key}")
        else:
            logger.info("No AWS Access Key found.")

        logger.info("[OK] S3 connection established")
"""

    def anonymize_buyer (self, input_string: str) -> str:
        """Anonymize buyer identifier using SHA-256 hashing."""
        to_hash = (self.salt + input_string).encode('utf-8')
        hash_value = hashlib.sha256(to_hash).hexdigest()
        return hash_value


    def extract_table(self, table_name: str, query: str = None) -> pd.DataFrame:
        """
        Extract a table from PostgreSQL.

        Args:
            table_name: Name of the table to extract
            query: Custom SQL query (optional, defaults to SELECT *)

        Returns:
            DataFrame with the table data
        """

        try:
            if query is None:
                query = f"SELECT * FROM {table_name}"

            logger.info(f"Extracting table: {table_name}")
            df = self.pg_hook.get_pandas_df(query)
            logger.info(f"[OK] Extracted {len(df):,} rows from {table_name}")

            return df

        except Exception as e:
            logger.error(f"[FAIL] Failed to extract {table_name}: {e}")
            raise

        
    def upload_df_to_s3(self, df: pd.DataFrame, s3_key: str):
        # Prepare CSV in memory
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        # Get bucket from Airflow S3 connection
        conn = BaseHook.get_connection(self.s3_hook.aws_conn_id)
        bucket = conn.extra_dejson.get('bucket_name', 'a-ns-bucket')
        logger.info(f"Uploading to S3 bucket: {bucket}")

        self.s3_hook.load_string(
            string_data=csv_buffer.getvalue(),
            bucket_name=bucket,
            key=s3_key,
            replace=True
        )
        return f"s3://{bucket}/{s3_key}"

    def extract_and_upload_table(self, table_name: str, query: str = None,
                                 prefix: str = "raw/") -> str:
        """
        Extract a table and upload it to S3.

        Args:
            table_name: Name of the table
            query: Custom SQL query (optional)
            prefix: S3 prefix/folder

        Returns:
            S3 URI
        """
        # Extract
        df = self.extract_table(table_name, query)

        # Anonymize buyer identifiers if table contains 'buyer_id'
        logger.info(f"Starting anonymize data for table {table_name}...")
        if "buyer_id" in df.columns:
            df["buyer_id"] = df["buyer_id"].astype(str).apply(self.anonymize_buyer)


        # Generate S3 key with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        #s3_key = f"{prefix}{table_name}/{table_name}_{timestamp}.csv"
        s3_key = f"{prefix}{table_name}/{table_name}.csv"

        # Upload
        return self.upload_df_to_s3(df, s3_key)

    def extract_all_tables(self) -> dict:
        """
        Extract all required tables to S3.

        Returns:
            Dictionary mapping table names to S3 URIs
        """

        logger.info("STARTING EXTRACTION: PostgreSQL → S3 Data Lake")


        results = {}

        # Define tables and queries
        tables = {
            'product': None, 
            'category': None, 
            'buyer' : None,    
            'review': None,   
            'product_reviews': None,  
            'review_images': None,    
            'orders': None,   
            'carrier': None,  
        }

        # Extract each table
        for table_name, query in tables.items():
            try:
                s3_uri = self.extract_and_upload_table(table_name, query)
                results[table_name] = s3_uri
            except Exception as e:
                logger.error(f"Failed to process {table_name}: {e}")
                results[table_name] = None


        logger.info("EXTRACTION COMPLETED")


        # Summary
        successful = sum(1 for v in results.values() if v is not None)
        logger.info(f"Successfully extracted {successful}/{len(tables)} tables")

        for table_name, s3_uri in results.items():
            if s3_uri:
                logger.info(f"  [OK] {table_name}: {s3_uri}")
            else:
                logger.error(f"  [FAIL] {table_name}: Failed")

        return results

# DAG Airflow

def airflow_run(**context):
    extractor = PostgresToS3Extractor(
        #postgres_conn_id="postgres_source",
        #aws_conn_id="aws_default",
        postgres_conn_id="pg_amazon",
        aws_conn_id="aws_s3_default",
    )
    extracted_results = extractor.extract_all_tables()
    return extracted_results


def check_extraction_results(**context):
    """Check extraction results and send alert if tables failed"""
    ti = context['ti']
    dag_id = context['dag'].dag_id
    task_id = context['task'].task_id
    execution_date = context['execution_date'].isoformat()

    # Get extraction results from previous task
    extracted_results = ti.xcom_pull(task_ids='extract_to_s3')

    if not extracted_results:
        logger.error("No extraction results found")
        return

    # Check for failed tables
    failed_tables = {table: uri for table, uri in extracted_results.items() if uri is None}

    if failed_tables:
        logger.warning(f"Found {len(failed_tables)} failed table(s): {list(failed_tables.keys())}")

        # Send alert email
        alerter = EmailAlerter(
            to_emails=os.getenv("ALERT_EMAIL", "admin@example.com").split(",")
        )

        alerter.alert_no_data_from_s3(
            dag_id=dag_id,
            task_id=task_id,
            execution_date=execution_date,
            tables=extracted_results
        )

        logger.info("Alert email sent for failed extraction")
    else:
        logger.info("All tables extracted successfully, no alert needed")


with DAG(
    "extract_postgres_to_s3",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@daily",
    catchup=False
) as dag:

    extract_task = PythonOperator(
        task_id="extract_to_s3",
        python_callable=airflow_run,
        provide_context=True
    )

    # Check extraction results and send alert if needed
    check_results_task = PythonOperator(
        task_id="check_extraction_results",
        python_callable=check_extraction_results,
        provide_context=True
    )

    # Task 3 -> Trigger DAG "transform_load_data"
    trigger_transform = TriggerDagRunOperator(
        task_id="fetch_s3_paths",
        trigger_dag_id="transform_load_data",
        wait_for_completion=False,
    )

    extract_task >> check_results_task >> trigger_transform

