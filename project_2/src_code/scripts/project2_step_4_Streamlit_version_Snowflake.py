import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark.context import get_active_session

# -------------------------------------------------------------------
# Initialisation
# -------------------------------------------------------------------
st.set_page_config(page_title="Amazon Reviews Analytics", layout="wide")
st.title("📊 Amazon Reviews Analytics Dashboard")
st.markdown("Analyse de la pertinence des avis utilisateurs selon les scores NLP et les règles métiers.")

# Récupération de la session active Snowflake
session = get_active_session()

# -------------------------------------------------------------------
# Fonction pour exécuter une requête SQL et renvoyer un DataFrame Pandas
# -------------------------------------------------------------------
@st.cache_data
def run_query(query: str) -> pd.DataFrame:
    return session.sql(query).to_pandas()

# -------------------------------------------------------------------
# Fonction d’affichage standardisée
# -------------------------------------------------------------------
def show_analysis(title, description, query, chart_config=None):
    st.markdown("---")
    st.subheader(title)
    st.markdown(description)

    df = run_query(query)
    st.dataframe(df, use_container_width=True)

    if chart_config:
        chart = alt.Chart(df).mark_bar().encode(**chart_config).properties(width="container")
        st.altair_chart(chart, use_container_width=True)

# -------------------------------------------------------------------
# ANALYSES
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# ANALYSE 1 — Distribution des statuts pertinence
# -------------------------------------------------------------------
show_analysis(
    "Analyse 1 — Distribution du statut de pertinence",
    "_Objectif : Observer la proportion d’avis classés RELEVANT / IRRELEVANT._",
    """
    SELECT
      RELEVANT_STATUS,
      COUNT(*) AS NB_REVIEWS,
      ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS POURCENTAGE
    FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
    GROUP BY RELEVANT_STATUS;
    """,
    chart_config=dict(
        x="RELEVANT_STATUS:N",
        y="NB_REVIEWS:Q",
        color="RELEVANT_STATUS:N"
    )
)

# -------------------------------------------------------------------
# ANALYSE 2 — Scores & Longueur
# -------------------------------------------------------------------
show_analysis(
    "Analyse 2 — Scores et longueur des textes",
    """_Objectif : Vérifier si RELEVANT correspond à des scores et longueurs plus élevés ou inversement._""",
    """
    SELECT
        RELEVANT_STATUS,
        AVG(RELEVANCE_SCORE) AS AVG_RELEVANCE_SCORE,
        AVG(CONFIDENCE_SCORE) AS AVG_CONFIDENCE_SCORE,
        AVG(TEXT_LENGTH_SCORE) AS AVG_LENGTH_SCORE
    FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
    GROUP BY RELEVANT_STATUS;
    """
)


# -------------------------------------------------------------------
# ANALYSE 3 — Par catégorie
# -------------------------------------------------------------------
show_analysis(
    "Analyse 3 — Pertinence par catégorie",
    "_Objectif : Identifier les catégories les plus qualitatives ou problématiques._",
    """
    SELECT
      CATEGORY,
      COUNT(*) AS NB_REVIEWS,
      SUM(CASE WHEN RELEVANT_STATUS = 'RELEVANT' THEN 1 ELSE 0 END) AS NB_RELEVANT,
      ROUND(SUM(CASE WHEN RELEVANT_STATUS = 'RELEVANT' THEN 1 ELSE 0 END) / COUNT(*), 2) AS POURCENTAGE_RELEVANT,
      AVG(RATING) AS AVG_RATING
    FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
    GROUP BY CATEGORY
    ORDER BY NB_REVIEWS DESC;
    """,
    chart_config=dict(
        x="CATEGORY:N",
        y=alt.Y("POURCENTAGE_RELEVANT:Q", title="% d'avis pertinents"),
        color="CATEGORY:N"
    )
)


# -------------------------------------------------------------------
# ANALYSE 4 — Par produit
# -------------------------------------------------------------------
show_analysis(
    "Analyse 4 — Pertinence par produit",
    "_Objectif : Identifier les produits à très fort / faible taux de pertinence._",
    """
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
    """
)


# -------------------------------------------------------------------
# ANALYSE 5 — Longueur texte
# -------------------------------------------------------------------
show_analysis(
    "Analyse 5 — Longueur des textes",
    "_Objectif : Vérifier que les textes RELEVANT sont en moyenne plus longs._",
    """
    SELECT
      RELEVANT_STATUS,
      AVG(TEXT_LENGTH) AS AVG_LEN,
      MIN(TEXT_LENGTH) AS MIN_LEN,
      MAX(TEXT_LENGTH) AS MAX_LEN
    FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
    WHERE TEXT_LENGTH > 0
    GROUP BY RELEVANT_STATUS;
    """,
    chart_config=dict(
        x=alt.X("RELEVANT_STATUS:N", title="Statut de pertinence"),
        y=alt.Y("AVG_LEN:Q",title="Longueur moyenne de l'avis"),
        color="RELEVANT_STATUS:N"
    )
)


# -------------------------------------------------------------------
# ANALYSE 6 — Impact rating extrême
# -------------------------------------------------------------------
show_analysis(
    "Analyse 6 — Impact des ratings extrêmes",
    "_Objectif : Détecter un possible biais lié aux notes très hautes ou très basses._",
    """
    SELECT
      IS_EXTREME_RATING,
      RELEVANT_STATUS,
      COUNT(*) AS NB
    FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
    GROUP BY IS_EXTREME_RATING, RELEVANT_STATUS
    ORDER BY IS_EXTREME_RATING;
    """,
    chart_config=dict(
        x=alt.X("IS_EXTREME_RATING:O", title="Rating extrême"),
        y=alt.Y("NB:Q" , title="Nombre d'avis"),
        color="RELEVANT_STATUS:N"
    )
)


# -------------------------------------------------------------------
# ANALYSE 7 — Keywords
# -------------------------------------------------------------------
show_analysis(
    "Analyse 7 — Influence des mots-clés",
    "_Objectif : Voir si KEYWORD_SCORE aide réellement la classification._",
    """
    SELECT
      RELEVANT_STATUS,
      AVG(KEYWORD_SCORE) AS AVG_KEYWORD
    FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
    GROUP BY RELEVANT_STATUS;
    """,
    chart_config=dict(
        x=alt.X("RELEVANT_STATUS:N", title="Statut de pertinence"),
        y=alt.Y("AVG_KEYWORD:Q", title="Score mots-clés moyen"),
        color="RELEVANT_STATUS:N"
    )
)


# -------------------------------------------------------------------
# ANALYSE 8 — Pertinence selon le rating
# -------------------------------------------------------------------
show_analysis(
    "Analyse 8 — Distribution pertinence selon rating",
    "_Objectif : Voir si certains ratings génèrent plus d’avis pertinents._",
    """
        SELECT
            RATING,
            RELEVANT_STATUS,
            COUNT(*) AS NB_REVIEWS,
            ROUND(COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY RATING), 2) AS PCT_PER_STATUS
        FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
        GROUP BY RATING, RELEVANT_STATUS
        ORDER BY RATING, RELEVANT_STATUS;
    """,
    chart_config=dict(
        x=alt.X("RATING:O", title="Rating"),
        y=alt.Y("PCT_PER_STATUS:Q", title="% d'avis par statut"),
        color="RELEVANT_STATUS:N"
    )
)


# -------------------------------------------------------------------
# ANALYSE 9 — Présence image
# -------------------------------------------------------------------
show_analysis(
    "Analyse 9 — Impact de la présence d’image",
    "_Objectif : Voir si les avis avec image sont plus pertinents._",
    """
    SELECT
        HAS_IMAGE,
        RELEVANT_STATUS,
        COUNT(*) AS NB_REVIEWS,
        ROUND(COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY HAS_IMAGE), 2) AS PCT_PER_STATUS
    FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
    GROUP BY HAS_IMAGE, RELEVANT_STATUS
    ORDER BY HAS_IMAGE, RELEVANT_STATUS;
    """,
    chart_config=dict(
        x=alt.X("HAS_IMAGE:O", title="Présence d'image"),
        y=alt.Y("PCT_PER_STATUS:Q", title="% d'avis par statut"),
        color="RELEVANT_STATUS:N"
    )
)


# -------------------------------------------------------------------
# ANALYSE 10 — A déjà commandé
# -------------------------------------------------------------------
show_analysis(
    "Analyse 10 — Impact du fait d'avoir déjà commandé",
    "_Objectif : Vérifier si les 'verified purchases' produisent des avis plus pertinents._",
    """
    SELECT
        HAS_ORDERS,
        RELEVANT_STATUS,
        COUNT(*) AS NB_REVIEWS,
        ROUND(COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY HAS_ORDERS), 2) AS PCT_PER_STATUS
    FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
    GROUP BY HAS_ORDERS, RELEVANT_STATUS
    ORDER BY HAS_ORDERS, RELEVANT_STATUS;
    """,
    chart_config=dict(
        x=alt.X("HAS_ORDERS:O", title="A déjà commandé"),
        y=alt.Y("PCT_PER_STATUS:Q", title="% d'avis par statut"),
        color="RELEVANT_STATUS:N"
    )
)

# -------------------------------------------------------------------
# ANALYSE 11 — Distribution pertinence selon longueur de texte
# -------------------------------------------------------------------
show_analysis(
    "Analyse 11 — Distribution pertinence selon longueur de texte",
    "_Objectif : Vérifier sur les avis pertinents la longueur du texte._  \n" \
    "_LEVEL0 -> entre 0 et 5 caractères._  \n" \
    "_LEVEL1 -> entre 6 et 10 caractères._  \n" \
    "_LEVEL2 -> entre 11 et 20 caractères._  \n" \
    "_LEVEL3 -> entre 21 et 40 caractères._  \n" \
    "_LEVEL4 -> entre 41 et 100 caractères._  \n" \
    "_LEVEL5 -> plus de 100 caractères._  \n",
    """
    SELECT
    COUNT(*) AS NB_RELEVANT,
    SUM(CASE WHEN TEXT_LENGTH BETWEEN 0 AND 5 THEN 1 ELSE 0 END) AS LEVEL0,
    SUM(CASE WHEN TEXT_LENGTH BETWEEN 6 AND 10 THEN 1 ELSE 0 END) AS LEVEL1,
    SUM(CASE WHEN TEXT_LENGTH BETWEEN 11 AND 20 THEN 1 ELSE 0 END) AS LEVEL2,
    SUM(CASE WHEN TEXT_LENGTH BETWEEN 21 AND 40 THEN 1 ELSE 0 END) AS LEVEL3,
    SUM(CASE WHEN TEXT_LENGTH BETWEEN 41 AND 100 THEN 1 ELSE 0 END) AS LEVEL4,
    SUM(CASE WHEN TEXT_LENGTH > 100 THEN 1 ELSE 0 END) AS LEVEL5
FROM DB_AMZ.REVIEW.REVIEW_RELEVANT
WHERE RELEVANT_STATUS = 'RELEVANT'
ORDER BY NB_RELEVANT ASC;
    """
)