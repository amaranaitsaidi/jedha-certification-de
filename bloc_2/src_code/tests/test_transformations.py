"""
Unit Tests for Data Transformation Functions
=============================================
Tests unitaires pour les fonctions de transformation du pipeline ETL.

Usage:
    pytest tests/test_transformations.py -v
    pytest tests/test_transformations.py -m unit
"""

import os
import sys
import pandas as pd
import pytest
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.process_and_store import ReviewProcessor


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_reviews_df():
    """Create a sample reviews DataFrame for testing."""
    return pd.DataFrame({
        'review_id': [1, 2, 3, 4, 5],
        'rating': [5, 4, 3, 2, 1],
        'title': ['Great', 'Good', 'OK', 'Bad', 'Terrible'],
        'description': ['Excellent product', 'Nice', 'Average', 'Not good', 'Waste of money'],
        'buyer_id': ['B1', 'B2', 'B3', 'B4', 'B5'],
        'p_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
        'product_name': ['Product 1', 'Product 2', 'Product 3', 'Product 4', 'Product 5'],
        'category': ['Electronics', 'Electronics', 'Books', 'Books', 'Electronics'],
        'text_length': [17, 4, 7, 8, 15],
        'has_image': [1, 1, 0, 0, 1],
        'has_orders': [1, 1, 1, 0, 0]
    })


@pytest.fixture
def reviews_with_duplicates():
    """Create DataFrame with duplicate review_ids."""
    return pd.DataFrame({
        'review_id': [1, 2, 2, 3, 4],  # review_id 2 is duplicated
        'rating': [5, 4, 4, 3, 2],
        'title': ['Great', 'Good', 'Good Duplicate', 'OK', 'Bad'],
        'description': ['Excellent', 'Nice', 'Nice duplicate', 'Average', 'Not good'],
        'buyer_id': ['B1', 'B2', 'B2', 'B3', 'B4'],
        'p_id': ['P1', 'P2', 'P2', 'P3', 'P4'],
        'product_name': ['Product 1', 'Product 2', 'Product 2', 'Product 3', 'Product 4'],
        'category': ['Electronics', 'Electronics', 'Electronics', 'Books', 'Books'],
        'text_length': [9, 4, 14, 7, 8],
        'has_image': [1, 1, 1, 0, 0],
        'has_orders': [1, 1, 1, 1, 0]
    })


@pytest.fixture
def reviews_with_nulls():
    """Create DataFrame with NULL values in required fields."""
    return pd.DataFrame({
        'review_id': [1, 2, None, 4, 5],  # NULL review_id
        'rating': [5, None, 3, 2, 1],  # NULL rating
        'title': ['Great', 'Good', 'OK', 'Bad', None],
        'description': ['Excellent', 'Nice', 'Average', None, 'Waste'],
        'buyer_id': ['B1', 'B2', 'B3', None, 'B5'],  # NULL buyer_id
        'p_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
        'product_name': ['Product 1', 'Product 2', 'Product 3', 'Product 4', 'Product 5'],
        'category': ['Electronics', 'Electronics', 'Books', 'Books', 'Electronics'],
        'text_length': [9, 4, 7, 0, 5],
        'has_image': [1, 1, 0, 0, 1],
        'has_orders': [1, 1, 1, 0, 0]
    })


@pytest.fixture
def reviews_with_invalid_ratings():
    """Create DataFrame with invalid rating values."""
    return pd.DataFrame({
        'review_id': [1, 2, 3, 4, 5],
        'rating': [5, 6, 0, -1, 3],  # 6, 0, -1 are invalid (should be 1-5)
        'title': ['Great', 'Good', 'OK', 'Bad', 'Terrible'],
        'description': ['Excellent', 'Nice', 'Average', 'Not good', 'Waste'],
        'buyer_id': ['B1', 'B2', 'B3', 'B4', 'B5'],
        'p_id': ['P1', 'P2', 'P3', 'P4', 'P5'],
        'product_name': ['Product 1', 'Product 2', 'Product 3', 'Product 4', 'Product 5'],
        'category': ['Electronics', 'Electronics', 'Books', 'Books', 'Electronics'],
        'text_length': [9, 4, 7, 8, 5],
        'has_image': [1, 1, 0, 0, 1],
        'has_orders': [1, 1, 1, 0, 0]
    })


@pytest.fixture
def review_processor():
    """Create ReviewProcessor instance for testing."""
    return ReviewProcessor()


# ============================================================================
# UNIT TESTS - DATA CLEANING
# ============================================================================

@pytest.mark.unit
@pytest.mark.cleaning
def test_clean_data_with_no_issues(review_processor, sample_reviews_df):
    """Test cleaning function with perfectly clean data."""
    df_clean, df_rejected = review_processor.clean_and_validate(sample_reviews_df)

    assert len(df_clean) == 5, "All records should be clean"
    assert len(df_rejected) == 0, "No records should be rejected"
    print(f"✓ Clean data: {len(df_clean)} records passed, {len(df_rejected)} rejected")


@pytest.mark.unit
@pytest.mark.cleaning
@pytest.mark.duplicates
def test_detect_duplicates(review_processor, reviews_with_duplicates):
    """Test duplicate detection and removal."""
    df_clean, df_rejected = review_processor.clean_and_validate(reviews_with_duplicates)

    # Should have 4 clean records (1 duplicate removed)
    assert len(df_clean) == 4, f"Expected 4 clean records, got {len(df_clean)}"
    assert len(df_rejected) == 1, f"Expected 1 rejected record, got {len(df_rejected)}"

    # Check that rejected record has correct reason
    if len(df_rejected) > 0:
        assert 'duplicate' in df_rejected.iloc[0]['rejection_reason'], "Rejection reason should contain 'duplicate'"

    # Ensure review_id 2 appears only once in clean data
    clean_review_ids = df_clean['review_id'].tolist()
    assert clean_review_ids.count(2) == 1, "Duplicate review_id should appear only once"

    print(f"✓ Duplicates handled: {len(df_clean)} clean, {len(df_rejected)} rejected")


@pytest.mark.unit
@pytest.mark.cleaning
@pytest.mark.nulls
def test_detect_null_values(review_processor, reviews_with_nulls):
    """Test NULL value detection in required fields."""
    df_clean, df_rejected = review_processor.clean_and_validate(reviews_with_nulls)

    # Should reject records with NULL in required fields (review_id, rating, buyer_id)
    assert len(df_rejected) > 0, "Should reject records with NULL values"

    # Check rejection reasons (df_rejected is a DataFrame)
    if len(df_rejected) > 0:
        null_rejections = df_rejected[df_rejected['rejection_reason'].str.contains('missing', case=False, na=False)]
        assert len(null_rejections) > 0, "Should have NULL/missing-related rejections"

    print(f"✓ NULL values handled: {len(df_clean)} clean, {len(df_rejected)} rejected")


@pytest.mark.unit
@pytest.mark.cleaning
@pytest.mark.ratings
def test_detect_invalid_ratings(review_processor, reviews_with_invalid_ratings):
    """Test invalid rating detection (must be 1-5)."""
    df_clean, df_rejected = review_processor.clean_and_validate(reviews_with_invalid_ratings)

    # Should reject records with ratings outside 1-5 range
    assert len(df_rejected) > 0, "Should reject records with invalid ratings"

    # Check that clean data only has ratings between 1-5
    if len(df_clean) > 0:
        assert df_clean['rating'].min() >= 1, "Clean data should have ratings >= 1"
        assert df_clean['rating'].max() <= 5, "Clean data should have ratings <= 5"

    print(f"✓ Invalid ratings handled: {len(df_clean)} clean, {len(df_rejected)} rejected")


# ============================================================================
# UNIT TESTS - DATA VALIDATION
# ============================================================================

@pytest.mark.unit
@pytest.mark.validation
def test_required_columns_present(sample_reviews_df):
    """Test that required columns are present in DataFrame."""
    required_columns = ['review_id', 'rating', 'buyer_id', 'p_id']

    for col in required_columns:
        assert col in sample_reviews_df.columns, f"Required column '{col}' is missing"

    print(f"✓ All required columns present: {required_columns}")


@pytest.mark.unit
@pytest.mark.validation
def test_data_types_after_cleaning(review_processor, sample_reviews_df):
    """Test that data types are correct after cleaning."""
    df_clean, _ = review_processor.clean_and_validate(sample_reviews_df)

    if len(df_clean) > 0:
        # Check that rating is numeric
        assert pd.api.types.is_numeric_dtype(df_clean['rating']), "Rating should be numeric"

        # Check that review_id is not null
        assert df_clean['review_id'].notna().all(), "Review IDs should not be NULL"

    print(f"✓ Data types validated for {len(df_clean)} records")


@pytest.mark.unit
@pytest.mark.validation
@pytest.mark.parametrize("rating,is_valid", [
    (1, True),
    (2, True),
    (3, True),
    (4, True),
    (5, True),
    (0, False),
    (6, False),
    (-1, False),
])
def test_rating_validation_logic(rating, is_valid):
    """Test rating validation logic with different values."""
    result = 1 <= rating <= 5

    assert result == is_valid, f"Rating {rating} validation failed: expected {is_valid}, got {result}"

    if is_valid:
        print(f"  ✓ Rating {rating} is valid")
    else:
        print(f"  ✓ Rating {rating} is correctly invalid")


# ============================================================================
# UNIT TESTS - DATA TRANSFORMATION
# ============================================================================

@pytest.mark.unit
@pytest.mark.transformation
def test_dataframe_shape_after_cleaning(review_processor, sample_reviews_df):
    """Test that DataFrame shape is correct after cleaning."""
    original_rows = len(sample_reviews_df)
    original_cols = len(sample_reviews_df.columns)

    df_clean, df_rejected = review_processor.clean_and_validate(sample_reviews_df)

    # Total records should match
    assert len(df_clean) + len(df_rejected) == original_rows, \
        "Total records (clean + rejected) should match original"

    # Columns should remain the same
    if len(df_clean) > 0:
        assert len(df_clean.columns) == original_cols, \
            "Number of columns should remain the same"

    print(f"✓ DataFrame shape: {original_rows} → {len(df_clean)} clean + {len(df_rejected)} rejected")


@pytest.mark.unit
@pytest.mark.transformation
def test_no_data_loss_during_cleaning(review_processor, sample_reviews_df):
    """Test that no valid data is lost during cleaning."""
    original_count = len(sample_reviews_df)
    df_clean, df_rejected = review_processor.clean_and_validate(sample_reviews_df)

    total_after = len(df_clean) + len(df_rejected)

    assert total_after == original_count, \
        f"Data loss detected: started with {original_count}, ended with {total_after}"

    print(f"✓ No data loss: {original_count} → {total_after} records accounted for")


# ============================================================================
# INTEGRATION TESTS (Marked as slow)
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
def test_full_cleaning_pipeline(review_processor):
    """Test full cleaning pipeline with mixed data quality issues."""
    # Create DataFrame with multiple issues
    mixed_df = pd.DataFrame({
        'review_id': [1, 2, 2, None, 5, 6],  # Has duplicate and NULL
        'rating': [5, 4, 4, 3, 0, 6],  # Has invalid ratings (0, 6)
        'title': ['Great', 'Good', 'Good', 'OK', 'Bad', 'Terrible'],
        'description': ['Excellent', 'Nice', 'Nice', 'Average', 'Not good', 'Waste'],
        'buyer_id': ['B1', 'B2', 'B2', 'B3', 'B4', None],  # Has NULL
        'p_id': ['P1', 'P2', 'P2', 'P3', 'P4', 'P5'],
        'product_name': ['P1', 'P2', 'P2', 'P3', 'P4', 'P5'],
        'category': ['Electronics', 'Electronics', 'Electronics', 'Books', 'Books', 'Electronics'],
        'text_length': [9, 4, 4, 7, 8, 5],
        'has_image': [1, 1, 1, 0, 0, 1],
        'has_orders': [1, 1, 1, 1, 0, 0]
    })

    df_clean, df_rejected = review_processor.clean_and_validate(mixed_df)

    # Should have rejections due to multiple issues
    assert len(df_rejected) > 0, "Should detect and reject problematic records"

    # All clean records should be valid
    if len(df_clean) > 0:
        assert df_clean['rating'].between(1, 5).all(), "All clean ratings should be 1-5"
        assert df_clean['review_id'].notna().all(), "No NULL review_ids in clean data"
        assert df_clean['buyer_id'].notna().all(), "No NULL buyer_ids in clean data"

    print(f"✓ Full pipeline test: {len(df_clean)} clean, {len(df_rejected)} rejected from {len(mixed_df)} records")
