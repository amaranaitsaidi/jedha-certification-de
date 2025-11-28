"""
Snowflake Data Warehouse Setup
================================
Creates database, schema, and tables for Amazon Review Analysis.
"""

import snowflake.connector
import os
from dotenv import load_dotenv

load_dotenv()


def setup_snowflake():
    """Initialize Snowflake data warehouse."""

    print("Connecting to Snowflake...")

    conn = snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
        role=os.getenv('SNOWFLAKE_ROLE', 'SYSADMIN')
    )

    cursor = conn.cursor()

    # ========================================
    # 1. Database and Schema
    # ========================================
    print("\n[STEP 1/4] Creating Database and Schema")

    database = os.getenv('SNOWFLAKE_DATABASE', 'AMAZON_REVIEWS')
    schema = os.getenv('SNOWFLAKE_SCHEMA', 'ANALYTICS')

    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
    cursor.execute(f"USE DATABASE {database}")
    cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
    cursor.execute(f"USE SCHEMA {schema}")

    print(f"  [OK] Database: {database}")
    print(f"  [OK] Schema: {schema}")

    # ========================================
    # 2. Warehouse
    # ========================================
    print("\n[STEP 2/4] Creating Warehouse")

    warehouse = os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH')

    cursor.execute(f"""
        CREATE WAREHOUSE IF NOT EXISTS {warehouse}
        WAREHOUSE_SIZE = 'XSMALL'
        AUTO_SUSPEND = 300
        AUTO_RESUME = TRUE
        INITIALLY_SUSPENDED = TRUE
    """)
    cursor.execute(f"USE WAREHOUSE {warehouse}")

    print(f"  [OK] Warehouse: {warehouse}")

    # ========================================
    # 3. Main Table: reviews
    # ========================================
    print("\n[STEP 3/4] Creating Table: reviews")

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
            ingestion_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
            pipeline_version VARCHAR(20)
        )
    """)

    print("  [OK] Table: reviews")
    print("    - Columns: review_id, buyer_id, product_id, product_name, category")
    print("               title, description, rating, has_image, ingestion_timestamp")

    # ========================================
    # 4. S3 Stage
    # ========================================
    print("\n[STEP 4/4] Creating S3 Stage")

    aws_key_id = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    s3_bucket = os.getenv('AWS_S3_BUCKET', 'your-bucket-name')

    # Clean S3 bucket URL
    if s3_bucket.startswith('s3://'):
        s3_bucket = s3_bucket[5:]
    if s3_bucket.endswith('/'):
        s3_bucket = s3_bucket[:-1]

    stage_sql = f"""
        CREATE OR REPLACE STAGE s3_review_stage
        URL = 's3://{s3_bucket}/processed/'
        CREDENTIALS = (
            AWS_KEY_ID = '{aws_key_id}'
            AWS_SECRET_KEY = '{aws_secret_key}'
        )
        FILE_FORMAT = (
            TYPE = 'CSV'
            FIELD_OPTIONALLY_ENCLOSED_BY = '"'
            SKIP_HEADER = 1
            FIELD_DELIMITER = ','
            NULL_IF = ('NULL', 'null', '')
        )
    """
    cursor.execute(stage_sql)

    print(f"  [OK] S3 Stage: s3_review_stage")
    print(f"    - Bucket: s3://{s3_bucket}/processed/")
    print(f"    - Format: CSV with header")

    # ========================================
    # 5. Create Useful Views
    # ========================================
    print("\n[BONUS] Creating Views")

    # View 1: Reviews by product
    cursor.execute("""
        CREATE OR REPLACE VIEW vw_reviews_by_product AS
        SELECT
            p_id,
            product_name,
            COUNT(*) as total_reviews,
            AVG(rating) as avg_rating,
            SUM(CASE WHEN has_image THEN 1 ELSE 0 END) as reviews_with_images,
            MIN(ingestion_timestamp) as first_review,
            MAX(ingestion_timestamp) as last_review
        FROM reviews
        GROUP BY p_id, product_name
        ORDER BY total_reviews DESC
    """)
    print("  [OK] View: vw_reviews_by_product")

    # View 2: Reviews by category
    cursor.execute("""
        CREATE OR REPLACE VIEW vw_reviews_by_category AS
        SELECT
            category,
            COUNT(*) as total_reviews,
            AVG(rating) as avg_rating,
            COUNT(DISTINCT p_id) as unique_products
        FROM reviews
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY total_reviews DESC
    """)
    print("  [OK] View: vw_reviews_by_category")

    # View 3: Data quality metrics
    cursor.execute("""
        CREATE OR REPLACE VIEW vw_data_quality AS
        SELECT
            COUNT(*) as total_reviews,
            COUNT(DISTINCT review_id) as unique_reviews,
            COUNT(DISTINCT buyer_id) as unique_buyers,
            COUNT(DISTINCT p_id) as unique_products,
            AVG(rating) as avg_rating,
            SUM(CASE WHEN has_image THEN 1 ELSE 0 END) / COUNT(*) * 100 as pct_with_images,
            COUNT(CASE WHEN description IS NULL OR description = '' THEN 1 END) as empty_descriptions
        FROM reviews
    """)
    print("  [OK] View: vw_data_quality")

    # ========================================
    # Summary
    # ========================================
    cursor.close()
    conn.close()

    print('\n' + '=' * 60)
    print('Snowflake Setup Complete!')
    print('=' * 60)
    print(f"Database: {database}")
    print(f"Schema: {schema}")
    print(f"Warehouse: {warehouse}")
    print("\nTables:")
    print("  - reviews: Main table for clean review data")
    print("\nViews:")
    print("  - vw_reviews_by_product: Aggregated by product")
    print("  - vw_reviews_by_category: Aggregated by category")
    print("  - vw_data_quality: Data quality metrics")
    print("\nStage:")
    print(f"  - s3_review_stage: s3://{s3_bucket}/processed/")


if __name__ == '__main__':
    setup_snowflake()
