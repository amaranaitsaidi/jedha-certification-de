--------------------------------------------------------------------------------------------
----------------------------------- Analyse 1 ----------------------------------------------
--------------------------------------------------------------------------------------------

-- Visualiser la distribution des avis selon leur status de pertinence.
SELECT
  RELEVANT_STATUS,
  COUNT(*) AS NB_REVIEWS,
  ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS POURCENTAGE
FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
GROUP BY RELEVANT_STATUS;

--------------------------------------------------------------------------------------------
----------------------------------- Analyse 2 ----------------------------------------------
--------------------------------------------------------------------------------------------

-- Analyse de la distribution de la pertinence selon :
-- la moyenne des scores calculés avec les algoritgmes et la moyenne de longueur des avis.
-- Objectif : vérifier que les avis classés "RELEVANT" ont bien :
-----------> un score de pertinence plus élevé
-----------> un score de confiance plus élevé
-----------> des textes un peu plus longs
-- Cette requête confirme que le modèle classe bien les avis selon les critères définis.

SELECT
    RELEVANT_STATUS,
    AVG(RELEVANCE_SCORE) AS AVG_RELEVANCE,
    AVG(CONFIDENCE_SCORE) AS AVG_CONFIDENCE,
    AVG(TEXT_LENGTH_SCORE) AS AVG_LENGTH_SCORE
FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
GROUP BY RELEVANT_STATUS;

--------------------------------------------------------------------------------------------
----------------------------------- Analyse 3 ----------------------------------------------
--------------------------------------------------------------------------------------------

-- Objectis :
-----------> Voir s'il y a des categories qui génèrent plus d'avis pertinents que d'autres.
-----------> Pouvoir identifier les catégories les plus problématiques et les plus intéressantes à traiter.
SELECT
  CATEGORY,
  COUNT(*) AS NB_REVIEWS,
  SUM(CASE WHEN RELEVANT_STATUS = 'RELEVANT' THEN 1 ELSE 0 END) AS NB_RELEVANT,
  ROUND(100.0 * SUM(CASE WHEN RELEVANT_STATUS = 'RELEVANT' THEN 1 ELSE 0 END) / COUNT(*), 2) AS POURCENTAGE_RELEVANT,
  AVG(RATING) AS AVG_RATING
FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
GROUP BY CATEGORY
ORDER BY NB_REVIEWS DESC;

--------------------------------------------------------------------------------------------
----------------------------------- Analyse 4 ----------------------------------------------
--------------------------------------------------------------------------------------------

-- Analyser la pertinence des avis par produit.
-- Objectifs :
-----------> Repèrer les produits avec un % très haut → avis riches & détaillés
-----------> Repèrer les produits avec un % très bas → avis pauvres ou spam
-----------> Repèrer les produits avec beaucoup d’avis → candidats pour analyses approfondies
--- Permet d’identifier quels produits génèrent du bon feedback ou au contraire pas du tout.

SELECT
    P_ID,
    PRODUCT_NAME,
    COUNT(*) AS NB_REVIEWS,
    SUM(CASE WHEN RELEVANT_STATUS = 'RELEVANT' THEN 1 ELSE 0 END) AS NB_RELEVANT,
    ROUND(100.0 * SUM(CASE WHEN RELEVANT_STATUS = 'RELEVANT' THEN 1 ELSE 0 END) / COUNT(*), 2) AS PCT_RELEVANT,
    AVG(RATING) AS AVG_RATING
FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
GROUP BY P_ID, PRODUCT_NAME
HAVING COUNT(*) >= 3
ORDER BY NB_REVIEWS DESC, PCT_RELEVANT DESC;

--------------------------------------------------------------------------------------------
----------------------------------- Analyse 5 ----------------------------------------------
--------------------------------------------------------------------------------------------

-- Analyse de la longueur des textes pour voir si elle corrélée avec la pertinence.
-- Ce que nous voulons observer :
-----------> RELEVANT → textes généralement plus longs
-----------> IRRELEVANT → textes plus courts.
-- Objectifs :
-----------> Justifier l’utilisation du critère TEXT_LENGTH_SCORE dans le modèle.

SELECT
  RELEVANT_STATUS,
  AVG(TEXT_LENGTH) AS AVG_LEN,
  MIN(TEXT_LENGTH) AS MIN_LEN,
  MAX(TEXT_LENGTH) AS MAX_LEN
FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
where TEXT_LENGTH > 0
GROUP BY RELEVANT_STATUS
;

--------------------------------------------------------------------------------------------
----------------------------------- Analyse 6 ----------------------------------------------
--------------------------------------------------------------------------------------------

-- Analyser si les notes extrêmes influencent la pertinence
-- Permet de comprendre si le rating introduit un biais dans les reviews.

SELECT
  IS_EXTREME_RATING,
  RELEVANT_STATUS,
  COUNT(*) AS NB
FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
GROUP BY IS_EXTREME_RATING, RELEVANT_STATUS
ORDER BY IS_EXTREME_RATING;


--------------------------------------------------------------------------------------------
----------------------------------- Analyse 7 ----------------------------------------------
--------------------------------------------------------------------------------------------

-- Analyser si la présence des mots-clés augmente la pertinence.
-- Permet de valider ou pas la pertinence d'avoir mis cette cette feature dans le score de pondération.

SELECT
  RELEVANT_STATUS,
  AVG(KEYWORD_SCORE) AS AVG_KEYWORD
FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
GROUP BY RELEVANT_STATUS;


--------------------------------------------------------------------------------------------
----------------------------------- Analyse 8 ----------------------------------------------
--------------------------------------------------------------------------------------------

-- Analyse de la distribution du statut de pertinence selon le rating
-- Visualiser comment la pertinence (RELEVANT / IRRELEVANT) varie selon la note laissée.

SELECT
    RATING,
    RELEVANT_STATUS,
    COUNT(*) AS NB_REVIEWS,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY RATING), 2) AS PCT_PER_STATUS
FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
GROUP BY RATING, RELEVANT_STATUS
ORDER BY RATING, RELEVANT_STATUS;

--------------------------------------------------------------------------------------------
----------------------------------- Analyse 9 ----------------------------------------------
--------------------------------------------------------------------------------------------

-- Distribution du statut selon la présence ou non d’une image
-- Mesurer si la présence d’image influence indirectement la pertinence

SELECT
    HAS_IMAGE,
    RELEVANT_STATUS,
    COUNT(*) AS NB_REVIEWS,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY HAS_IMAGE), 2) AS PCT_PER_STATUS
FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
GROUP BY HAS_IMAGE, RELEVANT_STATUS
ORDER BY HAS_IMAGE, RELEVANT_STATUS;

--------------------------------------------------------------------------------------------
----------------------------------- Analyse 10 ----------------------------------------------
--------------------------------------------------------------------------------------------

-- Distribution du statut selon le fait que l’utilisateur a déjà commandé le produit
-- L'objectif est de voir si le modèle classe trop sévèrement les avis "non vérifiés"
SELECT
    HAS_ORDERS,
    RELEVANT_STATUS,
    COUNT(*) AS NB_REVIEWS,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY HAS_ORDERS), 2) AS PCT_PER_STATUS
FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
GROUP BY HAS_ORDERS, RELEVANT_STATUS
ORDER BY HAS_ORDERS, RELEVANT_STATUS;

--------------------------------------------------------------------------------------------
----------------------------------- Analyse 11 ----------------------------------------------
--------------------------------------------------------------------------------------------

-- Distribution du statut selon la langueur des avis
-- Objectif : voir si le modèle classe bien les avis courts comme "IRRELEVANT"
SELECT
    COUNT(*) AS NB_RELEVANT,
    SUM(CASE WHEN TEXT_LENGTH BETWEEN 0 AND 5 THEN 1 ELSE 0 END) AS LEVEL0,
    SUM(CASE WHEN TEXT_LENGTH BETWEEN 6 AND 10 THEN 1 ELSE 0 END) AS LEVEL1,
    SUM(CASE WHEN TEXT_LENGTH BETWEEN 11 AND 20 THEN 1 ELSE 0 END) AS LEVEL2,
    SUM(CASE WHEN TEXT_LENGTH BETWEEN 21 AND 40 THEN 1 ELSE 0 END) AS LEVEL3,
    SUM(CASE WHEN TEXT_LENGTH BETWEEN 41 AND 100 THEN 1 ELSE 0 END) AS LEVEL4,
    SUM(CASE WHEN TEXT_LENGTH > 100 THEN 1 ELSE 0 END) AS LEVEL5
FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
WHERE RELEVANT_STATUS = 'RELEVANT';