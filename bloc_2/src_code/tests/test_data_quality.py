"""
Data Quality Tests using pytest and Great Expectations
======================================================
Tests de qualité des données pour le pipeline ETL Amazon Reviews.

Ces tests vérifient :
- L'intégrité des données sources (PostgreSQL)
- La qualité des transformations
- La validité des données finales (Snowflake)

Usage:
    pytest tests/test_data_quality.py -v
    pytest tests/test_data_quality.py -v --html=reports/quality_report.html
    pytest tests/test_data_quality.py -m database
"""

import os
import sys
import pandas as pd
import pytest
import great_expectations as ge
from dotenv import load_dotenv
import psycopg2
from datetime import datetime
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()


# NOTE: Fixtures are defined in conftest.py and automatically available


# ============================================================================
# DATABASE CONNECTION TESTS
# ============================================================================

@pytest.mark.database
@pytest.mark.connection
def test_postgresql_connection(db_connection):
    """Test 1: Vérifier la connexion PostgreSQL."""
    cursor = db_connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM product;")
    count = cursor.fetchone()[0]
    cursor.close()

    assert count > 0, f"Expected products in database, but found {count}"
    print(f"✓ Successfully connected. Found {count:,} products")


# ============================================================================
# DATA QUALITY TESTS - GREAT EXPECTATIONS
# ============================================================================

@pytest.mark.quality
@pytest.mark.ratings
def test_review_ratings_range(review_data):
    """Test 2: Vérifier que tous les ratings sont entre 1-5."""
    ge_df = ge.from_pandas(review_data)

    # Test: ratings between 1 and 5
    result = ge_df.expect_column_values_to_be_between(
        column='rating',
        min_value=1,
        max_value=5
    )

    invalid_count = len(review_data[(review_data['rating'] < 1) | (review_data['rating'] > 5)])

    assert result.success, (
        f"Found {invalid_count} invalid ratings out of {len(review_data)} reviews. "
        f"Min: {review_data['rating'].min()}, Max: {review_data['rating'].max()}"
    )
    print(f"✓ All {len(review_data):,} ratings are valid (1-5)")


@pytest.mark.quality
@pytest.mark.duplicates
def test_no_duplicate_reviews(db_connection):
    """Test 3: Vérifier l'absence de doublons sur review_id."""
    df = pd.read_sql_query("SELECT review_id FROM review;", db_connection)
    ge_df = ge.from_pandas(df)

    # Test: unique review_ids
    result = ge_df.expect_column_values_to_be_unique(column='review_id')
    duplicates = df[df.duplicated(subset=['review_id'], keep=False)]

    assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate review_ids"
    print(f"✓ No duplicates in {len(df):,} reviews")


@pytest.mark.quality
@pytest.mark.nulls
def test_required_fields_not_null(review_data):
    """Test 4: Vérifier que les champs obligatoires ne sont pas NULL."""
    ge_df = ge.from_pandas(review_data)

    errors = []
    for column in ['review_id', 'rating', 'buyer_id']:
        result = ge_df.expect_column_values_to_not_be_null(column=column)
        null_count = review_data[column].isna().sum()

        if not result.success:
            errors.append(f"{column}: {null_count} NULL values")
        else:
            print(f"  ✓ {column}: No NULL values")

    assert len(errors) == 0, f"Required fields with NULL values: {', '.join(errors)}"


@pytest.mark.quality
@pytest.mark.prices
def test_product_prices_positive(product_data):
    """Test 5: Vérifier que tous les prix sont positifs."""
    ge_df = ge.from_pandas(product_data)

    result = ge_df.expect_column_values_to_be_between(
        column='price',
        min_value=0,
        max_value=None
    )

    invalid_prices = product_data[product_data['price'] < 0]

    assert len(invalid_prices) == 0, (
        f"Found {len(invalid_prices)} products with negative prices. "
        f"Min: ${product_data['price'].min():.2f}, Max: ${product_data['price'].max():.2f}"
    )
    print(f"✓ All {len(product_data):,} prices are positive (Avg: ${product_data['price'].mean():.2f})")


@pytest.mark.quality
@pytest.mark.text
def test_review_text_not_empty(review_data):
    """Test 6: Vérifier que les textes de review ne sont pas vides."""
    # Check for NULL and empty strings
    empty_texts = review_data[
        review_data['r_desc'].isna() |
        (review_data['r_desc'].str.strip() == '')
    ]

    empty_percentage = len(empty_texts) / len(review_data) * 100

    # Allow up to 10% empty reviews
    assert empty_percentage < 10, (
        f"Too many empty reviews: {len(empty_texts):,} ({empty_percentage:.1f}%)"
    )
    print(f"✓ {len(review_data) - len(empty_texts):,} reviews have text ({empty_percentage:.1f}% empty)")


@pytest.mark.quality
@pytest.mark.types
def test_data_types_consistency(product_reviews_data):
    """Test 7: Vérifier la cohérence des types de données."""
    ge_df = ge.from_pandas(product_reviews_data)

    # Test: review_id is numeric
    result_review_id = ge_df.expect_column_values_to_be_of_type(
        column='review_id',
        type_='int64'
    )

    assert result_review_id.success, (
        f"Data type inconsistency detected. Column types: {product_reviews_data.dtypes.to_dict()}"
    )
    print(f"✓ Data types are consistent (review_id: {product_reviews_data['review_id'].dtype}, "
          f"p_id: {product_reviews_data['p_id'].dtype})")


@pytest.mark.quality
@pytest.mark.integrity
def test_referential_integrity(db_connection):
    """Test 8: Vérifier l'intégrité référentielle product_reviews -> product."""
    # Get all p_ids from product_reviews
    df_pr = pd.read_sql_query("SELECT DISTINCT p_id FROM product_reviews;", db_connection)

    # Get all p_ids from product
    df_p = pd.read_sql_query("SELECT p_id FROM product;", db_connection)

    # Find orphaned references
    orphaned = df_pr[~df_pr['p_id'].isin(df_p['p_id'])]
    valid_percentage = (1 - len(orphaned) / len(df_pr)) * 100 if len(df_pr) > 0 else 100

    assert len(orphaned) == 0, (
        f"Found {len(orphaned):,} orphaned product references out of {len(df_pr):,} "
        f"({valid_percentage:.1f}% valid)"
    )
    print(f"✓ All {len(df_pr):,} product references are valid")
