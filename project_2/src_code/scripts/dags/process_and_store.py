"""
Process and Store Reviews
==========================
Unified script that:
1. Loads raw data from S3
2. Joins tables using SQL
3. Cleans data and detects rejections
4. Stores clean data in Snowflake
5. Stores rejected data in MongoDB
"""

import pandas as pd
import boto3
from io import StringIO
from pandasql import sqldf
from datetime import datetime
import os
import sys
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
import snowflake.connector

# Load environment variables
load_dotenv()


class MongoDBLogHandler(logging.Handler):
    """Custom log handler to store logs in MongoDB."""

    def __init__(self, connection_string: str, database: str = 'amazon_reviews', collection: str = 'pipeline_logs'):
        """
        Initialize MongoDB log handler.

        Args:
            connection_string: MongoDB connection string
            database: Database name
            collection: Collection name for logs
        """
        super().__init__()
        self.connection_string = connection_string
        self.database_name = database
        self.collection_name = collection
        self.client = None
        self.collection = None
        self._connect()

    def _connect(self):
        """Establish MongoDB connection."""
        try:
            self.client = MongoClient(self.connection_string)
            db = self.client[self.database_name]
            self.collection = db[self.collection_name]
        except Exception as e:
            print(f"Failed to connect to MongoDB for logging: {e}")

    def emit(self, record):
        """
        Emit a log record to MongoDB.

        Args:
            record: Log record to emit
        """
        try:
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line_number': record.lineno,
                'process_id': record.process,
                'thread_id': record.thread
            }

            # Add exception info if present
            if record.exc_info:
                log_entry['exception'] = self.format(record)

            if self.collection is not None:
                self.collection.insert_one(log_entry)
        except Exception:
            self.handleError(record)

    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
        super().close()


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add MongoDB handler if MongoDB connection is configured
mongo_connection = os.getenv('MONGODB_CONNECTION_STRING')
if mongo_connection:
    try:
        mongo_handler = MongoDBLogHandler(mongo_connection)
        mongo_handler.setLevel(logging.INFO)
        logger.addHandler(mongo_handler)
        logger.info("MongoDB log handler initialized")
    except Exception as e:
        logger.warning(f"Could not initialize MongoDB log handler: {e}")


class ReviewProcessor:
    """Processes reviews from S3 to Snowflake and MongoDB."""

    def __init__(self):
        """Initialize connections."""
        self.s3_client = None
        self.mongo_client = None
        self.snowflake_conn = None
        self.pipeline_version = "1.0.0"
        self.run_id = datetime.now().strftime('%Y%m%d_%H%M%S')

    # ========================================
    # S3: Load Data
    # ========================================

    def _init_s3(self):
        """Initialize S3 client."""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'eu-west-1')
        )
        logger.info("[OK] S3 client initialized")

    def load_table_from_s3(self, s3_uri: str) -> pd.DataFrame:
        """
        Load a table from S3.

        Args:
            s3_uri: S3 URI (e.g., s3://bucket/raw/product/product.csv)

        Returns:
            DataFrame
        """
        if not self.s3_client:
            self._init_s3()

        # Parse S3 URI
        parts = s3_uri.replace('s3://', '').split('/', 1)
        bucket = parts[0]
        key = parts[1]

        # Read CSV from S3
        obj = self.s3_client.get_object(Bucket=bucket, Key=key)
        df = pd.read_csv(StringIO(obj['Body'].read().decode('utf-8')))

        return df

    def load_all_tables(self, s3_paths: dict) -> dict:
        """
        Load all required tables from S3.

        Args:
            s3_paths: Dict mapping table names to S3 URIs

        Returns:
            Dict of DataFrames
        """
        logger.info("Loading tables from S3...")
        tables = {}

        for table_name, s3_uri in s3_paths.items():
            try:
                df = self.load_table_from_s3(s3_uri)
                tables[table_name] = df
                logger.info(f"  [OK] {table_name}: {len(df):,} rows")
            except Exception as e:
                logger.error(f"  [FAIL] {table_name}: {e}")
                raise

        return tables

    # ========================================
    # JOIN & CLEAN
    # ========================================

    def join_tables(self, tables: dict, product_id: str = None) -> pd.DataFrame:
        """
        Join tables using SQL.

        Args:
            tables: Dict of DataFrames
            product_id: Optional product filter

        Returns:
            Joined DataFrame
        """
        logger.info("Joining tables using SQL...")

        # Extract tables
        product = tables['product']
        category = tables.get('category', pd.DataFrame())
        review = tables['review']
        product_reviews = tables['product_reviews']
        review_images = tables.get('review_images', pd.DataFrame())
        orders = tables.get('orders', pd.DataFrame())

        # Build WHERE clause
        where_clause = f"WHERE pr.p_id = '{product_id}'" if product_id else ""

        # SQL query
        query = f"""
        select
            distinct o.buyer_id,
            r.review_id,
            r.title,
            r.r_desc AS description,
            r.rating,
            LENGTH(r.r_desc) AS text_length,
            CASE WHEN ri.review_id IS NOT NULL THEN 1 ELSE 0 END AS has_image,
            CASE WHEN o.order_id IS NOT NULL THEN 1 ELSE 0 END AS has_orders,
            p.p_id,
            p.p_name AS product_name,
            c.name AS category
        FROM review r
        LEFT JOIN product_reviews pr ON r.review_id = pr.review_id
        LEFT JOIN product p ON pr.p_id = p.p_id
        LEFT JOIN category c ON p.category_id = c.category_id
        LEFT JOIN review_images ri ON r.review_id = ri.review_id
        LEFT JOIN orders  o ON r.buyer_id = o.buyer_id
        {where_clause}
        ORDER BY r.review_id
        """

        df = sqldf(query, locals())
        logger.info(f"  [OK] Joined {len(df):,} rows")

        return df

    def clean_and_validate(self, df: pd.DataFrame) -> tuple:
        """
        Clean data and separate valid/rejected records.

        Args:
            df: Joined DataFrame

        Returns:
            Tuple of (df_clean, df_rejected)
        """
        logger.info("Cleaning and validating data...")

        df_clean = df.copy()
        rejected_records = []

        # 1. Remove duplicates based on review_id
        initial_count = len(df_clean)
        duplicates = df_clean[df_clean.duplicated(subset=['review_id'], keep='first')]

        for _, dup in duplicates.iterrows():
            rejected_records.append({
                'review_id': dup['review_id'],
                'rejection_reason': 'duplicate_review_id',
                'rejected_at': datetime.now(),
                'original_data': dup.to_dict(),
                'error_details': 'Duplicate review_id found'
            })

        df_clean = df_clean.drop_duplicates(subset=['review_id'], keep='first')
        logger.info(f"  [OK] Removed {initial_count - len(df_clean)} duplicates")

        # 2. Check for missing required fields
        required_fields = ['review_id', 'rating']
        missing_mask = df_clean[required_fields].isnull().any(axis=1)
        missing_records = df_clean[missing_mask]

        for _, rec in missing_records.iterrows():
            rejected_records.append({
                'review_id': rec.get('review_id', 'UNKNOWN'),
                'rejection_reason': 'missing_required_fields',
                'rejected_at': datetime.now(),
                'original_data': rec.to_dict(),
                'error_details': f"Missing required fields: {', '.join([f for f in required_fields if pd.isna(rec.get(f))])}"
            })

        df_clean = df_clean[~missing_mask]
        logger.info(f"  [OK] Removed {len(missing_records)} records with missing required fields")

        # 3. Validate rating (1-5)
        invalid_rating = df_clean[(df_clean['rating'] < 1) | (df_clean['rating'] > 5)]

        for _, rec in invalid_rating.iterrows():
            rejected_records.append({
                'review_id': rec['review_id'],
                'rejection_reason': 'invalid_rating',
                'rejected_at': datetime.now(),
                'original_data': rec.to_dict(),
                'error_details': f"Invalid rating: {rec['rating']}"
            })

        df_clean = df_clean[(df_clean['rating'] >= 1) & (df_clean['rating'] <= 5)]
        logger.info(f"  [OK] Removed {len(invalid_rating)} records with invalid rating")

        empty_description = df_clean['description'].isnull() | (df_clean['description'].str.strip().str.len() == 0)
        empty_description_records = df_clean[empty_description]

        for _, rec in empty_description_records.iterrows():
            rejected_records.append({
                'review_id': rec.get('review_id', 'UNKNOWN'),
                'rejection_reason': 'empty_description',
                'rejected_at': datetime.now(),
                'original_data': rec.to_dict(),
                'error_details': 'Description is empty or null'
            })

        df_clean = df_clean[~empty_description]
        logger.info(f"  [OK] Removed {len(empty_description_records)} records with empty/null description")

        # 4. Fill missing values
        df_clean['title'] = df_clean['title'].fillna('')
        df_clean['description'] = df_clean['description'].fillna('')
        df_clean['category'] = df_clean['category'].fillna('Unknown')
        df_clean['text_length'] = df_clean['text_length'].fillna(0).astype(int)
        df_clean['has_image'] = df_clean['has_image'].fillna(0).astype(bool)
        df_clean['has_orders'] = df_clean['has_orders'].fillna(0).astype(bool)

        logger.info(f"  [OK] Final clean dataset: {len(df_clean):,} rows")
        logger.info(f"  [OK] Total rejected: {len(rejected_records)} records")

        df_rejected = pd.DataFrame(rejected_records) if rejected_records else pd.DataFrame()

        return df_clean, df_rejected

    # ========================================
    # STORAGE: Snowflake
    # ========================================

    def _init_snowflake(self):
        """Initialize Snowflake connection."""
        self.snowflake_conn = snowflake.connector.connect(
            user=os.getenv('SNOWFLAKE_USER'),
            password=os.getenv('SNOWFLAKE_PASSWORD'),
            account=os.getenv('SNOWFLAKE_ACCOUNT'),
            warehouse=os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
            database=os.getenv('SNOWFLAKE_DATABASE', 'AMAZON_REVIEWS'),
            schema=os.getenv('SNOWFLAKE_SCHEMA', 'ANALYTICS'),
            role=os.getenv('SNOWFLAKE_ROLE', 'SYSADMIN')
        )
        logger.info("[OK] Snowflake connection established")

    def save_to_snowflake(self, df: pd.DataFrame) -> int:
        """
        Save clean data to Snowflake.

        Args:
            df: Clean DataFrame

        Returns:
            Number of rows inserted
        """
        if not self.snowflake_conn:
            self._init_snowflake()

        logger.info("Saving to Snowflake...")

        cursor = self.snowflake_conn.cursor()

        # TRUNCATE table to avoid duplicates (anonymization creates different hashes each run)
        logger.info("Truncating existing data in Snowflake reviews table...")
        cursor.execute("TRUNCATE TABLE reviews")
        logger.info("  [OK] Table truncated")

        # Prepare data
        df_to_insert = df.copy()
        df_to_insert['ingestion_timestamp'] = datetime.now()
        df_to_insert['pipeline_version'] = self.pipeline_version

        # Convert boolean to int for Snowflake
        df_to_insert['has_image'] = df_to_insert['has_image'].astype(int)
        df_to_insert['has_orders'] = df_to_insert['has_orders'].astype(int)

        # Insert rows
        insert_query = """
        INSERT INTO reviews (
            review_id, buyer_id, p_id, product_name, category,
            title, description, rating, text_length, has_image, has_orders,
            ingestion_timestamp, pipeline_version
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Convert to list of dictionaries for easier handling
        rows = []
        for record in df_to_insert.to_dict('records'):
            # Handle NaN values properly
            buyer_id = record['buyer_id'] if pd.notna(record['buyer_id']) else None
            p_id = record['p_id'] if pd.notna(record['p_id']) else None
            product_name = record['product_name'] if pd.notna(record['product_name']) else None

            rows.append((
                record['review_id'],
                buyer_id,
                p_id,
                product_name,
                record['category'],
                record['title'],
                record['description'],
                int(record['rating']),
                int(record['text_length']),
                bool(record['has_image']),
                bool(record['has_orders']),
                record['ingestion_timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                record['pipeline_version']
            ))

        cursor.executemany(insert_query, rows)
        cursor.close()

        logger.info(f"  [OK] Inserted {len(rows):,} rows to Snowflake")

        return len(rows)

    # ========================================
    # STORAGE: MongoDB
    # ========================================

    def _init_mongodb(self):
        """Initialize MongoDB connection."""
        connection_string = os.getenv(
            'MONGODB_CONNECTION_STRING',
            'mongodb://admin:changeme@localhost:27017/'
        )
        self.mongo_client = MongoClient(connection_string)
        logger.info("[OK] MongoDB connection established")

    def save_rejected_to_mongodb(self, df_rejected: pd.DataFrame) -> int:
        """
        Save rejected records to MongoDB.

        Args:
            df_rejected: DataFrame with rejected records

        Returns:
            Number of documents inserted
        """
        if df_rejected.empty:
            logger.info("No rejected records to save")
            return 0

        if not self.mongo_client:
            self._init_mongodb()

        logger.info("Saving rejected records to MongoDB...")

        db = self.mongo_client['amazon_reviews']
        collection = db['rejected_reviews']

        # Convert to dict and insert
        records = df_rejected.to_dict('records')
        result = collection.insert_many(records)

        logger.info(f"  [OK] Inserted {len(result.inserted_ids)} rejected records to MongoDB")

        return len(result.inserted_ids)

    def save_metadata_to_mongodb(self, stats: dict):
        """Save pipeline execution metadata to MongoDB."""
        if not self.mongo_client:
            self._init_mongodb()

        db = self.mongo_client['amazon_reviews']
        collection = db['pipeline_metadata']

        metadata = {
            'pipeline_run_id': self.run_id,
            'execution_date': datetime.now(),
            'pipeline_version': self.pipeline_version,
            'stats': stats
        }

        collection.insert_one(metadata)
        logger.info("  [OK] Saved pipeline metadata to MongoDB")

    # ========================================
    # MAIN PROCESS
    # ========================================

    def process(self, s3_paths: dict, product_id: str = None) -> dict:
        """
        Execute full processing pipeline.

        Args:
            s3_paths: Dict mapping table names to S3 URIs
            product_id: Optional product filter

        Returns:
            Dict with statistics
        """
        try:
            logger.info("=" * 80)
            logger.info("STARTING REVIEW PROCESSING PIPELINE")
            logger.info("=" * 80)

            # Step 1: Load from S3
            logger.info("\n[STEP 1/4] LOAD DATA FROM S3")
            tables = self.load_all_tables(s3_paths)

            # Step 2: Join tables
            logger.info("\n[STEP 2/4] JOIN TABLES")
            df_joined = self.join_tables(tables, product_id)

            # Step 3: Clean and validate
            logger.info("\n[STEP 3/4] CLEAN & VALIDATE")
            df_clean, df_rejected = self.clean_and_validate(df_joined)

            # Step 4: Store
            logger.info("\n[STEP 4/4] STORE DATA")

            # Store clean data in Snowflake
            snowflake_count = self.save_to_snowflake(df_clean)

            # Store rejected data in MongoDB
            rejected_count = self.save_rejected_to_mongodb(df_rejected)

            # Store metadata
            stats = {
                'total_records_processed': len(df_joined),
                'clean_records': len(df_clean),
                'rejected_records': len(df_rejected),
                'snowflake_inserts': snowflake_count,
                'mongodb_inserts': rejected_count
            }
            self.save_metadata_to_mongodb(stats)

            # Summary
            logger.info("\n" + "=" * 80)
            logger.info("PIPELINE COMPLETED SUCCESSFULLY")
            logger.info("=" * 80)
            logger.info(f"Total processed: {len(df_joined):,}")
            logger.info(f"Clean records (Snowflake): {len(df_clean):,}")
            logger.info(f"Rejected records (MongoDB): {len(df_rejected):,}")
            logger.info("=" * 80)

            return stats

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            raise

    def close(self):
        """Close all connections."""
        # Close MongoDB log handler first (before closing connections)
        mongo_handler = None
        for handler in logger.handlers:
            if isinstance(handler, MongoDBLogHandler):
                mongo_handler = handler
                break

        if self.snowflake_conn:
            self.snowflake_conn.close()
            logger.info("[OK] Snowflake connection closed")
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("[OK] MongoDB connection closed")

        # Close the log handler after logging completion messages
        if mongo_handler:
            mongo_handler.close()
            # Don't log after closing the handler


def main():
    """Main execution."""
    try:
        # S3 paths configuration
        bucket = os.getenv('AWS_S3_BUCKET')
        s3_paths = {
            'product': f"s3://{bucket}/raw/product/product.csv",
            'category': f"s3://{bucket}/raw/category/category.csv",
            'review': f"s3://{bucket}/raw/review/review.csv",
            'product_reviews': f"s3://{bucket}/raw/product_reviews/product_reviews.csv",
            'review_images': f"s3://{bucket}/raw/review_images/review_images.csv",
            'orders': f"s3://{bucket}/raw/orders/orders.csv"
        }

        # Optional: filter by product_id
        product_id = os.getenv('PRODUCT_ID', None)

        # Initialize processor
        processor = ReviewProcessor()

        # Process
        stats = processor.process(s3_paths, product_id)

        # Close connections
        processor.close()

        sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
