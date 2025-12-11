"""
Process and Store Reviews - Simplified for Testing
===================================================
Lightweight version of ReviewProcessor for unit tests.
This version does not depend on Airflow.

For production usage, see: scripts/dags/utils/review_processor.py
"""

import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReviewProcessor:
    """
    Simplified ReviewProcessor for unit testing.
    Contains only the data cleaning and validation logic.
    """

    def __init__(self):
        """Initialize processor."""
        self.pipeline_version = "1.0.0"
        self.run_id = datetime.now().strftime('%Y%m%d_%H%M%S')

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

        # 4. Check for empty buyer_id
        if 'buyer_id' in df_clean.columns:
            empty_buyer = df_clean['buyer_id'].isnull()
            empty_buyer_records = df_clean[empty_buyer]

            for _, rec in empty_buyer_records.iterrows():
                rejected_records.append({
                    'review_id': rec.get('review_id', 'UNKNOWN'),
                    'rejection_reason': 'missing_buyer_id',
                    'rejected_at': datetime.now(),
                    'original_data': rec.to_dict(),
                    'error_details': 'Buyer ID is null'
                })

            df_clean = df_clean[~empty_buyer]
            logger.info(f"  [OK] Removed {len(empty_buyer_records)} records with missing buyer_id")

        logger.info(f"  [OK] Final clean dataset: {len(df_clean):,} rows")
        logger.info(f"  [OK] Total rejected: {len(rejected_records)} records")

        df_rejected = pd.DataFrame(rejected_records) if rejected_records else pd.DataFrame()

        # Convert datetime fields to strings for compatibility
        if 'rejected_at' in df_rejected.columns:
            df_rejected['rejected_at'] = df_rejected['rejected_at'].astype(str)

        return df_clean, df_rejected
