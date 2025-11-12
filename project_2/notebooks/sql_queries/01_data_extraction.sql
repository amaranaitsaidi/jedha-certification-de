-- ============================================
-- SQL QUERIES - Step 4 Case Study
-- ============================================
-- Fichier : 01_data_extraction.sql
-- Objectif : Extraction des données depuis Snowflake
-- Date : 2025-11-03
-- ============================================

-- ============================================
-- REQUÊTE 1 : Top produits par volume de reviews
-- ============================================
-- Objectif : Identifier les produits avec un volume significatif de reviews (minimum 15)

SELECT
    p.p_id,
    p.p_name,
    p.price,
    c.name as category,
    COUNT(pr.review_id) as nb_reviews,
    ROUND(AVG(r.rating), 2) as avg_rating
FROM product p
JOIN product_reviews pr ON p.p_id = pr.p_id
JOIN review r ON pr.review_id = r.review_id
LEFT JOIN category c ON p.category_id = c.category_id
GROUP BY p.p_id, p.p_name, p.price, c.name
HAVING COUNT(pr.review_id) >= 15  -- Au moins 15 reviews pour échantillon significatif
ORDER BY nb_reviews DESC
LIMIT 20;


-- ============================================
-- REQUÊTE 2 : Extraction complète des reviews d'un produit
-- ============================================
-- Objectif : Extraire toutes les reviews d'un produit avec leurs caractéristiques
-- NOTE : Remplacer '<SELECTED_PRODUCT_ID>' par l'ID du produit sélectionné

SELECT
    r.review_id,
    r.buyer_id,
    r.title,
    r.r_desc AS description,
    r.rating,
    LENGTH(r.r_desc) AS text_length,
    CASE WHEN ri.review_id IS NOT NULL THEN 1 ELSE 0 END AS has_image,
    CASE WHEN o.order_id IS NOT NULL THEN 1 ELSE 0 END AS has_orders,
    p.p_id,
    p.p_name AS product_name,
    c.name AS category
FROM review r
LEFT JOIN product_reviews pr ON r.review_id = pr.review_id
LEFT JOIN product p ON pr.p_id = p.p_id
LEFT JOIN category c ON p.category_id = c.category_id
LEFT JOIN review_images ri ON r.review_id = ri.review_id
LEFT JOIN orders o ON r.buyer_id = o.buyer_id
WHERE pr.p_id = '<SELECTED_PRODUCT_ID>'
ORDER BY r.review_id;


-- ============================================
-- REQUÊTE 3 : Vérification de la qualité des données
-- ============================================
-- Objectif : Identifier valeurs manquantes et doublons

-- Compter les valeurs NULL par colonne
SELECT
    COUNT(*) as total_reviews,
    SUM(CASE WHEN r_desc IS NULL OR r_desc = '' THEN 1 ELSE 0 END) as null_description,
    SUM(CASE WHEN title IS NULL OR title = '' THEN 1 ELSE 0 END) as null_title,
    SUM(CASE WHEN rating IS NULL THEN 1 ELSE 0 END) as null_rating
FROM review;

-- Identifier les doublons
SELECT
    review_id,
    COUNT(*) as duplicates
FROM review
GROUP BY review_id
HAVING COUNT(*) > 1;


-- ============================================
-- NOTES D'UTILISATION
-- ============================================
-- 1. Adapter les noms de tables selon votre schéma Snowflake
-- 2. Remplacer '<SELECTED_PRODUCT_ID>' par l'ID réel du produit
-- 3. Vérifier les permissions d'accès aux tables
-- 4. Optimiser avec LIMIT pour tests rapides
