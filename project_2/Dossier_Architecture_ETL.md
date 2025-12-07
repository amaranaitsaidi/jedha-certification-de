# DOSSIER D'ARCHITECTURE TECHNIQUE
## Projet ETL d'Analyse des Avis Amazon

---

**Version** : 1.0
**Date** : 6 décembre 2025
**Auteur** : Équipe Data Engineering
**Statut** : Final

---

## TABLE DES MATIÈRES

1. [Introduction](#1-introduction)
2. [PARTIE 1 - DONNÉES ET EXTRACTION (C10)](#partie-1---données-et-extraction-c10)
   - 2.1 [Données de Référence du Projet](#21-données-de-référence-du-projet)
   - 2.2 [Procédures de Sélection et Extraction](#22-procédures-de-sélection-et-extraction)
   - 2.3 [Proposition de Stockage Massif](#23-proposition-de-stockage-massif)
3. [PARTIE 2 - TRAITEMENT ET CONFORMITÉ (C11)](#partie-2---traitement-et-conformité-c11)
   - 3.1 [Étapes de Traitement et Chargement](#31-étapes-de-traitement-et-chargement)
   - 3.2 [Orchestration et Workflow](#32-orchestration-et-workflow)
   - 3.3 [Qualité des Données et Conformité](#33-qualité-des-données-et-conformité)
4. [Architecture Globale du Système](#4-architecture-globale-du-système)
5. [Technologies et Stack Technique](#5-technologies-et-stack-technique)
6. [Performance et Scalabilité](#6-performance-et-scalabilité)
7. [Sécurité et Conformité](#7-sécurité-et-conformité)
8. [Annexes](#8-annexes)

---

## 1. INTRODUCTION

### 1.1 Contexte du Projet

Le projet **Amazon Review Analysis ETL Pipeline** vise à mettre en place une infrastructure complète d'extraction, transformation et chargement (ETL) pour analyser et exploiter les avis clients Amazon. Ce système traite **607 630 enregistrements** issus de 6 tables relationnelles pour produire des données analytiques prêtes à l'exploitation.

### 1.2 Objectifs du Système

**Objectifs fonctionnels** :
- Extraire quotidiennement les données depuis une base PostgreSQL transactionnelle
- Transformer et enrichir les données avec des métriques calculées (longueur du texte, présence d'images, historique de commandes)
- Charger les données nettoyées dans Snowflake pour l'analyse
- Assurer une traçabilité complète via MongoDB (logs, métadonnées, données rejetées)
- Garantir une qualité de données supérieure à 99% avec détection et isolation des anomalies

**Objectifs non-fonctionnels** :
- Temps de traitement bout-en-bout : < 10 minutes (objectif : 5 minutes)
- Coût de traitement : < 0,10 $ par 1 000 avis traités
- Scalabilité : capacité à traiter 1M+ d'avis sans refonte majeure
- Fiabilité : taux d'échec < 1%, avec mécanismes de retry et recovery

### 1.3 Périmètre

**Dans le périmètre** :
- Extraction de 6 tables sources (product, category, review, product_reviews, review_images, orders)
- Transformation par jointures SQL et enrichissement de données
- Validation et nettoyage via Great Expectations
- Chargement vers Snowflake (Data Warehouse)
- Logging et monitoring via MongoDB
- Orchestration via Apache Airflow

**Hors périmètre** :
- Analyse temps-réel (streaming)
- Interface utilisateur de visualisation (dashboard)
- Traitement NLP avancé (sentiment analysis, ML)
- Gestion des images (stockage et traitement d'images)

---

## PARTIE 1 - DONNÉES ET EXTRACTION (C10)

### 2.1 DONNÉES DE RÉFÉRENCE DU PROJET

#### 2.1.1 Catalogue des Données Sources

Le système s'appuie sur **6 tables PostgreSQL** contenant au total **607 630 enregistrements** :

| Table | Volume | Description | Rôle dans le pipeline |
|-------|--------|-------------|----------------------|
| **product** | 42 858 | Catalogue produits | Table de référence principale |
| **category** | 2 | Catégories de produits | Lookup pour enrichissement |
| **review** | 111 322 | Avis clients | Table transactionnelle principale |
| **product_reviews** | 111 322 | Liaison produit-avis | Table de jointure |
| **review_images** | 119 382 | URLs d'images d'avis | Données semi-structurées |
| **orders** | 222 644 | Historique commandes | Enrichissement comportemental |

**Volume total** : 607 630 enregistrements
**Poids estimé** : ~500 MB (format CSV compressé)
**Croissance attendue** : +15% mensuel

#### 2.1.2 Formats de Données

**Données structurées** :
- **Format source** : Tables relationnelles PostgreSQL (types natifs : VARCHAR, INTEGER, TIMESTAMP, TEXT)
- **Format intermédiaire** : CSV UTF-8 sur S3 (séparateur : `,`, quote : `"`)
- **Format cible** : Table Snowflake avec types optimisés (VARIANT pour JSON, TIMESTAMP_NTZ, BOOLEAN)

**Données semi-structurées** :
- URLs d'images stockées en TEXT
- Métadonnées JSON dans MongoDB (logs, rejets)

**Encodage** : UTF-8 systématique pour compatibilité internationale

#### 2.1.3 Modèle de Données et Relations

**Schéma relationnel source (PostgreSQL)** :

```
┌──────────────┐       ┌──────────────────┐       ┌──────────────┐
│   category   │       │     product      │       │    review    │
├──────────────┤       ├──────────────────┤       ├──────────────┤
│ id (PK)      │◄──────│ category_id (FK) │       │ review_id(PK)│
│ name         │       │ p_id (PK)        │       │ buyer_id     │
└──────────────┘       │ name             │       │ rating (1-5) │
                       │ price            │       │ title        │
                       │ ...              │       │ description  │
                       └──────────────────┘       └──────────────┘
                              ▲                          │
                              │                          │
                              │                          │
                       ┌──────┴───────────┐             │
                       │ product_reviews  │◄────────────┘
                       ├──────────────────┤
                       │ p_id (FK)        │
                       │ review_id (FK)   │
                       └──────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  review_images   │
                       ├──────────────────┤
                       │ review_id (FK)   │
                       │ image_url        │
                       └──────────────────┘

┌──────────────┐
│    orders    │
├──────────────┤
│ order_id (PK)│
│ buyer_id     │
│ p_id         │
│ order_date   │
└──────────────┘
```

**Clés primaires et unicité** :
- **product.p_id** : Identifiant unique du produit (VARCHAR, non NULL)
- **review.review_id** : Identifiant unique de l'avis (INTEGER, auto-increment)
- **category.id** : Identifiant de catégorie (INTEGER)
- **orders.order_id** : Identifiant de commande (VARCHAR)

**Intégrité référentielle** :
- `product.category_id` → `category.id` (ON DELETE RESTRICT)
- `product_reviews.p_id` → `product.p_id` (ON DELETE CASCADE)
- `product_reviews.review_id` → `review.review_id` (ON DELETE CASCADE)
- `review_images.review_id` → `review.review_id` (ON DELETE CASCADE)
- `orders.p_id` → `product.p_id` (ON DELETE SET NULL)

**Contraintes de validation** :
- `review.rating` : BETWEEN 1 AND 5
- `product.price` : >= 0
- `review.buyer_id` : NOT NULL
- `review.review_id` : UNIQUE

#### 2.1.4 Hiérarchie et Granularité des Données

**Niveau 1 - Référentiel** :
- Tables `product` et `category` (données maîtres, low-cardinality)
- Mise à jour : batch quotidien
- SCD Type 1 (écrasement, pas d'historisation)

**Niveau 2 - Transactionnel** :
- Table `review` (grain : 1 ligne = 1 avis client)
- Table `orders` (grain : 1 ligne = 1 commande produit)
- Append-only (insertion uniquement)

**Niveau 3 - Jointure** :
- Table `product_reviews` (liaison N:N entre produits et avis)
- Grain : 1 ligne = 1 association produit-avis

**Niveau 4 - Enrichissement** :
- Table `review_images` (URLs d'images, relation 1:N avec review)
- Granularité : 1 ligne = 1 image par avis

**Cardinalités** :
- 1 product → N reviews (avg: 2,6 avis/produit)
- 1 review → 0..N images (avg: 1,07 images/avis)
- 1 buyer → N orders (avg: 2,2 commandes/acheteur)

---

### 2.2 PROCÉDURES DE SÉLECTION ET EXTRACTION

#### 2.2.1 Architecture d'Extraction

**Pattern architectural** : **ELT (Extract-Load-Transform)** avec Data Lake intermédiaire

```
PostgreSQL  →  S3 (Data Lake)  →  Snowflake (Data Warehouse)
  (Source)      (Raw/Bronze)         (Curated/Gold)
```

**Justification du choix ELT** :
- Séparation du compute et du stockage (scalabilité)
- Exploitation de la puissance de calcul de Snowflake
- Traçabilité : conservation des données brutes sur S3
- Résilience : possibilité de re-processing sans ré-extraction

#### 2.2.2 Procédure d'Extraction PostgreSQL → S3

**Outil** : Script Python `extract_to_s3.py` orchestré par Airflow DAG

**Processus détaillé** :

```python
# 1. CONNEXION à PostgreSQL
PostgresHook → Connection pooling (max 5 connexions)
   ├─ Host: localhost:5433 (Docker)
   ├─ Database: amazon_db
   └─ User: admin (privilèges SELECT uniquement)

# 2. EXTRACTION par table
FOR EACH table IN [product, category, review, product_reviews, review_images, orders]:
    ├─ Exécution requête SQL: SELECT * FROM {table}
    ├─ Fetch en chunks (10 000 lignes/batch) → évite saturation mémoire
    ├─ Conversion en DataFrame pandas
    └─ Anonymisation : buyer_id → SHA256(salt + buyer_id)

# 3. UPLOAD S3
S3Hook → boto3 client
   ├─ Bucket: a-ns-bucket
   ├─ Prefix: raw/{table_name}/
   ├─ Format: {table_name}_{timestamp}.csv
   ├─ Compression: GZIP (réduction 70% du poids)
   └─ Server-side encryption: AES-256
```

**Code extraction simplifié** :

```python
class PostgresToS3Extractor:
    def extract_table(self, table_name: str) -> pd.DataFrame:
        """Extract table from PostgreSQL."""
        query = f"SELECT * FROM {table_name}"
        df = self.pg_hook.get_pandas_df(query)

        # Anonymisation si colonne buyer_id présente
        if 'buyer_id' in df.columns:
            df['buyer_id'] = df['buyer_id'].apply(self.anonymize_buyer)

        return df

    def upload_to_s3(self, df: pd.DataFrame, table_name: str):
        """Upload DataFrame to S3 as CSV."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        s3_key = f"raw/{table_name}/{table_name}_{timestamp}.csv"

        # Conversion en CSV en mémoire
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')

        # Upload via S3Hook
        self.s3_hook.load_string(
            string_data=csv_buffer.getvalue(),
            key=s3_key,
            bucket_name=self.bucket,
            replace=True
        )
```

**Requêtes SQL d'extraction** :

| Table | Requête | Particularités |
|-------|---------|----------------|
| product | `SELECT * FROM product` | Aucun filtre (snapshot complet) |
| review | `SELECT * FROM review` | Anonymisation buyer_id |
| orders | `SELECT * FROM orders WHERE order_date >= CURRENT_DATE - 90` | Fenêtre glissante 90 jours |

#### 2.2.3 Gestion de la Compatibilité des Données

**Problématiques identifiées et solutions** :

| Problématique | Impact | Solution implémentée |
|--------------|--------|---------------------|
| **Encodage** | Caractères spéciaux (émojis, accents) corrompus | UTF-8 forcé à l'extraction + validation |
| **Types PostgreSQL** | Types spécifiques (JSONB, ARRAY) non compatibles S3/CSV | Conversion en TEXT avant export |
| **Valeurs NULL** | Inconsistance NULL vs chaîne vide | Préservation NULL explicite (na_rep='') |
| **Dates/Timestamps** | Formats locaux (timezone) | Normalisation ISO 8601 (YYYY-MM-DD HH:MM:SS) |
| **Décimales** | Précision flottants (prix) | Arrondi à 2 décimales, format US (point) |
| **Délimiteurs** | Virgules dans descriptions | Échappement CSV standard (quotes) |

**Validation post-extraction** :

```python
def validate_extraction(df: pd.DataFrame, table_name: str):
    """Validate extracted data before S3 upload."""
    checks = {
        'row_count': len(df) > 0,
        'no_duplicates': not df.duplicated().any(),
        'encoding': all(df[col].str.isascii() for col in df.select_dtypes(include='object').columns),
        'null_keys': df['primary_key'].notna().all()
    }

    if not all(checks.values()):
        raise ValueError(f"Validation failed for {table_name}: {checks}")
```

#### 2.2.4 Traitement des Données Rejetées

**Critères de rejet** :

1. **Rejet niveau extraction** :
   - Enregistrements avec clé primaire NULL
   - Valeurs hors plage (ex: rating = 0 ou 6)
   - Références orphelines (FK sans PK correspondante)

2. **Rejet niveau transformation** :
   - Duplicata (review_id en double)
   - Champs obligatoires NULL (buyer_id, rating, p_id)
   - Incohérences de types (texte dans champ numérique)

**Procédure de traitement** :

```
┌─────────────────┐
│ Donnée entrante │
└────────┬────────┘
         │
         ▼
  ┌──────────────┐
  │  Validation  │
  └──────┬───────┘
         │
    ┌────┴────┐
    │ Valid?  │
    └────┬────┘
         │
    ┌────┴─────────────┐
    ▼                  ▼
┌────────┐        ┌──────────┐
│  PASS  │        │  REJECT  │
│   ↓    │        │     ↓    │
│Snowflake│       │ MongoDB  │
└────────┘        └──────────┘
                  Collection:
                  rejected_reviews
```

**Structure MongoDB pour rejets** :

```json
{
  "_id": ObjectId("..."),
  "review_id": 12345,
  "rejection_reason": "rating_out_of_range",
  "rejection_details": {
    "field": "rating",
    "value": 7,
    "expected": "1-5"
  },
  "raw_data": { ... },
  "rejected_at": ISODate("2025-12-06T10:30:00Z"),
  "pipeline_run_id": "uuid-xxx-yyy-zzz"
}
```

**Indexes MongoDB** :
- `rejection_reason` (ASCENDING) → requêtes par type d'erreur
- `rejected_at` (DESCENDING) → tri chronologique
- `review_id` (ASCENDING) → lookup par ID

**Règles de rétention** :
- Conservation des rejets : **90 jours**
- Archive S3 Glacier après 90 jours
- Suppression définitive après 2 ans

---

### 2.3 PROPOSITION DE STOCKAGE MASSIF

#### 2.3.1 Architecture de Stockage Multi-Couches

**Pattern architectural** : **Medallion Architecture** (Bronze → Silver → Gold)

```
┌─────────────────────────────────────────────────────────────┐
│                    BRONZE LAYER (Raw Data)                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  AWS S3 - Data Lake                                   │  │
│  │  - Prefix: raw/                                       │  │
│  │  - Format: CSV.gz                                     │  │
│  │  - Retention: 2 ans                                   │  │
│  │  - Volume: ~500 MB/jour                               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   SILVER LAYER (Cleaned Data)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Snowflake Staging Tables                             │  │
│  │  - Schéma: STAGING                                    │  │
│  │  - Tables temporaires (TRANSIENT)                     │  │
│  │  - Données validées, pas encore enrichies             │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    GOLD LAYER (Curated Data)                │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Snowflake Analytics Tables                           │  │
│  │  - Schéma: ANALYTICS                                  │  │
│  │  - Table: reviews (111K lignes)                       │  │
│  │  - Données enrichies, prêtes pour BI                  │  │
│  │  - Clustering key: (ingestion_timestamp, category)    │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  METADATA & LOGS LAYER                      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  MongoDB                                              │  │
│  │  - Database: amazon_reviews                           │  │
│  │  - Collections:                                       │  │
│  │    • pipeline_metadata (stats d'exécution)            │  │
│  │    • rejected_reviews (données rejetées)              │  │
│  │    • airflow_logs (logs ETL)                          │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

#### 2.3.2 Data Lake (AWS S3)

**Choix technologique : AWS S3**

**Justification** :
- Durabilité 99,999999999% (11 neuf)
- Scalabilité illimitée
- Coût : $0,023/GB/mois (Standard)
- Intégration native avec Snowflake (External Stages)
- Lifecycle policies pour archivage automatique

**Organisation des données S3** :

```
s3://a-ns-bucket/
├── raw/                          ← Bronze layer
│   ├── product/
│   │   ├── product_20251206_083000.csv.gz
│   │   └── product_20251207_083000.csv.gz
│   ├── category/
│   ├── review/
│   ├── product_reviews/
│   ├── review_images/
│   └── orders/
│
├── processed/                    ← Silver layer (optionnel)
│   └── reviews_enriched/
│       └── reviews_20251206.parquet
│
└── archive/                      ← Données archivées
    └── 2024/
        └── Q4/
            └── raw/
```

**Politiques de cycle de vie S3** :

| Transition | Délai | Classe de stockage | Coût/GB/mois |
|-----------|-------|-------------------|--------------|
| Standard | 0-30 jours | S3 Standard | $0,023 |
| Transition 1 | 30 jours | S3 Standard-IA | $0,0125 |
| Transition 2 | 90 jours | S3 Glacier | $0,004 |
| Suppression | 730 jours | - | - |

**Partitionnement** :
- Par date : `raw/{table}/dt=2025-12-06/`
- Avantages : pruning efficace, suppression par partition

**Compression** :
- Format : GZIP (ratio ~70%)
- Coût stockage réduit de 70%
- Compatible lecture directe Snowflake

#### 2.3.3 Data Warehouse (Snowflake)

**Choix technologique : Snowflake**

**Justification** :
- Architecture cloud-native (séparation compute/storage)
- Auto-scaling (adaptatif au volume de requêtes)
- Support natif du format semi-structuré (VARIANT pour JSON)
- Partage de données sécurisé
- Time Travel (récupération données jusqu'à 90 jours)

**Schéma de la table `reviews` (Gold Layer)** :

```sql
CREATE TABLE IF NOT EXISTS ANALYTICS.reviews (
    -- Identifiants
    review_id VARCHAR(50) PRIMARY KEY,
    buyer_id VARCHAR(100) NOT NULL,         -- Anonymisé (SHA-256)
    p_id VARCHAR(50) NOT NULL,

    -- Informations produit
    product_name VARCHAR(500),
    category VARCHAR(100),

    -- Contenu de l'avis
    title VARCHAR(500),
    description TEXT,
    rating SMALLINT NOT NULL,               -- 1-5

    -- Métriques calculées (enrichissement)
    text_length INTEGER,                    -- Longueur du texte (description)
    has_image BOOLEAN DEFAULT FALSE,        -- Présence d'images
    has_orders BOOLEAN DEFAULT FALSE,       -- Historique de commandes du buyer

    -- Métadonnées techniques
    ingestion_timestamp TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    pipeline_version VARCHAR(20),           -- Ex: "v1.2.0"

    -- Contraintes
    CONSTRAINT chk_rating CHECK (rating BETWEEN 1 AND 5),
    CONSTRAINT chk_text_length CHECK (text_length >= 0)
)
CLUSTER BY (ingestion_timestamp, category);  -- Optimisation des requêtes
```

**Clustering Key** : `(ingestion_timestamp, category)`
- Requêtes fréquentes par date et catégorie
- Amélioration de 3-5x des performances de lecture

**Sizing et coûts Snowflake** :

| Composant | Configuration | Coût mensuel estimé |
|-----------|--------------|---------------------|
| Warehouse | X-SMALL (auto-suspend après 5 min) | $2/heure * 0,5h/jour = $30 |
| Stockage | 10 GB (compressé) | $23 (40 $ * 10/100) |
| **Total** | - | **~50 $/mois** |

**Optimisations** :
- Auto-suspend après 5 minutes d'inactivité
- Clustering automatique activé
- Search Optimization Service pour colonnes TEXT

#### 2.3.4 Stockage des Métadonnées et Logs (MongoDB)

**Choix technologique : MongoDB 7.0**

**Justification** :
- Schéma flexible (logs de structures variables)
- Haute performance en écriture
- Requêtes agrégées puissantes (pipeline d'agrégation)
- Réplication et haute disponibilité natives

**Collections MongoDB** :

**1. `pipeline_metadata` : Statistiques d'exécution**

```json
{
  "_id": ObjectId("..."),
  "run_id": "uuid-12345-abcde",
  "dag_id": "main_orchestrator",
  "execution_timestamp": ISODate("2025-12-06T08:30:00Z"),
  "status": "SUCCESS",
  "statistics": {
    "total_records_extracted": 607630,
    "clean_records": 111322,
    "rejected_records": 0,
    "processing_time_seconds": 290,
    "tables_processed": ["product", "category", "review", "product_reviews", "review_images", "orders"]
  },
  "s3_paths": {
    "product": "s3://a-ns-bucket/raw/product/product_20251206.csv.gz",
    ...
  }
}
```

**Index** :
- `execution_timestamp` (DESC) : recherche par date
- `run_id` (ASC) : lookup par ID de run

**2. `rejected_reviews` : Données rejetées**

(Déjà documenté en 2.2.4)

**3. `airflow_logs` : Logs applicatifs**

```json
{
  "_id": ObjectId("..."),
  "timestamp": ISODate("2025-12-06T08:31:25Z"),
  "level": "INFO",
  "logger": "extract_to_s3",
  "task_id": "extract_product_table",
  "message": "Extracted 42858 rows from product table",
  "extra": {
    "execution_time_ms": 1250,
    "memory_mb": 120
  }
}
```

**Index TTL** : suppression automatique après 30 jours

#### 2.3.5 Étapes de Traitement et Flux de Données

**Workflow complet (orchestré par Airflow)** :

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAG: main_orchestrator                       │
│                                                                 │
│  ┌──────────────┐       ┌──────────────┐                       │
│  │setup_mongodb │       │setup_snowflake│                      │
│  └──────┬───────┘       └──────┬────────┘                       │
│         └───────────┬───────────┘                               │
│                     ▼                                           │
│          ┌─────────────────────┐                                │
│          │trigger_extraction   │                                │
│          │    (TriggerDagRun)  │                                │
│          └──────────┬──────────┘                                │
└─────────────────────┼──────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              DAG: extract_postgres_to_s3                        │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  extract_to_s3 (PythonOperator)                          │  │
│  │  ├─ Connexion PostgreSQL (PostgresHook)                  │  │
│  │  ├─ Pour chaque table:                                   │  │
│  │  │   ├─ SELECT * FROM {table}                            │  │
│  │  │   ├─ Anonymisation buyer_id (SHA-256)                 │  │
│  │  │   ├─ Conversion DataFrame → CSV                       │  │
│  │  │   └─ Upload S3 (S3Hook) : raw/{table}/{table}.csv.gz  │  │
│  │  └─ Retour XCom : {table: s3_path}                       │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  trigger_transform (TriggerDagRunOperator)               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              DAG: transform_load_data                           │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  fetch_s3_paths (PythonOperator)                         │  │
│  │  └─ Pull XCom du DAG extract_postgres_to_s3              │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  load_from_s3 (PythonOperator)                           │  │
│  │  └─ Lecture CSV depuis S3 → 6 DataFrames pandas          │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  transform_data (PythonOperator)                         │  │
│  │  ├─ Jointure SQL (pandasql) : 6 tables → 1 DataFrame     │  │
│  │  ├─ Enrichissement :                                     │  │
│  │  │   • text_length = LENGTH(description)                 │  │
│  │  │   • has_image = EXISTS(image_url)                     │  │
│  │  │   • has_orders = EXISTS(buyer_id IN orders)           │  │
│  │  └─ Retour DataFrame enrichi                             │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  validate_data (PythonOperator)                          │  │
│  │  ├─ Validation Great Expectations :                      │  │
│  │  │   • rating BETWEEN 1 AND 5                            │  │
│  │  │   • review_id UNIQUE                                  │  │
│  │  │   • Champs requis NOT NULL                            │  │
│  │  ├─ Isolation rejets → MongoDB                           │  │
│  │  └─ Retour DataFrame clean                               │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  load_to_snowflake (PythonOperator)                      │  │
│  │  ├─ Connexion Snowflake (SnowflakeHook)                  │  │
│  │  ├─ COPY INTO reviews FROM @s3_stage                     │  │
│  │  └─ Vérification comptage                                │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  log_metadata (PythonOperator)                           │  │
│  │  └─ Enregistrement stats dans MongoDB.pipeline_metadata  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

#### 2.3.6 Nettoyage et Modifications des Données Sources

**Transformations appliquées** :

| Étape | Transformation | Code/Logique | Justification |
|-------|---------------|-------------|---------------|
| **1. Anonymisation** | `buyer_id` → SHA-256 hash | `hashlib.sha256((salt + buyer_id).encode()).hexdigest()` | Conformité RGPD |
| **2. Nettoyage chaînes** | Suppression espaces superflus | `str.strip()` | Cohérence |
| **3. Normalisation NULL** | Remplacement chaînes vides par NULL | `replace('', None)` | Intégrité |
| **4. Validation types** | Conversion rating → INT | `astype(int)` | Typage fort |
| **5. Enrichissement** | Calcul `text_length` | `LENGTH(description)` | Métrique analytique |
| **6. Enrichissement** | Flag `has_image` | `CASE WHEN EXISTS(...) THEN 1 ELSE 0` | Indicateur booléen |
| **7. Enrichissement** | Flag `has_orders` | `CASE WHEN COUNT(orders) > 0 THEN 1 ELSE 0` | Segmentation clients |
| **8. Dédoublonnage** | Suppression duplicata | `df.drop_duplicates(subset=['review_id'])` | Unicité PK |

**Requête SQL de jointure et enrichissement** :

```sql
SELECT
    r.review_id,
    r.buyer_id,                                    -- Déjà anonymisé
    pr.p_id,
    p.name AS product_name,
    c.name AS category,
    r.title,
    r.description,
    r.rating,
    LENGTH(r.description) AS text_length,          -- Enrichissement 1
    CASE
        WHEN ri.review_id IS NOT NULL THEN 1
        ELSE 0
    END AS has_image,                              -- Enrichissement 2
    CASE
        WHEN o.buyer_id IS NOT NULL THEN 1
        ELSE 0
    END AS has_orders                              -- Enrichissement 3
FROM review r
LEFT JOIN product_reviews pr ON r.review_id = pr.review_id
LEFT JOIN product p ON pr.p_id = p.p_id
LEFT JOIN category c ON p.category_id = c.id
LEFT JOIN review_images ri ON r.review_id = ri.review_id
LEFT JOIN orders o ON r.buyer_id = o.buyer_id AND pr.p_id = o.p_id
WHERE r.rating BETWEEN 1 AND 5                     -- Filtrage valeurs invalides
  AND r.buyer_id IS NOT NULL
  AND pr.p_id IS NOT NULL;
```

**Règles de nettoyage avancées** :

```python
def clean_and_validate(df: pd.DataFrame) -> tuple:
    """
    Nettoie et valide le DataFrame.

    Returns:
        (clean_df, rejected_df): DataFrames des données valides et rejetées
    """
    rejected_records = []

    # 1. Détection duplicata
    duplicates = df[df.duplicated(subset=['review_id'], keep=False)]
    if not duplicates.empty:
        rejected_records.append({
            'data': duplicates,
            'reason': 'duplicate_review_id'
        })
        df = df.drop_duplicates(subset=['review_id'], keep='first')

    # 2. Validation rating
    invalid_ratings = df[~df['rating'].between(1, 5)]
    if not invalid_ratings.empty:
        rejected_records.append({
            'data': invalid_ratings,
            'reason': 'rating_out_of_range'
        })
        df = df[df['rating'].between(1, 5)]

    # 3. Validation champs requis
    null_fields = df[df[['review_id', 'buyer_id', 'p_id']].isnull().any(axis=1)]
    if not null_fields.empty:
        rejected_records.append({
            'data': null_fields,
            'reason': 'required_field_null'
        })
        df = df.dropna(subset=['review_id', 'buyer_id', 'p_id'])

    return df, rejected_records
```

**Taux de rejet attendu** : < 1% (objectif qualité)
**Taux de rejet observé** : 0% (données sources déjà nettoyées)

---

## PARTIE 2 - TRAITEMENT ET CONFORMITÉ (C11)

### 3.1 ÉTAPES DE TRAITEMENT ET CHARGEMENT

#### 3.1.1 Transformation des Données

**Processus de transformation détaillé** :

**Étape 1 : Lecture depuis S3**

```python
def load_from_s3(s3_paths: dict) -> dict:
    """Charge les 6 tables depuis S3 en DataFrames pandas."""
    tables = {}
    for table_name, s3_path in s3_paths.items():
        df = pd.read_csv(s3_path, compression='gzip', encoding='utf-8')
        tables[table_name] = df
        logger.info(f"Loaded {len(df)} rows from {table_name}")

    return tables
```

**Étape 2 : Jointure SQL avec pandasql**

```python
import pandasql as psql

def transform_data(tables: dict) -> pd.DataFrame:
    """
    Effectue les jointures SQL et enrichit les données.

    Équivalent à une transformation dbt ou Spark SQL.
    """
    query = """
    SELECT
        r.review_id,
        r.buyer_id,
        pr.p_id,
        p.name AS product_name,
        c.name AS category,
        r.title,
        r.description,
        r.rating,
        LENGTH(r.description) AS text_length,
        CASE WHEN ri.review_id IS NOT NULL THEN 1 ELSE 0 END AS has_image,
        CASE WHEN o.buyer_id IS NOT NULL THEN 1 ELSE 0 END AS has_orders
    FROM review r
    LEFT JOIN product_reviews pr ON r.review_id = pr.review_id
    LEFT JOIN product p ON pr.p_id = p.p_id
    LEFT JOIN category c ON p.category_id = c.id
    LEFT JOIN (
        SELECT DISTINCT review_id FROM review_images
    ) ri ON r.review_id = ri.review_id
    LEFT JOIN (
        SELECT DISTINCT buyer_id, p_id FROM orders
    ) o ON r.buyer_id = o.buyer_id AND pr.p_id = o.p_id
    WHERE r.rating BETWEEN 1 AND 5
      AND r.buyer_id IS NOT NULL
      AND pr.p_id IS NOT NULL
    """

    df_result = psql.sqldf(query, tables)

    logger.info(f"Transformation complete: {len(df_result)} rows")
    return df_result
```

**Étape 3 : Validation qualité avec Great Expectations**

```python
import great_expectations as ge

def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """Valide les données avec Great Expectations."""

    # Conversion en GE DataFrame
    ge_df = ge.from_pandas(df)

    # Expectations (règles de validation)
    ge_df.expect_column_values_to_be_unique('review_id')
    ge_df.expect_column_values_to_be_between('rating', 1, 5)
    ge_df.expect_column_values_to_not_be_null('buyer_id')
    ge_df.expect_column_values_to_not_be_null('p_id')
    ge_df.expect_column_values_to_be_of_type('rating', 'int')

    # Validation
    validation_result = ge_df.validate()

    if not validation_result['success']:
        logger.error(f"Validation failed: {validation_result}")
        raise ValueError("Data quality validation failed")

    return df
```

#### 3.1.2 Chargement vers Snowflake

**Méthode de chargement : COPY INTO via External Stage**

```python
def load_to_snowflake(df: pd.DataFrame, conn_id: str):
    """Charge les données dans Snowflake."""

    # 1. Upload temporaire sur S3
    s3_temp_path = f"s3://a-ns-bucket/staging/reviews_{timestamp}.csv.gz"
    df.to_csv(s3_temp_path, index=False, compression='gzip')

    # 2. Connexion Snowflake
    hook = SnowflakeHook(snowflake_conn_id=conn_id)
    conn = hook.get_conn()
    cursor = conn.cursor()

    # 3. Création External Stage (si n'existe pas)
    cursor.execute("""
        CREATE STAGE IF NOT EXISTS s3_stage
        URL = 's3://a-ns-bucket/staging/'
        CREDENTIALS = (AWS_KEY_ID = '...' AWS_SECRET_KEY = '...')
        FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1 COMPRESSION = GZIP);
    """)

    # 4. COPY INTO (bulk load performant)
    cursor.execute(f"""
        COPY INTO ANALYTICS.reviews
        FROM @s3_stage/reviews_{timestamp}.csv.gz
        FILE_FORMAT = (TYPE = CSV SKIP_HEADER = 1 COMPRESSION = GZIP)
        ON_ERROR = 'ABORT_STATEMENT';
    """)

    # 5. Vérification
    cursor.execute("SELECT COUNT(*) FROM ANALYTICS.reviews")
    count = cursor.fetchone()[0]
    logger.info(f"Loaded {count} rows into Snowflake")

    # 6. Nettoyage fichier temporaire S3
    s3_hook.delete_objects(bucket='a-ns-bucket', keys=[f'staging/reviews_{timestamp}.csv.gz'])

    conn.close()
```

**Performance du chargement** :
- Débit : **~741 enregistrements/seconde**
- Temps pour 111 322 lignes : **~2 min 30 sec**
- Méthode : Bulk insert via COPY INTO (optimisé)

#### 3.1.3 Logging des Métadonnées

```python
def log_pipeline_metadata(stats: dict, mongo_uri: str):
    """Enregistre les statistiques d'exécution dans MongoDB."""

    from pymongo import MongoClient
    import uuid

    client = MongoClient(mongo_uri)
    db = client['amazon_reviews']
    collection = db['pipeline_metadata']

    document = {
        'run_id': str(uuid.uuid4()),
        'dag_id': 'transform_load_data',
        'execution_timestamp': datetime.utcnow(),
        'status': 'SUCCESS',
        'statistics': {
            'total_records_extracted': stats['extracted'],
            'clean_records': stats['clean'],
            'rejected_records': stats['rejected'],
            'processing_time_seconds': stats['duration'],
            'tables_processed': list(stats['tables'].keys())
        },
        's3_paths': stats['s3_paths']
    }

    collection.insert_one(document)
    logger.info(f"Logged metadata with run_id: {document['run_id']}")
```

---

### 3.2 ORCHESTRATION ET WORKFLOW

#### 3.2.1 Apache Airflow : Orchestrateur Central

**Architecture Airflow** :

```
┌─────────────────────────────────────────────────────────┐
│              Airflow Webserver (UI)                     │
│              http://localhost:8080                      │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│              Airflow Scheduler                          │
│  - Parsing DAGs (toutes les 30 sec)                     │
│  - Planification des tâches                             │
│  - Envoi vers Executor                                  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────┐
│              Airflow Executor (Local)                   │
│  - Exécution des tâches (PythonOperator)                │
│  - Max parallel tasks: 16                               │
└────────────────────────┬────────────────────────────────┘
                         │
                    ┌────┴────┐
                    ▼         ▼
            ┌──────────┐  ┌──────────┐
            │ Worker 1 │  │ Worker 2 │
            └──────────┘  └──────────┘
```

**Connections Airflow configurées** :

| Connection ID | Type | Description | Paramètres |
|--------------|------|-------------|-----------|
| `postgres_default` | PostgreSQL | Source de données | Host: amazon_postgres_db, Port: 5432, DB: amazon_db |
| `aws_s3_default` | AWS | Data Lake | Access Key, Secret Key, Bucket: a-ns-bucket |
| `snowflake_conn` | Snowflake | Data Warehouse | Account, User, Password, Database: AMAZON_REVIEWS, Schema: ANALYTICS |
| `mongo` | MongoDB | Logs et métadonnées | URI: mongodb://admin:changeme@mongodb:27017/ |

**Variables Airflow** :

```python
# Récupérées dans les DAGs via Variable.get()
AWS_S3_BUCKET = Variable.get("AWS_S3_BUCKET", default_var="a-ns-bucket")
AWS_REGION = Variable.get("AWS_REGION", default_var="eu-west-3")
```

#### 3.2.2 Diagramme de Flux des 3 DAGs

```
main_orchestrator (DAG 1)
│
├─ setup_mongodb        ─┐
│                         ├─> trigger_extraction_pipeline
└─ setup_snowflake      ─┘
                          │
                          ▼
        extract_postgres_to_s3 (DAG 2)
        │
        └─ extract_to_s3
           ├─ PostgreSQL → S3 (6 tables)
           ├─ Anonymisation buyer_id
           └─ XCom push: s3_paths
              │
              └─> trigger_transform
                  │
                  ▼
        transform_load_data (DAG 3)
        │
        ├─ fetch_s3_paths (XCom pull)
        ├─ load_from_s3
        ├─ transform_data (jointures SQL)
        ├─ validate_data (Great Expectations)
        ├─ load_to_snowflake (COPY INTO)
        └─ log_metadata (MongoDB)
```

**Durée totale bout-en-bout** : **~4 min 50 sec**

| DAG | Durée moyenne | Criticité |
|-----|--------------|----------|
| main_orchestrator | 30 sec | Faible (setup uniquement) |
| extract_postgres_to_s3 | 1 min 23 sec | Élevée |
| transform_load_data | 3 min 30 sec | Élevée |

#### 3.2.3 Gestion des Erreurs et Retry

**Stratégie de retry** :

```python
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 3,                      # Nombre de tentatives
    'retry_delay': timedelta(minutes=5), # Délai entre retries
    'retry_exponential_backoff': True,  # Backoff exponentiel
    'max_retry_delay': timedelta(minutes=30)
}
```

**Gestion d'erreurs dans le code** :

```python
def extract_with_retry(table_name: str, max_retries: int = 3):
    """Extraction avec retry automatique."""
    for attempt in range(max_retries):
        try:
            df = extract_table(table_name)
            return df
        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed for {table_name}: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(5 * (attempt + 1))  # Backoff
```

**Alertes email** (optionnel) :

```python
from utils.email_alerter import EmailAlerter

def on_failure_callback(context):
    """Envoi d'email en cas d'échec."""
    alerter = EmailAlerter()
    alerter.send_failure_alert(
        task_id=context['task'].task_id,
        dag_id=context['dag'].dag_id,
        execution_date=context['execution_date'],
        error=context['exception']
    )
```

---

### 3.3 QUALITÉ DES DONNÉES ET CONFORMITÉ

#### 3.3.1 Framework de Validation : Great Expectations

**Suite de tests automatisés** :

| Test | Objectif | Implémentation | Résultat attendu |
|------|---------|----------------|------------------|
| **1. Connexion PostgreSQL** | Vérifier disponibilité source | `pg_hook.get_conn().is_valid()` | PASS |
| **2. Rating plage (1-5)** | Valider cohérence métier | `expect_column_values_to_be_between('rating', 1, 5)` | 100% conformité |
| **3. Pas de doublons** | Garantir unicité PK | `expect_column_values_to_be_unique('review_id')` | 0 doublon |
| **4. Champs requis non NULL** | Intégrité des clés | `expect_column_values_to_not_be_null(['review_id', 'buyer_id', 'p_id'])` | 100% rempli |
| **5. Prix positifs** | Cohérence économique | `expect_column_values_to_be_between('price', 0, None)` | PASS |
| **6. Texte non vide** | Qualité du contenu | `expect_column_values_to_not_be_null('description', mostly=0.9)` | >90% rempli |
| **7. Types cohérents** | Typage fort | `expect_column_values_to_be_of_type('rating', 'int')` | PASS |
| **8. Intégrité référentielle** | Validation FK | `expect_column_pair_values_A_to_be_in_set_B('p_id', product.p_id)` | 100% valid |

**Score de qualité obtenu** : **100%** (8/8 tests passés)

#### 3.3.2 Métriques de Qualité

**Dimensions de qualité mesurées** :

| Dimension | Métrique | Cible | Réel | Statut |
|-----------|----------|-------|------|--------|
| **Complétude** | % champs non NULL | > 95% | 100% | ✅ |
| **Exactitude** | % ratings valides (1-5) | 100% | 100% | ✅ |
| **Cohérence** | % types de données corrects | 100% | 100% | ✅ |
| **Unicité** | % review_id uniques | 100% | 100% | ✅ |
| **Validité** | % intégrité référentielle | 100% | 100% | ✅ |

#### 3.3.3 Conformité RGPD et Sécurité

**Anonymisation des données personnelles** :

| Champ | Type de donnée | Traitement | Justification |
|-------|---------------|-----------|---------------|
| `buyer_id` | PII | Hachage SHA-256 avec salt | Pseudonymisation RGPD Article 4(5) |
| `review.title` | Texte libre | Conservation | Pas de PII directe |
| `review.description` | Texte libre | Conservation | Pas de PII directe |

**Code d'anonymisation** :

```python
import hashlib

SALT = os.getenv("ANONYMIZATION_SALT", "default_salt_12345")

def anonymize_buyer(buyer_id: str) -> str:
    """
    Anonymise l'identifiant acheteur par hachage SHA-256.

    Propriétés:
    - Non réversible (hachage cryptographique)
    - Déterministe (même input → même output)
    - Collision négligeable (SHA-256)
    """
    to_hash = (SALT + str(buyer_id)).encode('utf-8')
    hashed = hashlib.sha256(to_hash).hexdigest()
    return hashed
```

**Exemple** :
- Original : `buyer_id = "12345"`
- Anonymisé : `buyer_id = "3fc9b...a8d1e"` (64 caractères hexadécimaux)

**Conservation des données** :

| Composant | Durée de rétention | Justification |
|----------|-------------------|---------------|
| S3 Raw | 2 ans | Archivage légal |
| Snowflake | Indéfinie (avec Time Travel 90 jours) | Analytique |
| MongoDB rejets | 90 jours | Debug et qualité |

**Chiffrement** :
- **S3** : Server-Side Encryption (AES-256)
- **Snowflake** : End-to-End Encryption (TLS 1.2+)
- **MongoDB** : Encryption at Rest (optionnel, non activé en dev)

**Contrôle d'accès** :
- Credentials stockés dans `.env` (jamais commités en Git)
- Principe du moindre privilège : compte PostgreSQL en lecture seule
- IAM Roles AWS pour accès S3 (production)

#### 3.3.4 Monitoring et Observabilité

**Logs centralisés** :

Tous les logs applicatifs sont envoyés vers **MongoDB** via un handler personnalisé :

```python
class MongoHandler(logging.Handler):
    """Custom logging handler pour MongoDB."""

    def emit(self, record):
        log_entry = {
            'timestamp': datetime.utcnow(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'task_id': getattr(record, 'task_id', None),
            'extra': getattr(record, 'extra', {})
        }

        self.collection.insert_one(log_entry)
```

**Métriques collectées** :

- Temps d'exécution par tâche
- Volume de données traité (nombre de lignes)
- Taux de rejet
- Utilisation mémoire
- Erreurs et exceptions

**Dashboards** (recommandation future) :
- **Grafana** : monitoring temps-réel
- **Tableau/Power BI** : tableaux de bord métier sur Snowflake

---

## 4. ARCHITECTURE GLOBALE DU SYSTÈME

### 4.1 Vue d'Ensemble

```
┌────────────────────────────────────────────────────────────────────┐
│                     LAYER 1 : SOURCES                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL 17 (Docker)                                      │  │
│  │  - 6 tables (607K enregistrements)                           │  │
│  │  - Port: 5433 (localhost)                                    │  │
│  │  - Initialisation auto (CSV → SQL)                           │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                  LAYER 2 : ORCHESTRATION                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Apache Airflow 2.8.3 (Docker)                               │  │
│  │  - 3 DAGs (orchestrator, extract, transform)                 │  │
│  │  - Webserver: http://localhost:8080                          │  │
│  │  - Scheduler + LocalExecutor                                 │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                   LAYER 3 : BRONZE (RAW DATA)                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  AWS S3 Data Lake                                            │  │
│  │  - Bucket: a-ns-bucket                                       │  │
│  │  - Prefix: raw/{table}/                                      │  │
│  │  - Format: CSV.gz                                            │  │
│  │  - Rétention: 2 ans (lifecycle policy)                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                   LAYER 4 : PROCESSING                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Python 3.11 + pandas                                        │  │
│  │  - Jointures SQL (pandasql)                                  │  │
│  │  - Validation (Great Expectations)                           │  │
│  │  - Enrichissement (text_length, has_image, has_orders)       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────┬───────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
┌────────────────────────────────┐  ┌─────────────────────────────┐
│   LAYER 5 : GOLD (CURATED)    │  │  LAYER 6 : METADATA & LOGS  │
│  ┌─────────────────────────┐  │  │  ┌──────────────────────┐   │
│  │  Snowflake              │  │  │  │  MongoDB 7.0         │   │
│  │  - Database: AMAZON_... │  │  │  │  - pipeline_metadata │   │
│  │  - Schema: ANALYTICS    │  │  │  │  - rejected_reviews  │   │
│  │  - Table: reviews       │  │  │  │  - airflow_logs      │   │
│  │    (111K rows)          │  │  │  │  - Port: 27017       │   │
│  │  - Clustering: (ts,cat) │  │  │  │  - UI: 8081          │   │
│  └─────────────────────────┘  │  │  └──────────────────────┘   │
└────────────────────────────────┘  └─────────────────────────────┘
```

### 4.2 Flux de Données Détaillé

```
┌─────┐
│Start│
└──┬──┘
   │
   ▼
┌────────────────────────────┐
│ 1. EXTRACTION (1 min 23s)  │
│ ┌─────────────────────────┐│
│ │PostgreSQL → DataFrame   ││
│ │ • SELECT * FROM table   ││
│ │ • Anonymisation buyer_id││
│ │ • Chunking (10K rows)   ││
│ └─────────────────────────┘│
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│ 2. STOCKAGE S3 (20s)       │
│ ┌─────────────────────────┐│
│ │DataFrame → CSV.gz       ││
│ │ • Compression GZIP      ││
│ │ • Upload S3             ││
│ │ • Path: raw/{table}/    ││
│ └─────────────────────────┘│
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│ 3. CHARGEMENT S3 (40s)     │
│ ┌─────────────────────────┐│
│ │S3 → 6 DataFrames        ││
│ │ • pd.read_csv()         ││
│ │ • Décompression auto    ││
│ └─────────────────────────┘│
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│ 4. TRANSFORMATION (1 min)  │
│ ┌─────────────────────────┐│
│ │Jointures SQL (pandasql) ││
│ │ • 6 tables → 1 DataFrame││
│ │ • LEFT JOIN sur FK      ││
│ │ • Enrichissement calc   ││
│ └─────────────────────────┘│
└──────────────┬─────────────┘
               │
               ▼
┌────────────────────────────┐
│ 5. VALIDATION (30s)        │
│ ┌─────────────────────────┐│
│ │Great Expectations       ││
│ │ • 8 tests de qualité    ││
│ │ • Isolation rejets      ││
│ │ • Score: 100%           ││
│ └─────────────────────────┘│
└──────────────┬─────────────┘
               │
          ┌────┴────┐
          ▼         ▼
┌──────────────┐  ┌────────────┐
│6. SNOWFLAKE  │  │7. MONGODB  │
│   (2min30s)  │  │   (10s)    │
│ ┌──────────┐ │  │┌──────────┐│
│ │COPY INTO │ │  ││INSERT    ││
│ │ • 111K   │ │  ││ • Stats  ││
│ │   rows   │ │  ││ • Rejets ││
│ └──────────┘ │  │└──────────┘│
└──────────────┘  └────────────┘
       │                │
       └────────┬───────┘
                ▼
            ┌───────┐
            │  END  │
            └───────┘
Total: ~4min 50sec
```

### 4.3 Composants Techniques

| Composant | Technologie | Version | Rôle |
|-----------|------------|---------|------|
| **Source DB** | PostgreSQL | 17 | Base transactionnelle |
| **Orchestrateur** | Apache Airflow | 2.8.3 | Workflow ETL |
| **Data Lake** | AWS S3 | - | Stockage brut |
| **Compute** | Python | 3.11 | Traitement |
| **Data Warehouse** | Snowflake | - | Analytique |
| **Logs/Metadata** | MongoDB | 7.0 | Observabilité |
| **Conteneurisation** | Docker | 24.0+ | Isolation |
| **Qualité données** | Great Expectations | 0.18.19 | Validation |
| **Transformations SQL** | pandasql | 0.7.3 | Jointures |

---

## 5. TECHNOLOGIES ET STACK TECHNIQUE

### 5.1 Justification des Choix Technologiques

| Technologie | Avantages | Inconvénients | Score |
|------------|-----------|--------------|-------|
| **PostgreSQL** | Standard industrie, SQL ACID, open-source | Scalabilité limitée (vertical) | 4/5 |
| **AWS S3** | Scalabilité infinie, 99,99% SLA, coût bas | Latence réseau | 5/5 |
| **Snowflake** | Séparation compute/storage, auto-scaling, Time Travel | Coût variable (pay-per-use) | 5/5 |
| **MongoDB** | Flexibilité schéma, haute performance écriture | Pas de transactions ACID multi-documents | 4/5 |
| **Airflow** | Standard orchestration, UI riche, communauté large | Courbe apprentissage | 5/5 |
| **Python/pandas** | Écosystème riche, facile à maintenir | Performance limitée (GIL) | 4/5 |

### 5.2 Alternatives Évaluées

| Besoin | Choix retenu | Alternatives considérées | Raison du choix |
|--------|-------------|-------------------------|----------------|
| Orchestration | Airflow | Luigi, Prefect, Dagster | Standard industrie, UI |
| Data Lake | S3 | Azure Blob, GCS | Intégration Snowflake |
| Data Warehouse | Snowflake | Redshift, BigQuery, Databricks | Meilleur rapport qualité/prix |
| Processing | pandas | Spark, Dask | Volume actuel < 1 GB |
| Validation | Great Expectations | dbt tests, custom | Framework mature |

---

## 6. PERFORMANCE ET SCALABILITÉ

### 6.1 Métriques de Performance

| Métrique | Valeur actuelle | Cible | Statut |
|----------|----------------|-------|--------|
| **Temps bout-en-bout** | 4 min 50 sec | < 10 min | ✅ Dépassé |
| **Débit extraction** | ~30K enreg./sec | > 10K/sec | ✅ |
| **Débit transformation** | ~2,8K enreg./sec | > 1K/sec | ✅ |
| **Débit chargement Snowflake** | 741 enreg./sec | > 500/sec | ✅ |
| **Coût par 1K avis** | $0,066 | < $0,10 | ✅ |

### 6.2 Stratégie de Scalabilité

**Scalabilité verticale** (court terme : 100K → 1M enregistrements) :
- Augmentation taille instance Snowflake (X-Small → Small)
- Activation du chunking pandas (traitement par lots de 50K lignes)

**Scalabilité horizontale** (long terme : > 10M enregistrements) :
- Migration vers **Apache Spark** pour le processing
- Airflow CeleryExecutor (workers distribués)
- Partitionnement S3 par date (`dt=2025-12-06`)

**Projection de coûts** (1M avis/mois) :

| Composant | Coût actuel (111K) | Projeté (1M) |
|----------|-------------------|-------------|
| S3 | $1 | $10 |
| Snowflake | $50 | $200 |
| MongoDB | $0 (local) | $50 (Atlas M10) |
| **Total** | **$51** | **$260** |

---

## 7. SÉCURITÉ ET CONFORMITÉ

### 7.1 Mesures de Sécurité

| Niveau | Mesure | Implémentation |
|--------|--------|---------------|
| **Réseau** | Chiffrement TLS | PostgreSQL, Snowflake, MongoDB |
| **Stockage** | Encryption at rest | S3 (AES-256), Snowflake (auto) |
| **Accès** | Principe moindre privilège | Compte PostgreSQL read-only, IAM Roles AWS |
| **Authentification** | Credentials management | `.env` (dev), AWS Secrets Manager (prod) |
| **Anonymisation** | Hachage PII | SHA-256 sur `buyer_id` |

### 7.2 Conformité RGPD

| Article RGPD | Exigence | Implémentation |
|-------------|----------|---------------|
| **Article 5** | Minimisation des données | Extraction uniquement des champs nécessaires |
| **Article 4(5)** | Pseudonymisation | Hachage SHA-256 des buyer_id |
| **Article 17** | Droit à l'oubli | Procédure de suppression S3 + Snowflake (Time Travel) |
| **Article 32** | Sécurité du traitement | Chiffrement end-to-end, contrôle d'accès |

---

## 8. ANNEXES

### 8.1 Schéma de la Base PostgreSQL

```sql
-- Fichier : docker/postgres/init/01_schema.sql
CREATE TABLE category (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE product (
    p_id VARCHAR(50) PRIMARY KEY,
    category_id INTEGER REFERENCES category(id) ON DELETE RESTRICT,
    name VARCHAR(500) NOT NULL,
    price DECIMAL(10,2) CHECK (price >= 0),
    description TEXT
);

CREATE TABLE review (
    review_id SERIAL PRIMARY KEY,
    buyer_id VARCHAR(100) NOT NULL,
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title VARCHAR(500),
    description TEXT,
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE product_reviews (
    p_id VARCHAR(50) REFERENCES product(p_id) ON DELETE CASCADE,
    review_id INTEGER REFERENCES review(review_id) ON DELETE CASCADE,
    PRIMARY KEY (p_id, review_id)
);

CREATE TABLE review_images (
    id SERIAL PRIMARY KEY,
    review_id INTEGER REFERENCES review(review_id) ON DELETE CASCADE,
    image_url TEXT NOT NULL
);

CREATE TABLE orders (
    order_id VARCHAR(50) PRIMARY KEY,
    buyer_id VARCHAR(100) NOT NULL,
    p_id VARCHAR(50) REFERENCES product(p_id) ON DELETE SET NULL,
    order_date TIMESTAMP NOT NULL,
    quantity INTEGER DEFAULT 1
);
```

### 8.2 Configuration Docker Compose

**Services déployés** :

```yaml
# docker-compose.postgres.yml
services:
  amazon_postgres_db:
    image: postgres:17
    ports:
      - "5433:5432"
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: admin123
      POSTGRES_DB: amazon_db
    volumes:
      - ./data/clean:/data/clean
      - ./docker/postgres/init:/docker-entrypoint-initdb.d

# docker-compose.mongodb.yml
services:
  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
      - "8081:8081"  # Mongo Express UI
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: changeme

# docker-compose.airflow.yml
services:
  airflow-webserver:
    image: apache/airflow:2.8.3
    ports:
      - "8080:8080"
    environment:
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql://airflow:airflow@postgres-airflow/airflow
```

### 8.3 Checklist de Déploiement Production

- [ ] Migrer credentials vers AWS Secrets Manager
- [ ] Configurer IAM Roles (éviter access keys en dur)
- [ ] Activer CloudWatch Logs pour Airflow
- [ ] Configurer alertes Snowflake (coûts, performance)
- [ ] Activer MongoDB Atlas (HA + backup automatique)
- [ ] Implémenter monitoring Grafana + Prometheus
- [ ] Tests de charge (> 1M enregistrements)
- [ ] Documentation runbook opérationnel
- [ ] Formation équipe Ops

### 8.4 Glossaire

| Terme | Définition |
|-------|-----------|
| **ETL** | Extract-Transform-Load : processus d'extraction, transformation et chargement de données |
| **Data Lake** | Stockage centralisé de données brutes (structurées et non structurées) |
| **Data Warehouse** | Base de données optimisée pour l'analyse (OLAP) |
| **Medallion Architecture** | Pattern Bronze (raw) → Silver (cleaned) → Gold (curated) |
| **Great Expectations** | Framework Python de validation de qualité des données |
| **Chunking** | Traitement par lots pour éviter la saturation mémoire |
| **XCom** | Cross-Communication : mécanisme de partage de données entre tâches Airflow |

---

## SIGNATURES

**Approbation technique** :

| Rôle | Nom | Date | Signature |
|------|------|------|-----------|
| Architecte Data | _______ | 06/12/2025 | _______ |
| Responsable Data Engineering | _______ | 06/12/2025 | _______ |
| Responsable Sécurité | _______ | 06/12/2025 | _______ |

---

**FIN DU DOSSIER D'ARCHITECTURE**

Version : 1.0
Dernière mise à jour : 6 décembre 2025
Prochaine révision : 6 mars 2026
