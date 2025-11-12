-- ============================================
-- SQL QUERIES - Step 4 Case Study
-- ============================================
-- Fichier : 02_data_aggregation.sql
-- Objectif : Agrégations pour le dashboard et analyses
-- Date : 2025-11-03
-- ============================================

-- ============================================
-- REQUÊTE 1 : Statistiques par catégorie NLP
-- ============================================
-- Objectif : Calculer les métriques agrégées par catégorie après classification
-- NOTE : Cette requête suppose que REVIEWS_ANALYZED existe (créée par le notebook)

SELECT
    category,
    COUNT(*) as nb_reviews,
    ROUND(AVG(rating), 2) as avg_rating,
    ROUND(AVG(relevance_score), 2) as avg_relevance,
    ROUND(AVG(confidence_score), 3) as avg_confidence,
    ROUND(AVG(text_length), 0) as avg_text_length,
    SUM(CASE WHEN classification_review = 'Relevant' THEN 1 ELSE 0 END) as nb_relevant,
    ROUND(SUM(CASE WHEN classification_review = 'Relevant' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct_relevant
FROM REVIEWS_ANALYZED
GROUP BY category
ORDER BY nb_reviews DESC;


-- ============================================
-- REQUÊTE 2 : Distribution ratings par catégorie
-- ============================================
-- Objectif : Matrice catégorie x rating pour heatmap

SELECT
    category,
    rating,
    COUNT(*) as count
FROM REVIEWS_ANALYZED
GROUP BY category, rating
ORDER BY category, rating;


-- ============================================
-- REQUÊTE 3 : Top reviews pertinentes
-- ============================================
-- Objectif : Extraire les reviews avec le meilleur relevance score

SELECT
    review_id,
    category,
    rating,
    relevance_score,
    confidence_score,
    description,
    text_length,
    has_image,
    has_orders
FROM REVIEWS_ANALYZED
WHERE relevance_score >= 80
ORDER BY relevance_score DESC
LIMIT 50;


-- ============================================
-- REQUÊTE 4 : Analyse temporelle (si dates disponibles)
-- ============================================
-- Objectif : Évolution du volume de reviews par catégorie/mois
-- NOTE : Adapter si colonne date disponible

-- SELECT
--     DATE_TRUNC('month', review_date) as month,
--     category,
--     COUNT(*) as nb_reviews,
--     AVG(rating) as avg_rating,
--     AVG(relevance_score) as avg_relevance
-- FROM REVIEWS_ANALYZED
-- GROUP BY DATE_TRUNC('month', review_date), category
-- ORDER BY month, category;


-- ============================================
-- REQUÊTE 5 : Reviews problématiques à analyser
-- ============================================
-- Objectif : Identifier reviews avec low confidence score pour validation

SELECT
    review_id,
    category,
    confidence_score,
    rating,
    description
FROM REVIEWS_ANALYZED
WHERE confidence_score < 0.50  -- Seuil de confiance faible
ORDER BY confidence_score ASC
LIMIT 20;


-- ============================================
-- REQUÊTE 6 : Statistiques globales pour dashboard
-- ============================================
-- Objectif : KPIs principaux en une seule requête

SELECT
    COUNT(*) as total_reviews,
    ROUND(AVG(rating), 2) as avg_rating,
    ROUND(AVG(relevance_score), 2) as avg_relevance,
    ROUND(AVG(confidence_score), 3) as avg_confidence,
    SUM(CASE WHEN classification_review = 'Relevant' THEN 1 ELSE 0 END) as nb_relevant,
    ROUND(SUM(CASE WHEN classification_review = 'Relevant' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct_relevant,
    SUM(CASE WHEN has_image = 1 THEN 1 ELSE 0 END) as nb_with_images,
    ROUND(SUM(CASE WHEN has_image = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as pct_with_images
FROM REVIEWS_ANALYZED;


-- ============================================
-- REQUÊTE 7 : Comparaison relevance score par rating
-- ============================================
-- Objectif : Analyser la corrélation rating vs relevance

SELECT
    rating,
    COUNT(*) as nb_reviews,
    ROUND(AVG(relevance_score), 2) as avg_relevance,
    ROUND(MIN(relevance_score), 2) as min_relevance,
    ROUND(MAX(relevance_score), 2) as max_relevance,
    ROUND(STDDEV(relevance_score), 2) as std_relevance
FROM REVIEWS_ANALYZED
GROUP BY rating
ORDER BY rating;


-- ============================================
-- NOTES D'UTILISATION
-- ============================================
-- 1. Ces requêtes nécessitent la table REVIEWS_ANALYZED créée par le notebook
-- 2. Adapter les noms de colonnes selon votre schéma
-- 3. Les requêtes sont optimisées pour Snowflake (fonctions de fenêtrage disponibles)
-- 4. Utiliser LIMIT pour tests rapides sur gros volumes
