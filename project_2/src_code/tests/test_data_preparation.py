"""
Unit tests for data preparation module.
"""

import pytest
import pandas as pd
from src.modules.data_preparation import DataPreparation


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        'preparation': {
            'min_text_length': 0
        },
        'scoring': {
            'optimal_text_length': 300,
            'text_length_sigma': 200,
            'max_keywords': 10,
            'weights': {
                'text_length': 0.25,
                'has_image': 0.20,
                'has_orders': 0.15,
                'extreme_rating': 0.15,
                'keywords': 0.25
            }
        },
        'keywords': {
            'positive': ['excellent', 'great', 'quality'],
            'negative': ['poor', 'bad', 'defect']
        }
    }


@pytest.fixture
def sample_dataframe():
    """Sample DataFrame for testing."""
    return pd.DataFrame({
        'review_id': [1, 2, 3],
        'title': ['Great!', 'Bad product', 'Excellent quality'],
        'description': [
            'This is an excellent product with great quality.',
            'Poor quality, very bad.',
            'Amazing! Highly recommend.'
        ],
        'rating': [5, 1, 5],
        'has_image': [1, 0, 1],
        'has_orders': [1, 1, 0],
        'text_length': [46, 22, 27]
    })


def test_clean_text(sample_config):
    """Test text cleaning functionality."""
    prep = DataPreparation(sample_config)

    # Test normal text
    assert prep.clean_text("  Hello   World  ") == "Hello World"

    # Test empty text
    assert prep.clean_text("") == ""

    # Test None
    assert prep.clean_text(None) == ""


def test_prepare_data(sample_config, sample_dataframe):
    """Test data preparation."""
    prep = DataPreparation(sample_config)
    df_clean = prep.prepare_data(sample_dataframe)

    # Check no duplicates
    assert len(df_clean) == len(df_clean['review_id'].unique())

    # Check text is cleaned
    assert not df_clean['description'].isna().any()


def test_calculate_features(sample_config, sample_dataframe):
    """Test feature calculation."""
    prep = DataPreparation(sample_config)
    df_features = prep.calculate_features(sample_dataframe)

    # Check new columns exist
    assert 'text_length_score' in df_features.columns
    assert 'is_extreme_rating' in df_features.columns
    assert 'keyword_score' in df_features.columns

    # Check extreme rating calculation
    assert df_features[df_features['rating'] == 5]['is_extreme_rating'].all()
    assert df_features[df_features['rating'] == 1]['is_extreme_rating'].all()


def test_calculate_relevance_score(sample_config, sample_dataframe):
    """Test relevance score calculation."""
    prep = DataPreparation(sample_config)
    df_features = prep.calculate_features(sample_dataframe)
    df_scored = prep.calculate_relevance_score(df_features)

    # Check relevance_score exists
    assert 'relevance_score' in df_scored.columns

    # Check score range
    assert (df_scored['relevance_score'] >= 0).all()
    assert (df_scored['relevance_score'] <= 100).all()


def test_keyword_score_calculation(sample_config):
    """Test keyword scoring."""
    prep = DataPreparation(sample_config)

    # Text with positive keywords
    score1 = prep._calculate_keyword_score(
        "This is an excellent product with great quality",
        ['excellent', 'great', 'quality', 'poor', 'bad']
    )
    assert score1 > 0

    # Text with no keywords
    score2 = prep._calculate_keyword_score(
        "This is a product",
        ['excellent', 'great', 'quality']
    )
    assert score2 == 0

    # Empty text
    score3 = prep._calculate_keyword_score("", ['excellent'])
    assert score3 == 0
