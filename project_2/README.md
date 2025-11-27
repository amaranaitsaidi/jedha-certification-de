# Amazon Review Analysis - Pipeline ETL

Pipeline ETL automatisé pour extraire, transformer et charger les données d'avis Amazon depuis PostgreSQL vers S3, Snowflake et MongoDB.

> 🚀 **Nouveau sur le projet ?** Consultez [QUICKSTART.md](QUICKSTART.md) pour démarrer en 5 minutes !

## Démarrage Rapide (3 étapes)

### Docker
```bash
# Créer le réseau docker
docker network create review-analysis-network

### 1. Démarrer les bases de données

```bash
# PostgreSQL (contient les données source)
docker-compose -f docker-compose.postgres.yml up -d

# MongoDB (stocke les métadonnées du pipeline)
cd src_code
docker-compose -f docker-compose.mongodb.yml up -d

## 1/ Démarrage avec Airflow

# Container Airflow
docker-compose -f docker-compose.airflow.yml up -d

cd ..
```

**Attendre 1-2 minutes** pour que PostgreSQL initialise les données (première fois uniquement).
**Attendre 1-2 minutes** pour le démarrage d'Airflow.

### 2. Configurer les credentials

```bash
cd src_code
cp .env.example .env
# Éditer .env avec vos credentials AWS et Snowflake
# PostgreSQL et MongoDB sont déjà configurés pour Docker
```
**Configuration Airflow**
**Option 1 : Vous définissez vos connexions dans le docker compose Airflow**
**Option 2 : Vous définissez vos connexions dans la plateforme Airflow**
## information pour l'option 2 ->
Se rendre dans Admin -> Connections -> Add a new record

**aws_default** Pour Amazon S3
Connection Id : aws_default
Connection Type : Amazon Web Services
AWS Access Key ID : add your key ID
AWS Secret Access Key : add your Secret acces key

**postgres_source** Pour Postgresql Source
Connection Id : postgres_source
Connection Type : Postgres
Host : Container_name
Database : your database
Login : your login
password : your password
Port : 5432 (Port interne)

### Démarrage 
Une fois le container Airflow lancé, les DAGs se déclencheront seuls.
- Les logs sont enregistrés dans Mongodb.
- Les rejets sont enregistrés dans Mongodb.
- Les données cleans sont enregistrées dans Snowflake.

## 2/ Démarrage sans Airflow

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
├── docker-compose.postgres.yml            ← Base de données PostgreSQL
├── .env.local                             ← Config PostgreSQL
├── data/
│   └── clean/                             ← Données CSV (utilisées par Docker)
├── docker/postgres/init/                  ← Scripts d'initialisation DB
└── src_code/                              ← Code du pipeline ETL
    ├── README.md                          ← Documentation détaillée du pipeline
    ├── docker-compose.mongodb.yml         ← Base MongoDB
    ├── .env                               ← Configuration du pipeline
    ├── scripts/                           ← Scripts Python du pipeline
    │   ├── pipeline.py                    ← Script principal
    │   ├── extract_to_s3.py               ← Extraction PostgreSQL → S3
    │   └── process_and_store.py           ← Traitement et stockage
    └── config/                            ← Fichiers de configuration
```

## Commandes Utiles

### Gestion des conteneurs

```bash
# Voir les conteneurs en cours
docker ps

# Arrêter tout
docker-compose -f docker-compose.postgres.yml down
cd src_code && docker-compose -f docker-compose.mongodb.yml down

# Réinitialiser PostgreSQL (supprime les données)
docker-compose -f docker-compose.postgres.yml down -v
docker-compose -f docker-compose.postgres.yml up -d
```

### Vérifier les connexions

```bash
# PostgreSQL
docker exec -it amazon_postgres_db psql -U admin -d amazon_db -c "SELECT COUNT(*) FROM product;"

# MongoDB
docker exec -it amazon-reviews-mongodb mongosh -u admin -p changeme --eval "db.adminCommand('ping')"
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

- **Source** : PostgreSQL 17 (Docker)
- **Data Lake** : AWS S3
- **Data Warehouse** : Snowflake
- **Logs** : MongoDB (Docker)
- **ETL** : Python 3.11+

## Support

- Vérifier que Docker est bien installé et démarré
- Les ports 5433 (PostgreSQL) et 27017 (MongoDB) doivent être disponibles
- Voir `src_code/README.md` pour le troubleshooting détaillé
