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

## Résultats Clés

### Statistiques de l'Échantillon (10 produits)

- **Total reviews** : 2 592
- **Distribution ratings** : 76,4% de 5★ (biais positif)
- **Présence d'images** : 31,6% des reviews
- **Longueur médiane** : 44 caractères
- **Longueur moyenne** : 117 caractères

### Insights Principaux

1. **Biais positif massif** : Les produits analysés sont très bien notés
2. **Textes courts** : Majorité de reviews brèves ("Excellent !", "Top !")
3. **Reviews négatives plus détaillées** : Les 1★ et 2★ contiennent plus de contexte
4. **Images corrélées au sentiment** : 35,7% pour 5★ vs 7,6% pour 1★

### Classification

Avec un seuil de **80 points** :
- **Reviews pertinentes** : 39 (1,5%)
- **Reviews non pertinentes** : 2 553 (98,5%)

*Note : Le seuil est volontairement strict pour ce prototype*

## Limitations et Perspectives

### Limitations Identifiées

1. **Échantillon restreint** : Seulement 10 produits analysés
2. **Biais des données** : 76,4% de 5★, peu représentatif de tous les produits
3. **Textes courts** : Médiane de 44 caractères limite l'analyse NLP
4. **Achat vérifié** : 100% dans l'échantillon (pas de différenciation possible)
5. **Seuil strict** : 80% peut être trop élevé (98,5% classés comme non pertinents)

### Améliorations Proposées

#### Court Terme (0-3 mois)
- Filtrer les reviews <30 caractères avant classification
- Élargir à 20-50 produits de catégories variées
- Ajuster la pondération du `text_length_score`
- Validation manuelle sur 500-1000 reviews

#### Moyen Terme (3-6 mois)
- Fine-tuning avec dataset Amazon labelisé
- Intégration d'embeddings (sentence-transformers)
- Déploiement sur infrastructure GPU (AWS/GCP)

#### Long Terme (6-12 mois)
- Modèle multi-tâches : catégorisation + scoring + sentiment
- Détection de spam et fake reviews
- A/B testing pour mesurer l'impact business

## Tests Fonctionnels

Le prototype inclut des tests unitaires pour :
- `calculate_text_length_score()` : Validation de la fonction gaussienne
- `is_extreme_rating()` : Vérification des ratings extrêmes
- `sentiment_score()` : Tests VADER sur textes positifs/négatifs
- `calculate_relevance_score()` : Intégrité du pipeline complet

Tous les tests passent avec succès ✅

## Auteurs

- **Amara NAIT SAIDI** - Développeur principal
- **Dyhia TOUAHRI** - Contributeur

## Licence

Projet académique - Certification Jedha RNCP 37172

## Contact

Pour toute question concernant ce projet, veuillez contacter l'équipe via le dépôt GitHub.

---

**Date de dernière mise à jour** : Décembre 2025
