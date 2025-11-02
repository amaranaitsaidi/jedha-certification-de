# Amazon Review Analysis - ETL Pipeline

Pipeline ETL automatisé pour l'analyse des avis Amazon : PostgreSQL → S3 → Snowflake + MongoDB

## Configuration

Configurer les credentials dans `.env` (copier depuis `.env.example`) :
- AWS S3 (bucket, access key, secret)
- Snowflake (account, user, password, warehouse)
- MongoDB (connection string)

## Exécution avec Python

```bash
# Démarrer MongoDB
docker-compose up -d

# Pipeline complet (première fois - réinitialise les BDD)
python scripts/pipeline.py --all

# Pipeline étape par étape (runs suivants - préserve les données)
python scripts/extract_to_s3.py              # PostgreSQL → S3
python scripts/process_and_store.py          # S3 → Snowflake + MongoDB

# Vérification
python scripts/verify_snowflake.py
python scripts/verify_mongodb.py
```

## Exécution avec Docker

```bash
# Build l'image
docker build -t review-analysis .

# Première fois (réinitialise MongoDB et Snowflake)
docker run --env-file .env review-analysis

# Runs suivants (préserve les données existantes)
docker run --env-file .env review-analysis python scripts/pipeline.py --step extract
docker run --env-file .env review-analysis python scripts/pipeline.py --step process

# Mode interactif
docker run -it --env-file .env review-analysis /bin/bash
# Puis exécuter les scripts manuellement

# Dry-run (simulation)
docker run --env-file .env review-analysis python scripts/pipeline.py --all --dry-run
```

**⚠️ IMPORTANT** :
- `--all` réinitialise complètement MongoDB et Snowflake (supprime toutes les données)
- `--step extract` et `--step process` préservent les données existantes et ajoutent les nouvelles

## Technologies

Python 3.11 | PostgreSQL (Neon) | AWS S3 | Snowflake | MongoDB | Docker
