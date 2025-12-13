# Tests de Qualité des Données - Amazon Reviews ETL

Suite complète de tests pytest pour valider la qualité des données et les transformations du pipeline ETL.

## 📋 Structure des Tests

```
tests/
├── conftest.py                 # Fixtures partagées et configuration pytest
├── test_data_quality.py        # Tests de qualité des données (Great Expectations)
├── test_transformations.py     # Tests unitaires des transformations
└── README.md                   # Ce fichier
```

## 🚀 Installation

Installez les dépendances pytest :

```bash
pip install -r requirements.txt
```

Les packages pytest installés :
- `pytest` : Framework de test
- `pytest-html` : Génération de rapports HTML
- `pytest-cov` : Couverture de code
- `pytest-xdist` : Exécution parallèle

## ▶️ Exécution des Tests

### Exécuter tous les tests

```bash
cd src_code
pytest tests/ -v
```

### Exécuter un fichier de test spécifique

```bash
# Tests de qualité des données
pytest tests/test_data_quality.py -v

# Tests de transformation
pytest tests/test_transformations.py -v
```

### Exécuter des tests par marqueur (marker)

```bash
# Tests de base de données uniquement
pytest tests/ -m database -v

# Tests de qualité uniquement
pytest tests/ -m quality -v

# Tests unitaires uniquement
pytest tests/ -m unit -v

# Tests lents (intégration)
pytest tests/ -m slow -v

# Exclure les tests lents
pytest tests/ -m "not slow" -v
```

### Marqueurs disponibles

| Marqueur | Description |
|----------|-------------|
| `database` | Tests nécessitant une connexion DB |
| `connection` | Tests de connexion |
| `quality` | Tests de qualité des données |
| `ratings` | Validation des ratings |
| `duplicates` | Détection des doublons |
| `nulls` | Tests de valeurs NULL |
| `prices` | Validation des prix |
| `text` | Tests de contenu texte |
| `types` | Tests de types de données |
| `integrity` | Tests d'intégrité référentielle |
| `unit` | Tests unitaires |
| `integration` | Tests d'intégration |
| `slow` | Tests longs |

## 📊 Génération de Rapports

### Rapport HTML avec pytest-html

```bash
# Générer rapport HTML
pytest tests/ -v --html=reports/pytest_report.html --self-contained-html

# Ouvrir le rapport
start reports/pytest_report.html  # Windows
open reports/pytest_report.html   # macOS
xdg-open reports/pytest_report.html  # Linux
```

### Rapport de couverture

```bash
# Générer rapport de couverture
pytest tests/ --cov=scripts --cov-report=html --cov-report=term

# Voir le rapport
start htmlcov/index.html  # Windows
```

### Rapport JSON personnalisé

```bash
# Les tests Great Expectations génèrent un JSON
python tests/test_data_quality.py

# Générer HTML depuis JSON
python scripts/generate_quality_report.py
```

## 🔧 Configuration

### pytest.ini

Le fichier `pytest.ini` à la racine contient la configuration :

```ini
[pytest]
markers =
    database: Tests nécessitant DB
    quality: Tests de qualité
    unit: Tests unitaires
    ...

addopts =
    -v
    --tb=short
    --strict-markers
```

### Variables d'environnement

Les tests nécessitent les variables d'environnement suivantes (fichier `.env`) :

```bash
# PostgreSQL
POSTGRES_CONNECTION_STRING=postgresql://user:pass@host:port/db

# MongoDB
MONGODB_CONNECTION_STRING=mongodb://user:pass@host:port/

# Snowflake
SNOWFLAKE_ACCOUNT=account
SNOWFLAKE_USER=user
SNOWFLAKE_PASSWORD=password
SNOWFLAKE_DATABASE=database
SNOWFLAKE_SCHEMA=schema
SNOWFLAKE_WAREHOUSE=warehouse
```

## 📝 Tests Disponibles

### Tests de Qualité des Données (test_data_quality.py)

1. ✅ **test_postgresql_connection** : Vérification connexion DB
2. ✅ **test_review_ratings_range** : Ratings entre 1-5
3. ✅ **test_no_duplicate_reviews** : Absence de doublons
4. ✅ **test_required_fields_not_null** : Champs obligatoires non NULL
5. ✅ **test_product_prices_positive** : Prix positifs
6. ✅ **test_review_text_not_empty** : Textes non vides
7. ✅ **test_data_types_consistency** : Cohérence des types
8. ✅ **test_referential_integrity** : Intégrité référentielle

### Tests Unitaires (test_transformations.py)

1. ✅ **test_clean_data_with_no_issues** : Données propres
2. ✅ **test_detect_duplicates** : Détection doublons
3. ✅ **test_detect_null_values** : Détection NULL
4. ✅ **test_detect_invalid_ratings** : Ratings invalides
5. ✅ **test_required_columns_present** : Colonnes requises
6. ✅ **test_data_types_after_cleaning** : Types après nettoyage
7. ✅ **test_rating_validation_logic** : Logique validation (paramétré)
8. ✅ **test_dataframe_shape_after_cleaning** : Shape DataFrame
9. ✅ **test_no_data_loss_during_cleaning** : Pas de perte de données
10. ✅ **test_full_cleaning_pipeline** : Pipeline complet (intégration)

## 🎯 Exemples d'Utilisation

### Développement rapide

```bash
# Tests rapides (sans les tests lents)
pytest tests/ -m "not slow" -v

# Tests avec sortie détaillée
pytest tests/ -v -s

# Arrêt au premier échec
pytest tests/ -x
```

### CI/CD

```bash
# Tests pour intégration continue
pytest tests/ -v --tb=short --junit-xml=reports/junit.xml
```

### Débogage

```bash
# Mode verbose avec traces complètes
pytest tests/ -vv --tb=long

# Afficher les print() statements
pytest tests/ -s

# Mode interactif (pdb)
pytest tests/ --pdb
```

### Performance

```bash
# Exécution parallèle (4 workers)
pytest tests/ -n 4

# Exécution parallèle auto
pytest tests/ -n auto
```

## 📈 Résultats Attendus

### Avec données propres

```
==================== test session starts ====================
collected 18 items

tests/test_data_quality.py::test_postgresql_connection PASSED
tests/test_data_quality.py::test_review_ratings_range PASSED
tests/test_data_quality.py::test_no_duplicate_reviews PASSED
...

==================== 18 passed in 5.23s ====================
```

### Taux de réussite

- **Objectif** : 100% de tests passés
- **Seuil acceptable** : ≥ 95%
- **Action requise** : < 95%

## 🔍 Troubleshooting

### Erreur de connexion DB

```bash
# Vérifier les variables d'environnement
pytest tests/ -v --tb=short

# Tester uniquement la connexion
pytest tests/test_data_quality.py::test_postgresql_connection -v
```

### Tests lents

```bash
# Utiliser l'exécution parallèle
pytest tests/ -n auto

# Ou exclure les tests lents
pytest tests/ -m "not slow"
```

### Fixtures non trouvées

Les fixtures sont dans `conftest.py` et chargées automatiquement par pytest.

## 📚 Documentation

- [Pytest Documentation](https://docs.pytest.org/)
- [Great Expectations](https://docs.greatexpectations.io/)
- [pytest-html](https://pytest-html.readthedocs.io/)

## 🤝 Contribution

Pour ajouter de nouveaux tests :

1. Ajouter le test dans le fichier approprié
2. Utiliser les marqueurs appropriés (`@pytest.mark.xxx`)
3. Documenter le test avec un docstring
4. Tester localement avant commit

## 📞 Support

Pour toute question :
- Consulter la documentation du projet
- Vérifier les logs dans `reports/`
- Examiner les rapports HTML générés
