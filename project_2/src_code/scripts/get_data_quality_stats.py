"""
Get Data Quality Statistics
============================
Analyse les données pour obtenir les statistiques de qualité réelles.
"""

import os
import sys
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def get_quality_stats():
    """Obtenir les statistiques de qualité des données."""

    # Connexion à PostgreSQL
    conn = psycopg2.connect(os.getenv('POSTGRES_CONNECTION_STRING'))

    print("=" * 80)
    print("STATISTIQUES DE QUALITE DES DONNEES")
    print("=" * 80)
    print()

    # 1. Total des reviews
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM review;")
    total_reviews = cursor.fetchone()[0]
    print(f"[Total] Reviews dans la base: {total_reviews:,}")

    # 2. Reviews avec doublons
    cursor.execute("""
        SELECT COUNT(*)
        FROM (
            SELECT review_id, COUNT(*) as cnt
            FROM review
            GROUP BY review_id
            HAVING COUNT(*) > 1
        ) duplicates;
    """)
    duplicates = cursor.fetchone()[0]
    print(f"[Doublons] Reviews avec review_id duplique: {duplicates:,}")

    # 3. Reviews avec rating NULL
    cursor.execute("SELECT COUNT(*) FROM review WHERE rating IS NULL;")
    null_ratings = cursor.fetchone()[0]
    print(f"[NULL] Reviews avec rating NULL: {null_ratings:,}")

    # 4. Reviews avec ratings invalides (< 1 ou > 5)
    cursor.execute("""
        SELECT COUNT(*)
        FROM review
        WHERE rating < 1 OR rating > 5;
    """)
    invalid_ratings = cursor.fetchone()[0]
    print(f"[Invalide] Reviews avec rating invalide (< 1 ou > 5): {invalid_ratings:,}")

    # 5. Reviews avec buyer_id NULL
    cursor.execute("SELECT COUNT(*) FROM review WHERE buyer_id IS NULL;")
    null_buyers = cursor.fetchone()[0]
    print(f"[NULL Buyer] Reviews avec buyer_id NULL: {null_buyers:,}")

    # 6. Reviews avec description vide ou NULL
    cursor.execute("""
        SELECT COUNT(*)
        FROM review
        WHERE r_desc IS NULL OR TRIM(r_desc) = '';
    """)
    empty_descriptions = cursor.fetchone()[0]
    print(f"[Desc vide] Reviews avec description vide/NULL: {empty_descriptions:,}")

    # 7. Distribution des ratings
    print()
    print("Distribution des ratings:")
    cursor.execute("""
        SELECT rating, COUNT(*) as count
        FROM review
        WHERE rating IS NOT NULL
        GROUP BY rating
        ORDER BY rating;
    """)
    for row in cursor.fetchall():
        rating, count = row
        print(f"  Rating {rating}: {count:,}")

    # 8. Calcul du taux de rejet potentiel
    print()
    print("=" * 80)
    print("ANALYSE DE REJET")
    print("=" * 80)

    # Total des problèmes (en comptant les duplicatas aussi)
    cursor.execute("""
        WITH duplicate_reviews AS (
            SELECT review_id
            FROM review
            GROUP BY review_id
            HAVING COUNT(*) > 1
        )
        SELECT COUNT(DISTINCT r.review_id)
        FROM review r
        WHERE r.review_id IN (SELECT review_id FROM duplicate_reviews)
           OR r.rating IS NULL
           OR r.rating < 1
           OR r.rating > 5
           OR r.buyer_id IS NULL
           OR r.r_desc IS NULL
           OR TRIM(r.r_desc) = '';
    """)
    total_problematic = cursor.fetchone()[0]

    clean_reviews = total_reviews - total_problematic
    rejection_rate = (total_problematic / total_reviews * 100) if total_reviews > 0 else 0

    print(f"[OK] Reviews propres: {clean_reviews:,}")
    print(f"[KO] Reviews a rejeter: {total_problematic:,}")
    print(f"[%] Taux de rejet: {rejection_rate:.2f}%")
    print()

    # 9. Détail des motifs de rejet
    print("Detail des motifs de rejet:")
    motifs = {
        'Doublons': duplicates,
        'Rating NULL': null_ratings,
        'Rating invalide': invalid_ratings,
        'Buyer ID NULL': null_buyers,
        'Description vide': empty_descriptions
    }

    for motif, count in motifs.items():
        if count > 0:
            pct = (count / total_reviews * 100) if total_reviews > 0 else 0
            print(f"  - {motif}: {count:,} ({pct:.2f}%)")

    cursor.close()
    conn.close()

    return {
        'total_reviews': total_reviews,
        'clean_reviews': clean_reviews,
        'rejected_reviews': total_problematic,
        'rejection_rate': rejection_rate,
        'duplicates': duplicates,
        'null_ratings': null_ratings,
        'invalid_ratings': invalid_ratings,
        'null_buyers': null_buyers,
        'empty_descriptions': empty_descriptions
    }

if __name__ == '__main__':
    try:
        stats = get_quality_stats()
        print()
        print("=" * 80)
        print("✅ Analyse terminée avec succès")
        print("=" * 80)
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
