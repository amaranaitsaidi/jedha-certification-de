# Pipeline ETL - Documentation Technique

Pipeline d'extraction, transformation et chargement des avis Amazon : **PostgreSQL → S3 → Snowflake + MongoDB**

## Prérequis

1. **Python 3.11+** avec les dépendances installées
2. **Docker** en cours d'exécution
3. **Bases de données démarrées** :
   ```bash
   # Depuis la racine du projet
   docker-compose -f docker-compose.postgres.yml up -d        # PostgreSQL
   docker-compose -f docker-compose.mongodb.yml up -d         # MongoDB (depuis src_code/)
   ```

## Installation

```bash
# Installer les dépendances
pip install -r requirements.txt

# Configurer les credentials
cp .env.example .env
# Éditer .env avec vos credentials AWS et Snowflake
```

## Configuration

### Fichier `.env`

```bash
# PostgreSQL (déjà configuré pour Docker local)
POSTGRES_CONNECTION_STRING=postgresql://admin:admin123@localhost:5433/amazon_db

# AWS S3 (à remplir)
AWS_ACCESS_KEY_ID=votre_access_key
AWS_SECRET_ACCESS_KEY=votre_secret_key
AWS_S3_BUCKET=votre_bucket
AWS_REGION=eu-west-1

# Snowflake (à remplir)
SNOWFLAKE_ACCOUNT=votre_account
SNOWFLAKE_USER=votre_user
SNOWFLAKE_PASSWORD=votre_password
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_DATABASE=AMAZON_REVIEWS
SNOWFLAKE_SCHEMA=ANALYTICS
SNOWFLAKE_ROLE=ACCOUNTADMIN

# MongoDB (déjà configuré pour Docker local)
MONGODB_CONNECTION_STRING=mongodb://admin:changeme@localhost:27017/amazon_reviews?authSource=admin
```

## Utilisation

### Option 1 : Pipeline Complet (Recommandé)

```bash
python scripts/pipeline.py --all
```

**⚠️ Attention** : `--all` réinitialise complètement Snowflake et MongoDB (supprime toutes les données existantes)

### Option 2 : Exécution par Étapes

```bash
# Étape 1 : Extraction PostgreSQL → S3
python scripts/extract_to_s3.py

# Étape 2 : Traitement et Stockage S3 → Snowflake + MongoDB
python scripts/process_and_store.py
```

Cette approche **préserve les données existantes** et ajoute les nouvelles.

### Option 3 : Avec Docker

```bash
# Build l'image
docker build -t review-analysis .

# Exécuter le pipeline complet
docker run --env-file .env review-analysis

# Exécuter une étape spécifique
docker run --env-file .env review-analysis python scripts/extract_to_s3.py

# Mode interactif
docker run -it --env-file .env review-analysis /bin/bash
```

## Scripts Disponibles

| Script | Description | Durée |
|--------|-------------|-------|
| `pipeline.py --all` | Pipeline complet (extract + process) | ~5 min |
| `extract_to_s3.py` | Extraction PostgreSQL → S3 (6 tables) | ~20 sec |
| `process_and_store.py` | Traitement S3 → Snowflake + MongoDB | ~3 min |
| `verify_snowflake.py` | Vérification des données dans Snowflake | ~5 sec |
| `verify_mongodb.py` | Vérification des logs dans MongoDB | ~5 sec |

## Architecture du Pipeline

```
┌─────────────────┐
│  PostgreSQL     │  Tables extraites :
│  (localhost)    │  - product (42K rows)
│  Port: 5433     │  - review (111K rows)
└────────┬────────┘  - category, product_reviews,
         │             review_images, orders
         ↓
    extract_to_s3.py
         │
         ↓
┌─────────────────┐
│    AWS S3       │  Stockage : s3://bucket/raw/{table}/
│  (Data Lake)    │  Format : CSV avec timestamp
└────────┬────────┘
         │
         ↓
  process_and_store.py
         │
         ├──────────────────┐
         ↓                  ↓
┌─────────────────┐  ┌─────────────────┐
│   Snowflake     │  │    MongoDB      │
│ (Data Warehouse)│  │  (Logs & Meta)  │
│                 │  │                 │
│ Table: reviews  │  │ Collection:     │
│ 111K rows       │  │ - pipeline_logs │
│ Données nettoyées│ │ - metadata      │
└─────────────────┘  └─────────────────┘
```

## Configuration Avancée

### Fichier `config/config.yaml`

```yaml
tables:
  - product          # 42,858 rows
  - category         # 2 rows
  - review           # 111,322 rows
  - product_reviews  # 111,322 rows
  - review_images    # 119,382 rows
  - orders           # 222,644 rows

s3:
  raw_prefix: "raw/"

snowflake:
  table_name: "reviews"
  rejected_table: "rejected_reviews"
```

## Vérification

```bash
# Vérifier Snowflake
python scripts/verify_snowflake.py

# Vérifier MongoDB
python scripts/verify_mongodb.py

# Vérifier PostgreSQL
docker exec -it amazon_postgres_db psql -U admin -d amazon_db -c "\dt"
```

## Troubleshooting

### Erreur de connexion PostgreSQL

```bash
# Vérifier que le conteneur est démarré
docker ps | grep postgres

# Vérifier les logs
docker logs amazon_postgres_db

# Redémarrer
docker-compose -f ../docker-compose.postgres.yml restart
```

### Erreur de connexion MongoDB

```bash
# Vérifier que le conteneur est démarré
docker ps | grep mongo

# Tester la connexion
docker exec -it amazon-reviews-mongodb mongosh -u admin -p changeme
```

### Erreur AWS S3

- Vérifier les credentials dans `.env`
- Vérifier les permissions du bucket S3
- Vérifier la région AWS

### Erreur Snowflake

- Vérifier les credentials dans `.env`
- Vérifier que la database et le schema existent
- Vérifier les permissions de l'utilisateur

## Logs

Les logs sont automatiquement sauvegardés :
- **MongoDB** : Collection `pipeline_logs`
- **Console** : Output en temps réel avec timestamps

## Structure des Données

### Table Snowflake `reviews`

Colonnes principales :
- `review_id`, `p_id`, `p_name`, `category_name`
- `buyer_id`, `rating`, `review_title`, `review_text`
- `review_date`, `verified_purchase`, `helpful_count`
- `img_url`, `order_date`, `created_at`

### MongoDB Collections

- `pipeline_logs` : Logs d'exécution du pipeline
- `rejected_records` : Enregistrements rejetés (validation échouée)
- `pipeline_metadata` : Métadonnées (timestamp, nombre de lignes, etc.)

## Performance

- **Extraction** : ~20 secondes pour 607K rows
- **Traitement** : ~40 secondes (jointures + nettoyage)
- **Upload Snowflake** : ~2-3 minutes pour 111K rows
- **Total** : ~5 minutes pour le pipeline complet

## Développement

```bash
# Tests
pytest tests/

# Linter
flake8 scripts/

# Format
black scripts/
```
