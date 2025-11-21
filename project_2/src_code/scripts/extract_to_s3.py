"""
Extract Raw Data from PostgreSQL to S3
========================================
Script pour extraire les tables brutes de PostgreSQL
et les stocker dans le Data Lake S3.
"""

import psycopg2
import pandas as pd
import boto3
from datetime import datetime
from pathlib import Path
import logging
import sys
import os
from dotenv import load_dotenv
import hashlib


# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostgresToS3Extractor:
    """Extrait les tables brutes de PostgreSQL vers S3."""

    def __init__(self, postgres_conn_string: str, s3_bucket: str,
                 aws_access_key: str, aws_secret_key: str, aws_region: str = 'eu-west-1'):
        """
        Initialize the extractor.

        Args:
            postgres_conn_string: PostgreSQL connection string
            s3_bucket: S3 bucket name
            aws_access_key: AWS access key ID
            aws_secret_key: AWS secret access key
            aws_region: AWS region
        """
        self.postgres_conn_string = postgres_conn_string
        self.s3_bucket = s3_bucket
        self.aws_region = aws_region
        self.salt = os.getenv("ANONYMIZATION_SALT", "default_salt")
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )

        self.conn = None

    def connect_postgresql(self):
        """Establish connection to PostgreSQL."""
        try:
            self.conn = psycopg2.connect(self.postgres_conn_string)
            logger.info("[OK] Connected to PostgreSQL")
        except Exception as e:
            logger.error(f"[FAIL] Failed to connect to PostgreSQL: {e}")
            raise
    
    def anonymize_buyer(self, input_string: str) -> str:
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
        if not self.conn:
            self.connect_postgresql()

        try:
            if query is None:
                query = f"SELECT * FROM {table_name}"

            logger.info(f"Extracting table: {table_name}")
            df = pd.read_sql_query(query, self.conn)
            logger.info(f"[OK] Extracted {len(df):,} rows from {table_name}")

            return df

        except Exception as e:
            logger.error(f"[FAIL] Failed to extract {table_name}: {e}")
            raise

    def upload_to_s3(self, df: pd.DataFrame, s3_key: str) -> str:
        """
        Upload DataFrame to S3 as CSV.

        Args:
            df: DataFrame to upload
            s3_key: S3 object key (path)

        Returns:
            S3 URI
        """
        try:
            # Convert to CSV
            csv_buffer = df.to_csv(index=False)

            # Upload to S3
            logger.info(f"Uploading to s3://{self.s3_bucket}/{s3_key}")
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=csv_buffer.encode('utf-8'),
                ContentType='text/csv'
            )

            s3_uri = f"s3://{self.s3_bucket}/{s3_key}"
            logger.info(f"[OK] Uploaded {len(df):,} rows to {s3_uri}")

            return s3_uri

        except Exception as e:
            logger.error(f"[FAIL] Failed to upload to S3: {e}")
            raise

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
    def extract_and_upload_table(self, table_name: str, query: str = None, prefix: str = "raw/") -> str:
        # Extract
        df = self.extract_table(table_name, query)

        # Anonymize buyer identifiers if table contains 'buyer_id'
        logger.info(f"Starting anonymize data for table {table_name}...")
        if "buyer_id" in df.columns:
            df["buyer_id"] = df["buyer_id"].astype(str).apply(self.anonymize_buyer)

        # Generate S3 key with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"{prefix}{table_name}/{table_name}_{timestamp}.csv"

        # Upload
        s3_uri = self.upload_to_s3(df, s3_key)

        return s3_uri

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
            'product': None,  # Extract all products
            'category': None,  # Extract all categories
            'review': None,   # Extract all reviews
            'product_reviews': None,  # Extract all product-review mappings
            'review_images': None,    # Extract all review images
            'orders': None,   # Extract all orders
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

    def close(self):
        """Close PostgreSQL connection."""
        if self.conn:
            self.conn.close()
            logger.info("[OK] PostgreSQL connection closed")


def main():
    """Main execution."""
    try:
        # Get configuration from environment variables
        postgres_conn = os.getenv('POSTGRES_CONNECTION_STRING')
        s3_bucket = os.getenv('AWS_S3_BUCKET')
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION', 'eu-west-1')

        # Validate configuration
        if not all([postgres_conn, s3_bucket, aws_access_key, aws_secret_key]):
            logger.error("Missing required environment variables:")
            logger.error("  - POSTGRES_CONNECTION_STRING")
            logger.error("  - AWS_S3_BUCKET")
            logger.error("  - AWS_ACCESS_KEY_ID")
            logger.error("  - AWS_SECRET_ACCESS_KEY")
            sys.exit(1)

        # Initialize extractor
        extractor = PostgresToS3Extractor(
            postgres_conn_string=postgres_conn,
            s3_bucket=s3_bucket,
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
            aws_region=aws_region
        )

        # Extract all tables
        results = extractor.extract_all_tables()

        # Close connection
        extractor.close()

        # Exit with appropriate code
        if all(results.values()):
            logger.info("[OK] All tables extracted successfully")
            sys.exit(0)
        else:
            logger.error("[FAIL] Some tables failed to extract")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
