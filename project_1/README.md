# Projet 1 - Analyse des Avis Amazon et Scoring de Pertinence

## Description du Projet

Ce projet s'inscrit dans le cadre de la certification Jedha en Data Engineering. Il vise à développer un système intelligent d'analyse des avis clients Amazon pour améliorer l'expérience utilisateur sur les plateformes e-commerce.

Face au volume massif d'avis reçus quotidiennement (millions de commentaires), il devient crucial pour les consommateurs d'identifier rapidement les commentaires les plus pertinents et informatifs. Ce projet propose un **prototype fonctionnel** capable d'évaluer automatiquement la pertinence des reviews selon des critères objectifs.

## Objectifs

1. **Analyser** les avis clients Amazon de manière structurée
2. **Développer** un système de scoring de pertinence (0-100)
3. **Identifier** les reviews les plus informatives pour les utilisateurs
4. **Valider** la faisabilité technique sur un échantillon représentatif

## Méthodologie

### Données Analysées

- **Échantillon initial** : 376 reviews d'un produit représentatif
- **Échantillon étendu** : 2 592 reviews de 10 produits
- **Base de données totale** : 111 322 reviews disponibles pour extension future

### Système de Scoring de Pertinence

Le score de pertinence (0-100) combine **5 critères pondérés** :

| Critère | Pondération | Description |
|---------|-------------|-------------|
| **Longueur du texte** | 30% | Fonction gaussienne centrée sur 300 caractères |
| **Présence d'images** | 20% | Indicateur de qualité et engagement |
| **Achat vérifié** | 10% | Vérification via historique de commandes |
| **Rating extrême** | 15% | Reviews 1★ ou 5★ (plus détaillées) |
| **Densité sentiment** | 25% | Analyse VADER pour polarité du texte |

### Formule du Score

```python
relevance_score = (
    0.30 * text_length_score +
    0.20 * has_image +
    0.10 * has_orders +
    0.15 * is_extreme_rating +
    0.25 * keyword_score
) * 100
```

## Structure du Projet

```
project_1/
├── src/
│   └── Step_5_relevance_score_prototype-1.ipynb   # Notebook principal du prototype
├── docs/
│   ├── PDF/
│   │   ├── Project1_Step1_Strategic_Analysis_Report.pdf
│   │   ├── Project1-Step2-Ideation-and-Use-Case-Priorization.pdf
│   │   ├── Project1-Step3-Regulatory-and-Technology-Watch.pdf
│   │   ├── Project1-Step4-Data-Selection-And-Opportunity-Mapping.pdf
│   │   ├── Project1-Step6-Project-Requirements-Document.pdf
│   │   └── Project1-Step6-Technical-And-Functional-Specifications.pdf
│   └── Projet-01-Contexte-Industriel-Amazon-et-Prototype.pptx
└── README.md
```

## Technologies Utilisées

- **Python** : Langage principal
- **PostgreSQL** : Base de données (Neon Database)
- **Bibliothèques** :
  - `pandas`, `numpy` : Manipulation de données
  - `matplotlib`, `seaborn` : Visualisation
  - `nltk` (VADER) : Analyse de sentiment
  - `psycopg2` : Connexion PostgreSQL

## Installation et Utilisation

### Prérequis

```bash
pip install pandas numpy matplotlib seaborn nltk psycopg2-binary
```

### Configuration de la Base de Données

Le projet utilise une base de données PostgreSQL hébergée sur Neon. La chaîne de connexion est déjà configurée dans le notebook (accès en lecture seule).

### Exécution du Prototype

1. Ouvrir le notebook `src/Step_5_relevance_score_prototype-1.ipynb`
2. Exécuter les cellules séquentiellement
3. Les graphiques de statistiques seront générés automatiquement



## Auteurs

- **Amara NAIT SAIDI** 

