"""
Module pour gérer la connexion à Snowflake
"""
import os
import snowflake.connector
from dotenv import load_dotenv
from pathlib import Path

# Load .env from current directory or parent directory
env_path = Path('.env')
if not env_path.exists():
    env_path = Path('../.env')
load_dotenv(dotenv_path=env_path)

def get_snowflake_connection():
    """
    Crée et retourne une connexion à Snowflake.

    Returns:
        snowflake.connector.connection: Connexion Snowflake active
    """
    conn = snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA'),
        role=os.getenv('SNOWFLAKE_ROLE')
    )
    return conn

def execute_query(query: str, params: dict = None):
    """
    Exécute une requête SQL sur Snowflake et retourne les résultats.

    Args:
        query: Requête SQL à exécuter
        params: Paramètres pour la requête (optionnel)

    Returns:
        list: Liste des résultats
    """
    conn = get_snowflake_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        # Convertir les résultats en liste de dictionnaires
        result_dicts = []
        for row in results:
            result_dicts.append(dict(zip(columns, row)))

        return result_dicts
    finally:
        cursor.close()
        conn.close()
