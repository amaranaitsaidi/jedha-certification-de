-- ============================================
-- SQL QUERIES - Step 4 Case Study
-- ============================================
-- Fichier : 03_advanced_analysis.sql
-- Objectif : Analyses avancées et insights métier
-- Date : 2025-11-03
-- ============================================

-- ============================================
-- REQUÊTE 1 : Corrélation has_image vs relevance
-- ============================================
-- Objectif : Mesurer l'impact de la présence d'images sur la pertinence

SELECT
    has_image,
    COUNT(*) as nb_reviews,
    ROUND(AVG(relevance_score), 2) as avg_relevance,
    ROUND(AVG(rating), 2) as avg_rating,
    ROUND(AVG(text_length), 0) as avg_text_length
FROM REVIEWS_ANALYZED
GROUP BY has_image
ORDER BY has_image DESC;


-- ============================================
-- REQUÊTE 2 : Distribution de la longueur de texte par catégorie
-- ============================================
-- Objectif : Identifier si certaines catégories génèrent des reviews plus longues

SELECT
    category,
    COUNT(*) as nb_reviews,
    ROUND(AVG(text_length), 0) as avg_length,
    ROUND(MIN(text_length), 0) as min_length,
    ROUND(MAX(text_length), 0) as max_length,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY text_length), 0) as median_length
FROM REVIEWS_ANALYZED
GROUP BY category
ORDER BY avg_length DESC;


-- ============================================
-- REQUÊTE 3 : Reviews courtes vs longues - Performance du modèle
-- ============================================
-- Objectif : Analyser l'impact de la longueur sur la confiance du modèle

SELECT
    CASE
        WHEN text_length < 30 THEN 'Très court (<30)'
        WHEN text_length < 100 THEN 'Court (30-100)'
        WHEN text_length < 300 THEN 'Moyen (100-300)'
        ELSE 'Long (>300)'
    END as length_category,
    COUNT(*) as nb_reviews,
    ROUND(AVG(confidence_score), 3) as avg_confidence,
    ROUND(AVG(relevance_score), 2) as avg_relevance,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM REVIEWS_ANALYZED), 1) as pct_total
FROM REVIEWS_ANALYZED
GROUP BY length_category
ORDER BY MIN(text_length);


-- ============================================
-- REQUÊTE 4 : Produits avec le plus de reviews "Delivery Issue"
-- ============================================
-- Objectif : Identifier les produits avec problèmes logistiques
-- NOTE : Adapter si analyse multi-produits

SELECT
    product_name,
    COUNT(*) as nb_delivery_issues,
    ROUND(AVG(rating), 2) as avg_rating,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM REVIEWS_ANALYZED WHERE category = 'delivery issue or shipping delay'), 1) as pct_of_category
FROM REVIEWS_ANALYZED
WHERE category = 'delivery issue or shipping delay'
GROUP BY product_name
ORDER BY nb_delivery_issues DESC
LIMIT 10;


-- ============================================
-- REQUÊTE 5 : Analyse de cohérence rating vs sentiment
-- ============================================
-- Objectif : Identifier les reviews incohérentes (ex: 5★ mais sentiment négatif)

SELECT
    review_id,
    rating,
    keyword_score,  -- sentiment score (0-1)
    relevance_score,
    description,
    CASE
        WHEN rating >= 4 AND keyword_score < 0.4 THEN 'Incohérent Positif'
        WHEN rating <= 2 AND keyword_score > 0.6 THEN 'Incohérent Négatif'
        ELSE 'Cohérent'
    END as coherence_label
FROM REVIEWS_ANALYZED
WHERE (rating >= 4 AND keyword_score < 0.4) OR (rating <= 2 AND keyword_score > 0.6)
ORDER BY ABS((rating / 5.0) - keyword_score) DESC
LIMIT 20;


-- ============================================
-- REQUÊTE 6 : Benchmark des sous-scores du relevance_score
-- ============================================
-- Objectif : Comprendre quels critères contribuent le plus au score final

SELECT
    category,
    ROUND(AVG(text_length_score), 3) as avg_text_length_score,
    ROUND(AVG(has_image), 2) as avg_has_image,
    ROUND(AVG(has_orders), 2) as avg_has_orders,
    ROUND(AVG(is_extreme_rating), 2) as avg_is_extreme_rating,
    ROUND(AVG(keyword_score), 3) as avg_keyword_score,
    ROUND(AVG(relevance_score), 2) as avg_relevance_total
FROM REVIEWS_ANALYZED
GROUP BY category
ORDER BY avg_relevance_total DESC;


-- ============================================
-- REQUÊTE 7 : Détection de reviews potentiellement spam/fake
-- ============================================
-- Objectif : Identifier patterns suspects (reviews très courtes, génériques)

SELECT
    review_id,
    rating,
    text_length,
    description,
    relevance_score,
    confidence_score
FROM REVIEWS_ANALYZED
WHERE
    (text_length < 20 AND rating IN (1, 5))  -- Très courtes et extrêmes
    OR (description LIKE '%Perfect!%' OR description LIKE '%Great!%' OR description LIKE '%Excellent!%')  -- Génériques
ORDER BY text_length ASC
LIMIT 30;


-- ============================================
-- REQUÊTE 8 : Ranking des reviews les plus utiles par catégorie
-- ============================================
-- Objectif : Créer un top 3 des reviews à mettre en avant

WITH ranked_reviews AS (
    SELECT
        review_id,
        category,
        rating,
        relevance_score,
        description,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY relevance_score DESC) as rank
    FROM REVIEWS_ANALYZED
    WHERE relevance_score >= 70  -- Seuil minimum de pertinence
)
SELECT
    category,
    rank,
    review_id,
    rating,
    relevance_score,
    LEFT(description, 150) || '...' as description_preview
FROM ranked_reviews
WHERE rank <= 3
ORDER BY category, rank;


-- ============================================
-- REQUÊTE 9 : Distribution des quartiles de relevance_score
-- ============================================
-- Objectif : Identifier les seuils optimaux pour classification

SELECT
    'Q1 (25%)' as quartile,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY relevance_score), 2) as score_threshold
FROM REVIEWS_ANALYZED
UNION ALL
SELECT
    'Q2 (50%)' as quartile,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY relevance_score), 2) as score_threshold
FROM REVIEWS_ANALYZED
UNION ALL
SELECT
    'Q3 (75%)' as quartile,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY relevance_score), 2) as score_threshold
FROM REVIEWS_ANALYZED
UNION ALL
SELECT
    'Q4 (90%)' as quartile,
    ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY relevance_score), 2) as score_threshold
FROM REVIEWS_ANALYZED;


-- ============================================
-- REQUÊTE 10 : Export pour dashboard Streamlit
-- ============================================
-- Objectif : Vue matérialisée pour optimiser les requêtes du dashboard

-- CREATE OR REPLACE VIEW DASHBOARD_SUMMARY AS
-- SELECT
--     category,
--     rating,
--     classification_review,
--     COUNT(*) as count,
--     ROUND(AVG(relevance_score), 2) as avg_relevance,
--     ROUND(AVG(confidence_score), 3) as avg_confidence
-- FROM REVIEWS_ANALYZED
-- GROUP BY category, rating, classification_review;


-- ============================================
-- NOTES D'UTILISATION
-- ============================================
-- 1. Ces requêtes sont optimisées pour Snowflake (PERCENTILE_CONT, window functions)
-- 2. Adapter les seuils selon les résultats de votre analyse
-- 3. Pour production, créer des vues matérialisées pour performances
-- 4. Monitorer les coûts Snowflake pour requêtes fréquentes
