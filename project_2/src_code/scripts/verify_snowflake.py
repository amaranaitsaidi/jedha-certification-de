"""
Verify Snowflake Data Storage
==============================
Quick script to verify data stored in Snowflake
"""

import snowflake.connector
from dotenv import load_dotenv
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Connect to Snowflake
conn = snowflake.connector.connect(
    user=os.getenv('SNOWFLAKE_USER'),
    password=os.getenv('SNOWFLAKE_PASSWORD'),
    account=os.getenv('SNOWFLAKE_ACCOUNT'),
    warehouse=os.getenv('SNOWFLAKE_WAREHOUSE', 'COMPUTE_WH'),
    database=os.getenv('SNOWFLAKE_DATABASE', 'AMAZON_REVIEWS'),
    schema=os.getenv('SNOWFLAKE_SCHEMA', 'ANALYTICS'),
    role=os.getenv('SNOWFLAKE_ROLE', 'SYSADMIN')
)

cursor = conn.cursor()

print("=" * 80)
print("SNOWFLAKE DATA VERIFICATION")
print("=" * 80)

# 1. Check total count
print("\n1. TOTAL REVIEWS IN SNOWFLAKE")
print("-" * 80)
cursor.execute("SELECT COUNT(*) FROM reviews")
total_count = cursor.fetchone()[0]
print(f"Total reviews: {total_count:,}")

# 2. Check by rating
print("\n2. REVIEWS BY RATING")
print("-" * 80)
cursor.execute("""
    SELECT rating, COUNT(*) as count
    FROM reviews
    GROUP BY rating
    ORDER BY rating
""")
print("Rating | Count")
print("-------|----------")
for row in cursor:
    print(f"  {row[0]}    | {row[1]:,}")

# 3. Check by category
print("\n3. REVIEWS BY CATEGORY")
print("-" * 80)
cursor.execute("""
    SELECT category, COUNT(*) as count
    FROM reviews
    GROUP BY category
    ORDER BY count DESC
    LIMIT 10
""")
print(f"{'Category':<30} | Count")
print("-" * 30 + "|----------")
for row in cursor:
    print(f"{row[0]:<30} | {row[1]:,}")

# 4. Check data with images
print("\n4. REVIEWS WITH IMAGES")
print("-" * 80)
cursor.execute("""
    SELECT has_image, COUNT(*) as count
    FROM reviews
    GROUP BY has_image
""")
for row in cursor:
    status = "With images" if row[0] else "Without images"
    print(f"{status:20} : {row[1]:,}")

# 5. Check data with orders
print("\n5. REVIEWS WITH ORDERS")
print("-" * 80)
cursor.execute("""
    SELECT has_orders, COUNT(*) as count
    FROM reviews
    GROUP BY has_orders
""")
for row in cursor:
    status = "With orders" if row[0] else "Without orders"
    print(f"{status:20} : {row[1]:,}")

# 6. Check latest ingestion
print("\n6. LATEST INGESTION")
print("-" * 80)
cursor.execute("""
    SELECT
        pipeline_version,
        ingestion_timestamp,
        COUNT(*) as count
    FROM reviews
    GROUP BY pipeline_version, ingestion_timestamp
    ORDER BY ingestion_timestamp DESC
    LIMIT 5
""")
print(f"{'Version':<10} | {'Timestamp':<20} | Count")
print("-" * 10 + "|" + "-" * 20 + "|----------")
for row in cursor:
    print(f"{row[0]:<10} | {str(row[1]):<20} | {row[2]:,}")

# 7. Sample data
print("\n7. SAMPLE DATA (First 5 rows)")
print("-" * 80)
cursor.execute("""
    SELECT
        review_id,
        rating,
        category,
        product_name,
        SUBSTRING(title, 1, 40) as title
    FROM reviews
    LIMIT 5
""")
for row in cursor:
    print(f"  {row[0]} | Rating: {row[1]} | {row[2]} | {row[4][:40] if row[4] else 'N/A'}")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)

cursor.close()
conn.close()
