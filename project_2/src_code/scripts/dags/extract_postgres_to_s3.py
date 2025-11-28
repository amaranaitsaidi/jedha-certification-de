"""
Extract Raw Data from PostgreSQL to S3
========================================
Script to extract tables from PostgreSQL and store them in S3 Data Lake.
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import logging
import sys
import os
import hashlib
from dotenv import load_dotenv

# Import connection libraries
from setup_conn_postgresql import PostgresConnection
from setup_conn_s3 import S3Connection

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostgresToS3Extractor:
    """Extract tables from PostgreSQL to S3"""

    def __init__(self, pg_connection: PostgresConnection, s3_connection: S3Connection):
            self.pg = pg_connection
            self.s3 = s3_connection
            self.salt = os.getenv("ANONYMIZATION_SALT", "default_salt")
            
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
        conn = self.pg.connect()

        try:
            if query is None:
                query = f"SELECT * FROM {table_name}"

            logger.info(f"Extracting table: {table_name}")
            df = pd.read_sql_query(query, conn)
            logger.info(f"[OK] Extracted {len(df):,} rows from {table_name}")

            return df

        except Exception as e:
            logger.error(f"[FAIL] Failed to extract {table_name}: {e}")
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
        s3_uri = self.s3.upload_file(df, s3_key)

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
            'buyer' : None,    # Extract all buyers
            'review': None,   # Extract all reviews
            'product_reviews': None,  # Extract all product-review mappings
            'review_images': None,    # Extract all review images
            'orders': None,   # Extract all orders
            'carrier': None,  # this is for test
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
        self.pg.close()
        logger.info("[OK] PostgreSQL connection closed")


def main():
    """Main execution."""
    try:
        # PostgreSQL
        pg = PostgresConnection(
            host=os.getenv('POSTGRES_HOST'),
            dbname=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD'),
            port=int(os.getenv('POSTGRES_PORT', 5432))
        )
        s3 = S3Connection(
            aws_access_key=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            bucket_name=os.getenv('AWS_S3_BUCKET'),
            aws_region=os.getenv('AWS_REGION', 'eu-west-1')
        )

        extractor = PostgresToS3Extractor(pg, s3)
        results = extractor.extract_all_tables()
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
