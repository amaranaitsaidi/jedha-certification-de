"""
MongoDB Setup Script
====================
Creates collections, indexes, and validation rules for Amazon Review Analysis.
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def setup_mongodb(connection_string: str = None):
    """Initialize MongoDB database with collections, indexes, and validation."""

    if connection_string is None:
        connection_string = os.getenv(
            'MONGODB_CONNECTION_STRING',
            'mongodb://admin:changeme@localhost:27017/'
        )

    client = MongoClient(connection_string)
    db = client['amazon_reviews']

    print(f"Connected to MongoDB: {db.name}")

    # ========================================
    # Collection 1: reviews (données propres)
    # ========================================
    print('\nCreating collection: reviews')

    if 'reviews' in db.list_collection_names():
        db.reviews.drop()
        print("  - Dropped existing collection")

    db.create_collection('reviews', validator={
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['review_id', 'rating', '_ingestion_timestamp'],
            'properties': {
                'review_id': {'bsonType': 'string'},
                'buyer_id': {'bsonType': 'string'},
                'product_id': {'bsonType': 'string'},
                'product_name': {'bsonType': 'string'},
                'category': {'bsonType': 'string'},
                'title': {'bsonType': 'string'},
                'description': {'bsonType': 'string'},
                'rating': {'bsonType': 'int', 'minimum': 1, 'maximum': 5},
                'has_image': {'bsonType': 'bool'},
                '_ingestion_timestamp': {'bsonType': 'date'},
                '_pipeline_version': {'bsonType': 'string'}
            }
        }
    }, validationAction='error', validationLevel='strict')

    # Create indexes
    reviews_collection = db['reviews']
    reviews_collection.create_index([('review_id', ASCENDING)], unique=True, name='idx_review_id')
    reviews_collection.create_index([('product_id', ASCENDING)], name='idx_product_id')
    reviews_collection.create_index([('rating', ASCENDING)], name='idx_rating')
    reviews_collection.create_index([('_ingestion_timestamp', DESCENDING)], name='idx_ingestion_timestamp_desc')
    reviews_collection.create_index([('buyer_id', ASCENDING)], name='idx_buyer_id')
    reviews_collection.create_index([('category', ASCENDING)], name='idx_category')

    print(f"  [OK] Created {len(list(reviews_collection.list_indexes()))} indexes")

    # ========================================
    # Collection 2: rejected_reviews
    # ========================================
    print('\nCreating collection: rejected_reviews')

    if 'rejected_reviews' in db.list_collection_names():
        db.rejected_reviews.drop()
        print("  - Dropped existing collection")

    db.create_collection('rejected_reviews', validator={
        '$jsonSchema': {
            'bsonType': 'object',
            'required': ['review_id', 'rejection_reason', 'rejected_at'],
            'properties': {
                'review_id': {'bsonType': 'string'},
                'rejection_reason': {
                    'enum': [
                        'duplicate_review_id',
                        'missing_required_fields',
                        'invalid_rating',
                        'data_quality_issue',
                        'join_failure',
                        'other'
                    ]
                },
                'rejected_at': {'bsonType': 'date'},
                'original_data': {'bsonType': 'object'},
                'error_details': {'bsonType': 'string'}
            }
        }
    }, validationAction='warn', validationLevel='moderate')

    rejected_collection = db['rejected_reviews']
    rejected_collection.create_index([('review_id', ASCENDING)], name='idx_rejected_review_id')
    rejected_collection.create_index([('rejection_reason', ASCENDING)], name='idx_rejection_reason')
    rejected_collection.create_index([('rejected_at', DESCENDING)], name='idx_rejected_at_desc')

    print(f"  [OK] Created {len(list(rejected_collection.list_indexes()))} indexes")

    # ========================================
    # Collection 3: pipeline_metadata
    # ========================================
    print('\nCreating collection: pipeline_metadata')

    if 'pipeline_metadata' in db.list_collection_names():
        db.pipeline_metadata.drop()
        print("  - Dropped existing collection")

    db.create_collection('pipeline_metadata')
    metadata_collection = db['pipeline_metadata']
    metadata_collection.create_index([('execution_date', DESCENDING)], name='idx_execution_date_desc')
    metadata_collection.create_index([('pipeline_run_id', ASCENDING)], name='idx_pipeline_run_id')

    # Insert initialization document
    metadata_collection.insert_one({
        '_id': 'initialization',
        'event': 'database_initialized',
        'timestamp': datetime.now(),
        'schema_version': '1.0',
        'collections': ['reviews', 'rejected_reviews', 'pipeline_metadata']
    })

    print(f"  [OK] Created {len(list(metadata_collection.list_indexes()))} indexes")
    print(f"  [OK] Inserted initialization metadata")

    # ========================================
    # Summary
    # ========================================
    print('\n' + '=' * 60)
    print('MongoDB Setup Complete!')
    print('=' * 60)
    print(f"Database: {db.name}")
    print(f"Collections: {', '.join(db.list_collection_names())}")
    print('\nCollection Details:')
    print(f"  - reviews: Clean review data")
    print(f"  - rejected_reviews: Rejected records with reasons")
    print(f"  - pipeline_metadata: Pipeline execution metadata")

    client.close()


if __name__ == '__main__':
    setup_mongodb()
