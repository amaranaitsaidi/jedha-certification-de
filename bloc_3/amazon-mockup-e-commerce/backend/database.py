import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import snowflake.connector

# Charger .env depuis le répertoire parent (racine du projet)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# ============================================
# PostgreSQL Connection (for e-commerce tables)
# ============================================
db_url = os.getenv("DATABASE_URL")

if not db_url:
    raise ValueError("DATABASE_URL n'est pas défini dans le fichier .env")

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ============================================
# Snowflake Connection (for reviews)
# ============================================
def get_snowflake_connection():
    """
    Creates and returns a Snowflake connection for reviews data.
    """
    conn = snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA_STAGING', 'STAGING'),
        role=os.getenv('SNOWFLAKE_ROLE')
    )
    return conn