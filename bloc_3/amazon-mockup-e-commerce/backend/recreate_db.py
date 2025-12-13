"""
Script pour recréer toutes les tables PostgreSQL avec les nouveaux schémas.
ATTENTION: Cela supprimera toutes les données existantes !
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, str(Path(__file__).parent))

from database import Base, engine
import models

def recreate_database():
    """Supprime et recrée toutes les tables."""
    print("🗑️  Suppression de toutes les tables...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tables supprimées")

    print("🔨 Création des nouvelles tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables créées avec succès!")
    print("")
    print("Les tables suivantes ont été créées:")
    for table in Base.metadata.sorted_tables:
        print(f"  - {table.name}")

if __name__ == "__main__":
    print("⚠️  ATTENTION: Ce script va supprimer toutes les données de la base!")
    response = input("Voulez-vous continuer? (oui/non): ")

    if response.lower() in ['oui', 'yes', 'y', 'o']:
        recreate_database()
    else:
        print("❌ Opération annulée")
