import logging
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.hooks.base import BaseHook
import os
from utils.mongo_handler import MongoHandler
from utils.review_processor import ReviewProcessor
import pandas as pd

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================================================
# LOGGING → MongoDB
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("transform_load")

conn = BaseHook.get_connection("mongo")
mongo_uri = conn.get_uri()

mongo_handler = MongoHandler(
    uri=mongo_uri,
    db_name="airflow_logs",
    collection="transform_logs"
)

if not any(isinstance(h, MongoHandler) for h in logger.handlers):
    logger.addHandler(mongo_handler)



# ============================================================================
# DAG transform_load_data
# ============================================================================
with DAG(
    dag_id="transform_load_data",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["reviews", "etl"],
) as dag:

    # -------------------------------------------------------
    # 1. Récupérer les S3 paths du DAG précédent
    # -------------------------------------------------------
    def pull_s3_paths(**context):
        """Pull XCom results from extract DAG."""
        ti = context["ti"]

        s3_paths = ti.xcom_pull(
            dag_id="extract_postgres_to_s3",
            task_ids="extract_to_s3"
        )
        logger.info(f"DEBUG -> S3 paths pulled from XCom : {s3_paths}")

        if not s3_paths:
            # Get bucket from Airflow connection
            aws_conn = BaseHook.get_connection("aws_s3_default")
            bucket = aws_conn.extra_dejson.get("bucket_name", "a-ns-bucket")
            logger.info(f"Using S3 bucket from connection: {bucket}")

            s3_paths = {
            'product': f"s3://{bucket}/raw/product/product.csv",
            'category': f"s3://{bucket}/raw/category/category.csv",
            'review': f"s3://{bucket}/raw/review/review.csv",
            'product_reviews': f"s3://{bucket}/raw/product_reviews/product_reviews.csv",
            'review_images': f"s3://{bucket}/raw/review_images/review_images.csv",
            'orders': f"s3://{bucket}/raw/orders/orders.csv"
        }

        logger.info("Received S3 paths:")
        logger.info(s3_paths)

        return s3_paths


    fetch_paths = PythonOperator(
        task_id="fetch_s3_paths",
        python_callable=pull_s3_paths,
        provide_context=True
    )


    # -------------------------------------------------------
    # 2. Charger les données depuis S3
    # -------------------------------------------------------
    def load_from_s3(**context):
        s3_paths = context["ti"].xcom_pull(task_ids="fetch_s3_paths")
        processor = ReviewProcessor(aws_conn_id="aws_s3_default", snowflake_conn_id="snowflake_conn")
        tables = processor.load_all_tables(s3_paths)
        return tables


    load_tables = PythonOperator(
        task_id="load_tables_from_s3",
        python_callable=load_from_s3,
        provide_context=True
    )


    # -------------------------------------------------------
    # 3. Join
    # -------------------------------------------------------
    def join_step(**context):
        tables = context["ti"].xcom_pull(task_ids="load_tables_from_s3")
        processor = ReviewProcessor(aws_conn_id="aws_s3_default", snowflake_conn_id="snowflake_conn")
        merged = processor.join_tables(tables)
        return merged.to_dict()


    join_tables = PythonOperator(
        task_id="join_tables",
        python_callable=join_step,
        provide_context=True
    )


    # -------------------------------------------------------
    # 4. Clean & Validate
    # -------------------------------------------------------
    def clean_step(**context):
        merged_dict = context["ti"].xcom_pull(task_ids="join_tables")
        df_joined = pd.DataFrame(merged_dict)

        processor = ReviewProcessor(aws_conn_id="aws_s3_default", snowflake_conn_id="snowflake_conn")
        df_clean, df_rejected = processor.clean_and_validate(df_joined)

        return {
            "clean": df_clean.to_dict(),
            "rejected": df_rejected.to_dict()
        }


    clean_validate = PythonOperator(
        task_id="clean_and_validate",
        python_callable=clean_step,
        provide_context=True
    )


    # -------------------------------------------------------
    # 5. Load clean → Snowflake
    # -------------------------------------------------------
    def load_snowflake(**context):
        data = context["ti"].xcom_pull(task_ids="clean_and_validate")
        df_clean = pd.DataFrame(data["clean"])

        processor = ReviewProcessor(aws_conn_id="aws_s3_default", snowflake_conn_id="snowflake_conn")
        return processor.save_to_snowflake(df_clean)


    save_clean = PythonOperator(
        task_id="load_clean_to_snowflake",
        python_callable=load_snowflake,
        provide_context=True
    )


    # -------------------------------------------------------
    # 6. Load rejected → MongoDB
    # -------------------------------------------------------
    def load_rejected(**context):
        data = context["ti"].xcom_pull(task_ids="clean_and_validate")
        df_rejected = pd.DataFrame(data["rejected"])

        processor = ReviewProcessor(aws_conn_id="aws_s3_default", snowflake_conn_id="snowflake_conn")
        return processor.save_rejected_to_mongodb(df_rejected)


    save_rejected = PythonOperator(
        task_id="load_rejected_to_mongodb",
        python_callable=load_rejected,
        provide_context=True
    )


    # -------------------------------------------------------
    # 7. Close connections
    # -------------------------------------------------------
    def close_connections(**context):
        ti = context["ti"]

        stats = {
            "snowflake_inserts": ti.xcom_pull(task_ids="load_clean_to_snowflake"),
            "mongodb_inserts": ti.xcom_pull(task_ids="load_rejected_to_mongodb"),
        }

        processor = ReviewProcessor(aws_conn_id="aws_s3_default", snowflake_conn_id="snowflake_conn")
        processor.save_metadata_to_mongodb(stats)


    metadata = PythonOperator(
        task_id="close_connections",
        python_callable=close_connections,
        provide_context=True
    )


    # =============================
    #         DAG FLOW
    # =============================
    fetch_paths >> load_tables >> join_tables >> clean_validate
    clean_validate >> [save_clean, save_rejected] >> metadata



