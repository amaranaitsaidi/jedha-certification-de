"""
Test Email Alerts Script
=========================
Test the email alerter functionality before deploying to production.

Usage:
    python test_email_alerts.py
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dags'))

from utils.email_alerter import EmailAlerter


def test_s3_extraction_alert():
    """Test alert for failed S3 extraction"""
    print("\n" + "="*80)
    print("TEST 1: S3 Extraction Failure Alert")
    print("="*80)

    alerter = EmailAlerter(
        to_emails=os.getenv("ALERT_EMAIL", "test@example.com").split(",")
    )

    # Simulate failed extraction
    tables = {
        "product": "s3://bucket/raw/product/product.csv",
        "category": None,  # Failed
        "review": "s3://bucket/raw/review/review.csv",
        "orders": None,  # Failed
    }

    success = alerter.alert_no_data_from_s3(
        dag_id="test_dag",
        task_id="test_extract_to_s3",
        execution_date=datetime.now().isoformat(),
        tables=tables
    )

    if success:
        print("[OK] S3 extraction alert sent successfully")
    else:
        print("[FAIL] Failed to send S3 extraction alert")

    return success


def test_snowflake_load_alert():
    """Test alert for no data loaded to Snowflake"""
    print("\n" + "="*80)
    print("TEST 2: Snowflake Load Failure Alert")
    print("="*80)

    alerter = EmailAlerter(
        to_emails=os.getenv("ALERT_EMAIL", "test@example.com").split(",")
    )

    success = alerter.alert_no_data_to_snowflake(
        dag_id="test_dag",
        task_id="test_load_to_snowflake",
        execution_date=datetime.now().isoformat(),
        rows_inserted=0
    )

    if success:
        print("[OK] Snowflake load alert sent successfully")
    else:
        print("[FAIL] Failed to send Snowflake load alert")

    return success


def test_pipeline_success():
    """Test success notification"""
    print("\n" + "="*80)
    print("TEST 3: Pipeline Success Notification")
    print("="*80)

    alerter = EmailAlerter(
        to_emails=os.getenv("ALERT_EMAIL", "test@example.com").split(",")
    )

    stats = {
        "snowflake_inserts": 15234,
        "mongodb_inserts": 45
    }

    success = alerter.alert_pipeline_success(
        dag_id="test_dag",
        execution_date=datetime.now().isoformat(),
        stats=stats
    )

    if success:
        print("[OK] Pipeline success notification sent successfully")
    else:
        print("[FAIL] Failed to send pipeline success notification")

    return success


def main():
    """Run all tests"""
    print("="*80)
    print("EMAIL ALERTS TEST SUITE")
    print("="*80)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Recipients: {os.getenv('ALERT_EMAIL', 'NOT CONFIGURED')}")
    print(f"SMTP Host: {os.getenv('AIRFLOW__SMTP__SMTP_HOST', 'NOT CONFIGURED')}")
    print(f"SMTP Port: {os.getenv('AIRFLOW__SMTP__SMTP_PORT', 'NOT CONFIGURED')}")
    print("="*80)

    # Check configuration
    if not os.getenv("ALERT_EMAIL"):
        print("\n[WARNING] ALERT_EMAIL not configured in .env")
        print("Please configure ALERT_EMAIL before running tests")
        return

    if not os.getenv("AIRFLOW__SMTP__SMTP_HOST"):
        print("\n[WARNING] SMTP configuration missing in .env")
        print("Please configure SMTP settings before running tests")
        return

    # Run tests
    results = []

    try:
        results.append(("S3 Extraction Alert", test_s3_extraction_alert()))
    except Exception as e:
        print(f"[ERROR] S3 extraction alert test failed: {e}")
        results.append(("S3 Extraction Alert", False))

    try:
        results.append(("Snowflake Load Alert", test_snowflake_load_alert()))
    except Exception as e:
        print(f"[ERROR] Snowflake load alert test failed: {e}")
        results.append(("Snowflake Load Alert", False))

    try:
        results.append(("Pipeline Success", test_pipeline_success()))
    except Exception as e:
        print(f"[ERROR] Pipeline success test failed: {e}")
        results.append(("Pipeline Success", False))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {test_name}")

    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)

    print("="*80)
    print(f"Results: {passed_tests}/{total_tests} tests passed")
    print("="*80)

    if passed_tests == total_tests:
        print("\n[SUCCESS] All email alerts are working correctly!")
        print("Check your email inbox for the test messages.")
        return 0
    else:
        print("\n[FAILURE] Some tests failed. Check the error messages above.")
        print("Common issues:")
        print("  - SMTP configuration incorrect")
        print("  - Firewall blocking SMTP port")
        print("  - Invalid email credentials")
        return 1


if __name__ == "__main__":
    sys.exit(main())
