"""
Verify MongoDB Data Storage
============================
Quick script to verify data stored in MongoDB
"""

from pymongo import MongoClient
from dotenv import load_dotenv
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Connect to MongoDB
connection_string = os.getenv('MONGODB_CONNECTION_STRING')
client = MongoClient(connection_string)
db = client['amazon_reviews']

print("=" * 80)
print("MONGODB DATA VERIFICATION")
print("=" * 80)

# 1. Check Pipeline Logs
print("\n1. PIPELINE LOGS")
print("-" * 80)
logs_collection = db['pipeline_logs']
log_count = logs_collection.count_documents({})
print(f"Total logs: {log_count:,}")

if log_count > 0:
    print("\nLatest 10 logs:")
    for log in logs_collection.find().sort('timestamp', -1).limit(10):
        print(f"  [{log['timestamp']}] {log['level']:8} - {log['message']}")

# 2. Check Rejected Reviews
print("\n2. REJECTED REVIEWS")
print("-" * 80)
rejected_collection = db['rejected_reviews']
rejected_count = rejected_collection.count_documents({})
print(f"Total rejected: {rejected_count:,}")

if rejected_count > 0:
    # Count by rejection reason
    pipeline = [
        {"$group": {
            "_id": "$rejection_reason",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}}
    ]
    print("\nRejection reasons:")
    for reason in rejected_collection.aggregate(pipeline):
        print(f"  {reason['_id']:30} : {reason['count']:,}")

# 3. Check Pipeline Metadata
print("\n3. PIPELINE METADATA")
print("-" * 80)
metadata_collection = db['pipeline_metadata']
metadata_count = metadata_collection.count_documents({})
print(f"Total pipeline runs: {metadata_count:,}")

if metadata_count > 0:
    print("\nLatest pipeline run:")
    latest = list(metadata_collection.find().sort('execution_date', -1).limit(1))[0]
    print(f"  Run ID: {latest['pipeline_run_id']}")
    print(f"  Date: {latest['execution_date']}")
    print(f"  Version: {latest['pipeline_version']}")
    print(f"  Stats:")
    for key, value in latest['stats'].items():
        print(f"    {key:30} : {value:,}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)

client.close()
