"""
Fonctions CRUD pour interroger Snowflake
"""
from snowflake_connector import execute_query
import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from current directory or parent directory
env_path = Path('.env')
if not env_path.exists():
    env_path = Path('../.env')

load_dotenv(dotenv_path=env_path)


database= os.getenv('SNOWFLAKE_DATABASE')
schema=os.getenv('SNOWFLAKE_SCHEMA_ANALYTICS')

def get_all_products_from_snowflake(limit: int = 100):
    """
    Récupère la liste de tous les produits disponibles depuis Snowflake.

    Args:
        limit: Nombre maximum de produits à retourner (par défaut: 100)

    Returns:
        Liste des produits uniques avec leurs informations
    """
    query = f"""
        SELECT DISTINCT
            P_ID,
            PRODUCT_NAME,
            CATEGORY
        FROM {database}.{schema}.review_relevant
        ORDER BY PRODUCT_NAME
        LIMIT %(limit)s
    """

    results = execute_query(query, {"limit": limit})

    products = []
    for row in results:
        products.append({
            "p_id": row["P_ID"],
            "product_name": row["PRODUCT_NAME"],
            "category": row.get("CATEGORY")
        })

    return products


def get_buyer_products_from_snowflake(buyer_id: str):
    """
    Récupère la liste des produits achetés par un buyer depuis Snowflake.

    Args:
        buyer_id: ID de l'acheteur

    Returns:
        Liste des produits uniques achetés par le buyer
    """
    query = f"""
        SELECT DISTINCT
            P_ID,
            PRODUCT_NAME,
            CATEGORY
        FROM {database}.{schema}.review_relevant
        WHERE BUYER_ID = %(buyer_id)s
        ORDER BY P_ID
    """

    results = execute_query(query, {"buyer_id": buyer_id})

    products = []
    for row in results:
        products.append({
            "p_id": row["P_ID"],
            "product_name": row["PRODUCT_NAME"],
            "category": row.get("CATEGORY")
        })

    return products


def get_product_reviews_from_snowflake(p_id: str, limit: int = 10):
    """
    Récupère les reviews pertinentes (RELEVANT_STATUS = 'RELEVANT')
    pour un produit spécifique depuis Snowflake (tous les buyers).

    Args:
        p_id: ID du produit
        limit: Nombre maximum de reviews à retourner (par défaut: 10)

    Returns:
        Liste des reviews avec tous les scores et métadonnées
    """
    # Requête pour récupérer les reviews depuis la table staging
    query = f"""
        SELECT
            REVIEW_ID,
            BUYER_ID,
            P_ID,
            PRODUCT_NAME,
            CATEGORY,
            TITLE,
            DESCRIPTION,
            RATING,
            TEXT_LENGTH,
            HAS_IMAGE,
            HAS_ORDERS,
            TEXT_LENGTH_SCORE,
            IS_EXTREME_RATING,
            KEYWORD_SCORE,
            RELEVANCE_SCORE,
            CATEGORY_REVIEW,
            CONFIDENCE_SCORE,
            RELEVANT_STATUS,
            REVIEW_IMG
        FROM {database}.{schema}.review_relevant
        WHERE P_ID = %(p_id)s
          AND RELEVANT_STATUS = 'RELEVANT'
        ORDER BY RELEVANCE_SCORE DESC
        LIMIT %(limit)s
    """

    reviews = execute_query(query, {"p_id": p_id, "limit": limit})

    # Transformer les résultats
    for review in reviews:
        # Gérer les images - soit une seule URL, soit multiple
        review_img = review.get("REVIEW_IMG")
        if review_img:
            # Si c'est une chaîne avec des virgules, séparer
            if isinstance(review_img, str) and ',' in review_img:
                images = [img.strip() for img in review_img.split(',') if img.strip()]
            elif isinstance(review_img, str):
                images = [review_img] if review_img else []
            else:
                images = []
        else:
            images = []

        # Renommer et formater les champs
        review["review_id"] = review.pop("REVIEW_ID")
        review["buyer_id"] = review.pop("BUYER_ID")
        review["p_id"] = review.pop("P_ID")
        review["product_name"] = review.pop("PRODUCT_NAME")
        review["category"] = review.pop("CATEGORY")
        review["title"] = review.pop("TITLE")
        review["r_desc"] = review.pop("DESCRIPTION")
        review["rating"] = review.pop("RATING")
        review["text_length"] = review.pop("TEXT_LENGTH")
        review["has_image"] = bool(review.pop("HAS_IMAGE"))
        review["has_orders"] = bool(review.pop("HAS_ORDERS"))
        review["text_length_score"] = review.pop("TEXT_LENGTH_SCORE")
        review["is_extreme_rating"] = bool(review.pop("IS_EXTREME_RATING"))
        review["keyword_score"] = review.pop("KEYWORD_SCORE")
        review["relevance_score"] = review.pop("RELEVANCE_SCORE")
        review["category_review"] = review.pop("CATEGORY_REVIEW")
        review["confidence_score"] = review.pop("CONFIDENCE_SCORE")
        review["relevant_status"] = review.pop("RELEVANT_STATUS")
        review["images"] = images
        review.pop("REVIEW_IMG", None)

    return reviews


def get_relevant_reviews_from_snowflake(buyer_id: str, p_id: str):
    """
    Récupère les reviews pertinentes (RELEVANT_STATUS = 'RELEVANT')
    d'un buyer pour un produit spécifique depuis Snowflake.

    Args:
        buyer_id: ID de l'acheteur
        p_id: ID du produit

    Returns:
        Liste des reviews avec tous les scores et métadonnées
    """
    # Requête pour récupérer les reviews depuis la table staging
    query = f"""
        SELECT
            REVIEW_ID,
            BUYER_ID,
            P_ID,
            PRODUCT_NAME,
            CATEGORY,
            TITLE,
            DESCRIPTION,
            RATING,
            TEXT_LENGTH,
            HAS_IMAGE,
            HAS_ORDERS,
            TEXT_LENGTH_SCORE,
            IS_EXTREME_RATING,
            KEYWORD_SCORE,
            RELEVANCE_SCORE,
            CATEGORY_REVIEW,
            CONFIDENCE_SCORE,
            RELEVANT_STATUS,
            REVIEW_IMG
        FROM {database}.{schema}.review_relevant
        WHERE BUYER_ID = %(buyer_id)s
          AND P_ID = %(p_id)s
          AND RELEVANT_STATUS = 'RELEVANT'
        ORDER BY RELEVANCE_SCORE DESC
    """

    reviews = execute_query(query, {"buyer_id": buyer_id, "p_id": p_id})

    # Transformer les résultats
    for review in reviews:
        # Gérer les images - soit une seule URL, soit multiple
        review_img = review.get("REVIEW_IMG")
        if review_img:
            # Si c'est une chaîne avec des virgules, séparer
            if isinstance(review_img, str) and ',' in review_img:
                images = [img.strip() for img in review_img.split(',') if img.strip()]
            elif isinstance(review_img, str):
                images = [review_img] if review_img else []
            else:
                images = []
        else:
            images = []

        # Renommer et formater les champs
        review["review_id"] = review.pop("REVIEW_ID")
        review["buyer_id"] = review.pop("BUYER_ID")
        review["p_id"] = review.pop("P_ID")
        review["product_name"] = review.pop("PRODUCT_NAME")
        review["category"] = review.pop("CATEGORY")
        review["title"] = review.pop("TITLE")
        review["r_desc"] = review.pop("DESCRIPTION")
        review["rating"] = review.pop("RATING")
        review["text_length"] = review.pop("TEXT_LENGTH")
        review["has_image"] = bool(review.pop("HAS_IMAGE"))
        review["has_orders"] = bool(review.pop("HAS_ORDERS"))
        review["text_length_score"] = review.pop("TEXT_LENGTH_SCORE")
        review["is_extreme_rating"] = bool(review.pop("IS_EXTREME_RATING"))
        review["keyword_score"] = review.pop("KEYWORD_SCORE")
        review["relevance_score"] = review.pop("RELEVANCE_SCORE")
        review["category_review"] = review.pop("CATEGORY_REVIEW")
        review["confidence_score"] = review.pop("CONFIDENCE_SCORE")
        review["relevant_status"] = review.pop("RELEVANT_STATUS")
        review["images"] = images
        review.pop("REVIEW_IMG", None)

    return reviews
