# Amazon Review Analysis - Pipeline ETL

Pipeline ETL automatisé pour extraire, transformer et charger les données d'avis Amazon depuis PostgreSQL vers S3, Snowflake et MongoDB.

> 🚀 **Nouveau sur le projet ?** Consultez [QUICKSTART.md](QUICKSTART.md) pour démarrer en 5 minutes !

## Démarrage Rapide

### 1️⃣ Démarrage de l'infrastructure Docker

```bash
# 1. Créer le réseau Docker (une seule fois)
docker network create review-analysis-network

# 2. PostgreSQL (contient les données source - initialisation automatique)
docker-compose -f docker-compose.postgres.yml up -d

# 3. MongoDB (stocke les logs et données rejetées)
docker-compose -f docker-compose.mongodb.yml up -d

# 4. Airflow (orchestration du pipeline ETL)
docker-compose -f docker-compose.airflow.yml up -d
```

**⏱️ Temps de démarrage:**
- PostgreSQL: 1-2 minutes (initialisation automatique des données au premier lancement)
- Airflow: 1-2 minutes (initialisation de la base de données Airflow)

### 2️⃣ Configuration des credentials

**Créer le fichier `.env` à la racine:**
```bash
cp .env.example .env
# Éditer .env avec vos credentials AWS et Snowflake
```

**Variables obligatoires dans `.env`:**
```bash
# AWS S3
AWS_ACCESS_KEY_ID=votre_access_key
AWS_SECRET_ACCESS_KEY=votre_secret_key
AWS_S3_BUCKET=votre-bucket
AWS_REGION=eu-west-1

# Snowflake
SNOWFLAKE_USER=votre_user
SNOWFLAKE_PASSWORD=votre_password
SNOWFLAKE_ACCOUNT=votre_account
SNOWFLAKE_DATABASE=AMAZON_REVIEWS
SNOWFLAKE_SCHEMA=ANALYTICS
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_ROLE=ACCOUNTADMIN

# PostgreSQL et MongoDB sont déjà configurés pour Docker
```

### 3️⃣ Configuration Airflow

Les connexions Airflow (PostgreSQL, MongoDB, Snowflake, AWS S3) sont **automatiquement configurées** via les variables d'environnement définies dans le fichier `.env` (format `AIRFLOW_CONN_*`). Aucune configuration manuelle n'est nécessaire.

### 4️⃣ Lancer le pipeline

**Activer les DAGs (une seule fois):**
```bash
docker exec airflow-webserver airflow dags unpause main_orchestrator
docker exec airflow-webserver airflow dags unpause extract_postgres_to_s3
docker exec airflow-webserver airflow dags unpause transform_load_data
```

**Déclencher le pipeline complet:**
```bash
docker exec airflow-webserver airflow dags trigger main_orchestrator
```

**Le pipeline exécutera automatiquement:**
1. ✅ Initialisation MongoDB (collections + indexes)
2. ✅ Initialisation Snowflake (database + schema + tables)
3. ✅ Extraction PostgreSQL → S3 (8 tables, anonymisation buyer_id)
4. ✅ Transformation et chargement → Snowflake + MongoDB

**Monitoring:**
- **Interface Airflow**: http://localhost:8080 (login: admin / password: admin)
- **MongoDB UI**: http://localhost:8081
- **Logs en temps réel**: `docker logs -f airflow-scheduler`

---

## Alternative: Démarrage sans Airflow

### 3. Lancer le pipeline

```bash
cd src_code

# Option A : Pipeline complet (recommandé pour la première fois)
python scripts/pipeline.py --all

# Option B : Étape par étape
python scripts/extract_to_s3.py          # PostgreSQL → S3
python scripts/process_and_store.py      # S3 → Snowflake + MongoDB
```

## Architecture

```
PostgreSQL (Docker)    →    AWS S3    →    Snowflake
   localhost:5433         (Data Lake)    (Data Warehouse)
   130K+ clients
   42K+ produits                              ↓
   111K+ avis                          MongoDB (Docker)
                                       (Logs & Metadata)
```

## Structure du Projet

```
project_2/
├── README.md                              ← Vous êtes ici
├── .env                                   ← Configuration centrale (AWS, Snowflake, etc.)
├── .env.example                           ← Template de configuration
│
├── docker-compose.postgres.yml            ← PostgreSQL (données source)
├── docker-compose.mongodb.yml             ← MongoDB (logs & rejets)
├── docker-compose.airflow.yml             ← Airflow (orchestration)
│
├── data/
│   └── clean/                             ← Données CSV (auto-chargées dans PostgreSQL)
├── docker/postgres/init/                  ← Scripts d'initialisation PostgreSQL
│
└── src_code/
    ├── README.md                          ← Documentation détaillée du pipeline
    ├── scripts/
    │   ├── pipeline.py                    ← Pipeline manuel (sans Airflow)
    │   ├── extract_to_s3.py               ← Extraction PostgreSQL → S3
    │   ├── process_and_store.py           ← Traitement et stockage
    │   └── dags/                          ← DAGs Airflow
    │       ├── main_orchestrator_dag.py   ← DAG principal
    │       ├── extract_to_s3.py           ← DAG extraction
    │       ├── transform_load_data.py     ← DAG transformation
    │       └── utils/                     ← Utilitaires DAGs
    │           ├── mongo_handler.py       ← Gestionnaire MongoDB
    │           └── review_processor.py    ← Processeur de données
    └── config/                            ← Fichiers de configuration
```

## Commandes Utiles

### Gestion des conteneurs

```bash
# Voir les conteneurs en cours
docker ps

# Arrêter tous les services
docker-compose -f docker-compose.airflow.yml down
docker-compose -f docker-compose.mongodb.yml down
docker-compose -f docker-compose.postgres.yml down

# Redémarrer un service spécifique
docker-compose -f docker-compose.airflow.yml restart

# Réinitialiser PostgreSQL (supprime les données)
docker-compose -f docker-compose.postgres.yml down -v
docker-compose -f docker-compose.postgres.yml up -d
```

### Commandes Airflow

```bash
# Lister les DAGs
docker exec airflow-webserver airflow dags list

# Voir l'état d'un DAG
docker exec airflow-webserver airflow dags list-runs -d main_orchestrator

# Activer/Désactiver un DAG
docker exec airflow-webserver airflow dags unpause main_orchestrator
docker exec airflow-webserver airflow dags pause main_orchestrator

# Déclencher un DAG manuellement
docker exec airflow-webserver airflow dags trigger main_orchestrator

# Voir les tâches d'un DAG run
docker exec airflow-webserver airflow tasks states-for-dag-run transform_load_data <run_id>

# Lister les variables Airflow
docker exec airflow-webserver airflow variables list

# Voir les logs
docker logs -f airflow-scheduler
docker logs -f airflow-webserver
```

### Vérifier les connexions

```bash
# PostgreSQL
docker exec -it amazon_postgres_db psql -U admin -d amazon_db -c "SELECT COUNT(*) FROM product;"

# MongoDB
docker exec -it amazon-reviews-mongodb mongosh -u admin -p changeme --eval "db.adminCommand('ping')"

# Airflow (vérifier qu'il est prêt)
docker exec airflow-webserver airflow db check
```

## Données Disponibles

Le projet contient **~1.7M d'enregistrements** sur 25 tables :
- **130,766** clients
- **42,858** produits
- **222,644** commandes
- **111,322** avis clients
- **100,000** acheteurs
- Et plus...

## Tests de Qualité

Le projet inclut une suite complète de tests de qualité des données :

```bash
cd src_code

# Exécuter les tests
python tests/test_data_quality.py

# Générer le rapport HTML
python scripts/generate_quality_report.py
```

**8 tests automatisés** :
- Connexion PostgreSQL
- Validation des ratings (1-5)
- Détection des doublons
- Champs obligatoires non-NULL
- Prix positifs
- Textes non-vides
- Cohérence des types
- Intégrité référentielle

Les rapports sont disponibles dans `src_code/reports/` (JSON + HTML).

## Documentation Détaillée

- **`src_code/README.md`** - Documentation complète du pipeline ETL
- **`CONFORMITE_ETL.md`** - Analyse de conformité du projet
- **`.env.example`** - Template de configuration avec explications

## Technologies

- **Orchestration** : Apache Airflow 2.8.3 (Docker)
- **Source** : PostgreSQL 17 (Docker)
- **Data Lake** : AWS S3
- **Data Warehouse** : Snowflake
- **Logs & Rejets** : MongoDB 7.0 (Docker)
- **ETL** : Python 3.11+ avec pandas, boto3, snowflake-connector
- **Conteneurisation** : Docker & Docker Compose

## Support

- Vérifier que Docker est bien installé et démarré
- Les ports 5433 (PostgreSQL) et 27017 (MongoDB) doivent être disponibles
- Voir `src_code/README.md` pour le troubleshooting détaillé
