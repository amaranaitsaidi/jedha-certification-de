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



### Avec Docker

```bash
# Build l'image
docker build -t review-analysis .
# Exécuter le pipeline complet
docker run --env-file .env review-analysis
# Exécuter une étape spécifique
docker run --env-file .env review-analysis python scripts/extract_to_s3.py
```

## Architecture du Pipeline

```
┌─────────────────┐
│  PostgreSQL     │  
│  (localhost)    │ 
└────────┬────────┘   
         │              
         ↓
    extract_to_s3.py
         │
         ↓
┌─────────────────┐
│    AWS S3       │  
│  (Data Lake)    │  
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
  - product          
  - category         
  - review            
  - product_reviews  
  - review_images     
  - orders            

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
## Logs

Les logs sont automatiquement sauvegardés :
- **MongoDB** : Collection `pipeline_logs`
- **Console** : Output en temps réel avec timestamps


## Tests de Qualité des Données

### Exécution des Tests

```bash
# Exécuter la suite complète de tests
python tests/test_data_quality.py

# Générer le rapport HTML
python scripts/generate_quality_report.py

# Ouvrir le rapport
# Le fichier HTML est dans reports/data_quality_report.html
```

### Tests Disponibles

| # | Test | Description |
|---|------|-------------|
| 1 | Connexion PostgreSQL | Vérifie la connexion à la base de données |
| 2 | Ratings (1-5) | Valide que tous les ratings sont entre 1 et 5 |
| 3 | Pas de doublons | Détecte les review_id en double |
| 4 | Champs obligatoires | Vérifie l'absence de NULL |
| 5 | Prix positifs | S'assure que tous les prix > 0 |
| 6 | Textes non-vides | Contrôle la présence de contenu |
| 7 | Types cohérents | Valide les types de données |
| 8 | Intégrité référentielle | Vérifie les clés étrangères |

**Résultat attendu : 100% de succès (8/8 tests passent)**

### Rapports Générés

- **JSON** : `reports/data_quality_report.json` - Données structurées
- **HTML** : `reports/data_quality_report.html` - Rapport visuel