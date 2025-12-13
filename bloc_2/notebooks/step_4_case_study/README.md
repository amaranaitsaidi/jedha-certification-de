# Step 4: Case Study - Data Analysis

## 📋 Vue d'Ensemble

Ce dossier contient le **Jupyter Notebook principal** pour l'analyse et la catégorisation des avis utilisateurs Amazon via des algorithmes NLP (Natural Language Processing).

**Objectif** : Développer un système automatisé de classification thématique et de scoring de pertinence des reviews.

---

## 📁 Structure du Projet

```
project_2/
│
├── notebooks/
│   ├── step_4_case_study/
|   |   ├── data
|   |   |   └── df_relevant_reviews.csv         📄 fichier pré-calculé
│   │   ├── Step_4_Case_Study_Analysis.ipynb    ⭐ Notebook principal
│   │   └── README.md                           📄 Ce fichier
│   │
│   └── sql_queries/                            📂 Requêtes SQL Snowflake
│       ├── 01_data_extraction.sql              → Extraction des données
│       ├── 02_data_aggregation.sql             → Agrégations pour dashboard
│       └── 03_advanced_analysis.sql            → Analyses avancées
│
├── data/outputs/
│   ├── visualizations/                         📊 Graphiques générés
│   │   ├── local_streamlit_dashboard.py        📊 Dashboard à exécuter en local (similaire au résultat du streamlit App sur Snowflake)
│   └── └── snowflake_streamlit_dashboard.py    📊 Streamlit App Snowflake
│
│
└── docs/
    └── Project2-step4-Analysis-report...pdf    📄 Rapport d'analyse (5-10 pages)
```
---

## 🚀 Démarrage Rapide

### 1. Prérequis

```bash
# Installer les dépendances Python
pip install snowflake-connector-python
pip install transformers torch
pip install nltk pandas numpy matplotlib seaborn plotly
```

### 2. Configuration Snowflake

Mettre à jour les credentials dans le notebook (Section 2.3) :

```python
conn_params = {
    'account': 'YOUR_ACCOUNT',
    'user': 'YOUR_USER',
    'password': 'YOUR_PASSWORD',
    'warehouse': 'YOUR_WAREHOUSE',
    'database': 'YOUR_DATABASE',
    'schema': 'YOUR_SCHEMA'
}
```

### 3. Exécution

1. Ouvrir `Step_4_Case_Study_Analysis.ipynb` dans Jupyter/VS Code
2. Exécuter les cellules séquentiellement (Shift+Enter)
3. Suivre les instructions dans chaque section

---

## 📊 Contenu du Notebook

### Section 1 : Introduction & Contexte
- Problématique business
- Objectifs de l'analyse
- Questions de recherche

### Section 2 : Configuration & Connexion
- Installation des dépendances
- Import des bibliothèques
- Connexion à Snowflake

### Section 3 : Extraction des Données et application des algorithmes
- Sélection du produit échantillon
- Extraction des reviews depuis Snowflake
- Nettoyage des données
- Application de l'algorithme de pondération
- Application de l'agorithme Zero-shot. Note : pour gagner du temps, ne pas lancer les algorithmes et partir directement de la section 3.1.1 en utilisant le fichier pré-calculé.
- Définission de seuils de pertinence

### Section 4 : Sauvegarde des résultats dans Snowflake
- Statistiques descriptives
- Visualisations (ratings, longueur, images)
- Insights clés

### Section 5 : Dashboards et visulations
- Pour cette section il faut soit passer dans Snowflake et lancer une Streamlit App. Soit lancer en local le fichier avec le script streamlit fourni.


### Section 6 : Livrables & Export
- Documentation : rapport d'analyse

---

## 🎯 Algorithme de Classification

### Zero-Shot Classification

**Modèle** : `mDeBERTa-v3` pour multilingue

**Catégories métier** :
1. **Product Quality or Satisfaction** : Qualité, performance, satisfaction
2. **Product Defect or Damaged Item** : Défauts, problèmes, dommages
3. **Delivery Issue or Shipping Delay** : Livraison, délais, packaging
4. **Customer Service or Support** : SAV, remboursement, support

**Avantages** :
- Pas de labeling manuel requis
- Flexibilité (ajustement des catégories sans ré-entraînement)
- Performance acceptable (70-85%)

---

## 📈 Relevance Score

### Formule

```python
relevance_score = (
    0.30 × text_length_score      # Gaussienne centrée sur 300 caractères
  + 0.20 × has_image              # Présence d'image (0 ou 1)
  + 0.10 × has_orders             # Achat vérifié (0 ou 1)
  + 0.15 × is_extreme_rating      # Rating 1★ ou 5★ (0 ou 1)
  + 0.25 × sentiment_score        # VADER sentiment (0-1)
) × 100
```

**Échelle** : 0-100 (plus élevé = plus pertinent)

**Seuil de pertinence** : 60/100

---


## 🛠️ Technologies Utilisées

| Technologie | Usage | Version |
|-------------|-------|---------|
| **Python** | Langage principal | 3.11+ |
| **Snowflake** | Data warehouse | - |
| **Transformers (Hugging Face)** | Modèles NLP | 4.30+ |
| **PyTorch** | Backend ML | 2.0+ |
| **NLTK** | Sentiment analysis (VADER) | 3.8+ |
| **Pandas** | Manipulation de données | 2.0+ |
| **Matplotlib/Seaborn** | Visualisations statiques | - |
| **Plotly** | Visualisations interactives | 5.0+ |
| **Streamlit** | Dashboard (futur) | 1.30+ |

---

**Temps estimé pour l'exécution du notebook complet sur Google Colab** : 3 heures pour 111K avis avec GPU.

---


## 📚 Ressources & Références

### Documentation officielle
- [Hugging Face - Zero-Shot Classification](https://huggingface.co/tasks/zero-shot-classification)
- [VADER Sentiment Analysis](https://github.com/cjhutto/vaderSentiment)
- [Snowflake Python Connector](https://docs.snowflake.com/en/user-guide/python-connector)
- [Streamlit Documentation](https://docs.streamlit.io)

### Papers
- [BART: Denoising Sequence-to-Sequence Pre-training](https://arxiv.org/abs/1910.13461)
- [DeBERTa: Decoding-enhanced BERT with Disentangled Attention](https://arxiv.org/abs/2006.03654)

### Modèles utilisés
- [facebook/bart-large-mnli](https://huggingface.co/facebook/bart-large-mnli)
- [MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7](https://huggingface.co/MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7)

---

## 🤝 Support & Contact

Pour toute question sur ce case study :

1. **Consulter le notebook** : Commentaires détaillés dans chaque cellule
2. **Examiner les visualisations** : `data/outputs/visualizations/local_streamlit_dashboard.py`
3. **Lire le rapport final** : `/docs/Project2-step4-Analysis-report...pdf` (après génération)


---

**Dernière mise à jour** : 2025-11-28
**Version** : 1.0
**Status** : Structure créée, prêt pour exécution
