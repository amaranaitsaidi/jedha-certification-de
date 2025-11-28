import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Charger .env depuis le répertoire parent (racine du projet)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Pull from environment or default to a local Docker network URL
db_url = os.getenv("DATABASE_URL")

if not db_url:
    raise ValueError("DATABASE_URL n'est pas défini dans le fichier .env")

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()