"""
Pytest Configuration and Shared Fixtures
=========================================
Configuration file for pytest containing shared fixtures
used across all test modules.
"""

import os
import sys
import pandas as pd
import pytest
from dotenv import load_dotenv
import psycopg2

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def db_connection():
    """
    Fixture: PostgreSQL database connection (session-scoped).

    This fixture creates a single database connection that is shared
    across all tests in a session. The connection is automatically
    closed at the end of the session.

    Yields:
        psycopg2.connection: Active database connection
    """
    conn = psycopg2.connect(os.getenv('POSTGRES_CONNECTION_STRING'))
    yield conn
    conn.close()


# ============================================================================
# DATA FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def review_data(db_connection):
    """
    Fixture: Load review data sample for testing.

    Loads a sample of 10,000 reviews from the database. This data
    is used for data quality tests that don't need the full dataset.

    Args:
        db_connection: Database connection fixture

    Returns:
        pd.DataFrame: Sample of review data with columns:
            - review_id: Unique review identifier
            - rating: Review rating (1-5)
            - buyer_id: Customer identifier
            - r_desc: Review text description
    """
    query = """
        SELECT review_id, rating, buyer_id, r_desc
        FROM review
        LIMIT 10000;
    """
    return pd.read_sql_query(query, db_connection)


@pytest.fixture(scope="session")
def product_data(db_connection):
    """
    Fixture: Load product data for testing.

    Loads all products from the database for validation tests.

    Args:
        db_connection: Database connection fixture

    Returns:
        pd.DataFrame: Product data with columns:
            - p_id: Product identifier
            - p_name: Product name
            - price: Product price
    """
    query = "SELECT p_id, p_name, price FROM product;"
    return pd.read_sql_query(query, db_connection)


@pytest.fixture(scope="session")
def product_reviews_data(db_connection):
    """
    Fixture: Load product_reviews relationship data.

    Loads the many-to-many relationship between products and reviews.
    Limited to 1,000 records for faster testing.

    Args:
        db_connection: Database connection fixture

    Returns:
        pd.DataFrame: Product-review relationship data with columns:
            - review_id: Review identifier
            - p_id: Product identifier
    """
    query = "SELECT review_id, p_id FROM product_reviews LIMIT 1000;"
    return pd.read_sql_query(query, db_connection)


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """
    Fixture: Test configuration parameters.

    Returns:
        dict: Configuration dictionary with test parameters
    """
    return {
        'max_empty_text_percentage': 10,  # Max % of empty review texts allowed
        'min_rating': 1,
        'max_rating': 5,
        'min_price': 0,
        'required_columns': ['review_id', 'rating', 'buyer_id'],
    }


# ============================================================================
# PYTEST HOOKS
# ============================================================================

def pytest_configure(config):
    """
    Pytest hook: Called after command line options are parsed.

    This hook adds custom configuration and displays information
    about the test environment.
    """
    print("\n" + "=" * 70)
    print("Amazon Reviews ETL - Data Quality Test Suite")
    print("=" * 70)
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Test directory: {os.path.dirname(__file__)}")
    print("=" * 70 + "\n")


def pytest_collection_finish(session):
    """
    Pytest hook: Called after test collection is finished.

    Displays the number of collected tests.
    """
    if session.config.option.collectonly:
        print(f"\nCollected {len(session.items)} test(s)")


def pytest_sessionfinish(session, exitstatus):
    """
    Pytest hook: Called after whole test run finished.

    Displays final summary information.
    """
    print("\n" + "=" * 70)
    print("Test Session Complete")
    print("=" * 70)
