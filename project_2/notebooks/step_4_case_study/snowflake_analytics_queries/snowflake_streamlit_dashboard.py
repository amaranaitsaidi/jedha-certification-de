import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark.context import get_active_session

# -------------------------------------------------------------------
# Initialisation
# -------------------------------------------------------------------
st.set_page_config(page_title="Amazon Reviews Analytics", layout="wide")

st.title("📊 Amazon Reviews Analytics Dashboard")
st.markdown("Analyse enrichie des avis Amazon : pertinence, NLP, catégories et KPIs personnalisés.")

session = get_active_session()

# -------------------------------------------------------------------
# Utils Snowflake
# -------------------------------------------------------------------
@st.cache_data
def run_query(query: str) -> pd.DataFrame:
    return session.sql(query).to_pandas()

# -------------------------------------------------------------------
# Fonction d'affichage avec option camembert
# -------------------------------------------------------------------
def show_section(title, description):
    st.markdown("---")
    st.subheader(title)
    st.markdown(description)

def pie_chart(df, label_col, value_col):
    chart = (
        alt.Chart(df)
        .mark_arc()
        .encode(
            theta=alt.Theta(value_col, type="quantitative"),
            color=alt.Color(label_col, type="nominal"),
            tooltip=[label_col, value_col]
        )
        .properties(width=350, height=350)
    )
    return chart

# -------------------------------------------------------------------
# SECTION : KPIs GLOBAUX
# -------------------------------------------------------------------
show_section("KPIs Globaux", "Vue d’ensemble : ")

df_kpi = run_query("""
    SELECT
        COUNT(*) AS TOTAL_REVIEWS,
        SUM(CASE WHEN RELEVANT_STATUS='RELEVANT' THEN 1 ELSE 0 END) AS NB_RELEVANT,
        ROUND(AVG(RATING), 2) AS AVG_RATING,
        ROUND(AVG(RELEVANCE_SCORE), 2) AS AVG_RELEVANCE_SCORE,
        ROUND(AVG(CONFIDENCE_SCORE), 2) AS AVG_CONFIDENCE_SCORE,
        ROUND(AVG(TEXT_LENGTH), 2) AS AVG_TEXT_LENGTH
    FROM DB_AMZ.ANALYTICS.REVIEW_RELEVANT
""")

c1, c2, c3, c4, c5,c6 = st.columns(6)
c1.metric("Avis totaux", f"{df_kpi.TOTAL_REVIEWS[0]:,}")
c2.metric("Avis pertinents", f"{df_kpi.NB_RELEVANT[0]:,}")
c3.metric("Rating moyen", df_kpi.AVG_RATING[0])
c4.metric("Score Pondération moyen", df_kpi.AVG_RELEVANCE_SCORE[0])
c5.metric("Score Confidence moyen", df_kpi.AVG_CONFIDENCE_SCORE[0])
c6.metric("Longueur texte moyenne", df_kpi.AVG_TEXT_LENGTH[0])

# -------------------------------------------------------------------
# ANALYSE 1 — Distribution des statuts (Camembert)
# -------------------------------------------------------------------
show_section("Distribution du statut de pertinence",
             "Répartition RELEVANT / IRRELEVANT.")

df_status = run_query("""
    SELECT
      RELEVANT_STATUS,
      COUNT(*) AS NB_REVIEWS
    FROM DB_AMZ.ANALYTICS.REVIEW_RELEVANT
    GROUP BY RELEVANT_STATUS
""")

c1, c2 = st.columns([1.2,1])

with c1:
    st.dataframe(df_status, use_container_width=True)

with c2:
    st.altair_chart(pie_chart(df_status, "RELEVANT_STATUS", "NB_REVIEWS"))

# -------------------------------------------------------------------
# ANALYSE 3 — Par catégorie
# -------------------------------------------------------------------
show_section("Pertinence par catégorie produit",
             "Identifier les catégories produits les plus pertinentes.")

df_cat = run_query("""
    SELECT
      CATEGORY,
      COUNT(*) AS NB_REVIEWS,
      SUM(CASE WHEN RELEVANT_STATUS='RELEVANT' THEN 1 ELSE 0 END) AS NB_RELEVANT,
      ROUND(SUM(CASE WHEN RELEVANT_STATUS='RELEVANT' THEN 1 ELSE 0 END) / COUNT(*), 3) AS POURCENTAGE_RELEVANT,
      ROUND(AVG(RATING),2) AS AVG_RATING
    FROM DB_AMZ.ANALYTICS.REVIEW_RELEVANT
    GROUP BY CATEGORY
    ORDER BY NB_REVIEWS DESC
""")

st.dataframe(df_cat, use_container_width=True)

bar = (
    alt.Chart(df_cat)
    .mark_bar()
    .encode(
        x="CATEGORY:N",
        y=alt.Y("POURCENTAGE_RELEVANT:Q", title="% pertinence"),
        color="CATEGORY:N"
    )
    .properties(width="container")
)

st.altair_chart(bar, use_container_width=True)


# -------------------------------------------------------------------
# KPI 1 — Top 10 produits avec le plus d'avis pertinents
# -------------------------------------------------------------------
show_section("KPI 1 — Top 20 produits avec le plus d'avis pertinents",
             "Produits générant le plus d'avis classés comme RELEVANT.")

df_kpi1 = run_query("""
    SELECT
        PRODUCT_NAME,
        COUNT(*) AS NB_RELEVANT_REVIEWS
    FROM DB_AMZ.ANALYTICS.REVIEW_RELEVANT
    WHERE RELEVANT_STATUS = 'RELEVANT'
    GROUP BY PRODUCT_NAME
    ORDER BY NB_RELEVANT_REVIEWS DESC
    LIMIT 20;
""")

st.dataframe(df_kpi1, use_container_width=True)

chart_kpi1 = (
    alt.Chart(df_kpi1)
    .mark_bar()
    .encode(
        x="PRODUCT_NAME:N",
        y="NB_RELEVANT_REVIEWS:Q",
        tooltip=["PRODUCT_NAME", "NB_RELEVANT_REVIEWS"]
    )
)
st.altair_chart(chart_kpi1, use_container_width=True)

# -------------------------------------------------------------------
# KPI 2 — Répartition par catégorie (avis pertinents uniquement)
# -------------------------------------------------------------------
show_section("KPI 2 — Répartition par catégorie review",
             "Distribution des avis pertinents selon la catégorie review.")

df_kpi2 = run_query("""
    SELECT
        CATEGORY_REVIEW,
        COUNT(*) AS NB_RELEVANT
    FROM DB_AMZ.ANALYTICS.REVIEW_RELEVANT
    WHERE RELEVANT_STATUS = 'RELEVANT'
    GROUP BY CATEGORY_REVIEW
    ORDER BY NB_RELEVANT DESC;
""")

c1, c2 = st.columns([1.3, 1])

with c1:
    st.dataframe(df_kpi2, use_container_width=True)

with c2:
    st.altair_chart(
        pie_chart(df_kpi2, "CATEGORY_REVIEW", "NB_RELEVANT"),
        use_container_width=True
    )

# -------------------------------------------------------------------
# KPI 3 — Top 10 clients selon le nombre d'avis pertinents
# -------------------------------------------------------------------
show_section("KPI 3 — Top 20 clients (avis pertinents)",
             "Liste des acheteurs ayant laissé le plus d'avis pertinents. Cette indicateur pour voir si les mêmes clients laissent beaucoup d'avis.")

df_kpi3 = run_query("""
    SELECT
        BUYER_ID,
        COUNT(*) AS NB_RELEVANT_REVIEWS
    FROM DB_AMZ.ANALYTICS.REVIEW_RELEVANT
    WHERE RELEVANT_STATUS = 'RELEVANT'
    GROUP BY BUYER_ID
    ORDER BY NB_RELEVANT_REVIEWS DESC
    LIMIT 20;
""")

st.dataframe(df_kpi3, use_container_width=True)

chart_kpi3 = (
    alt.Chart(df_kpi3)
    .mark_bar()
    .encode(
        x="BUYER_ID:N",
        y="NB_RELEVANT_REVIEWS:Q",
        tooltip=["BUYER_ID", "NB_RELEVANT_REVIEWS"]
    )
)

# -------------------------------------------------------------------
# KPI 4 — Produits avec le moins d'avis
# -------------------------------------------------------------------
show_section("KPI 4 — 20 produits avec le moins d'avis",
             "Les produits qui apparaissent le moins dans les reviews (low data).")

df_kpi4 = run_query("""
    SELECT
        PRODUCT_NAME,
        COUNT(*) AS NB_REVIEWS,
        CATEGORY_REVIEW
    FROM DB_AMZ.ANALYTICS.REVIEW_RELEVANT
    GROUP BY PRODUCT_NAME,CATEGORY_REVIEW
    ORDER BY NB_REVIEWS ASC
    LIMIT 20;
""")

st.dataframe(df_kpi4, use_container_width=True)

chart_kpi4 = (
    alt.Chart(df_kpi4)
    .mark_bar()
    .encode(
        x="PRODUCT_NAME:N",
        y="NB_REVIEWS:Q",
        tooltip=["PRODUCT_NAME", "NB_REVIEWS"]
    )
)
st.altair_chart(chart_kpi4, use_container_width=True)

# -------------------------------------------------------------------
# KPI 5 — Top 20 clients avec volume + pertinence
# -------------------------------------------------------------------
show_section("KPI 5 — Top 20 clients les plus actifs",
             "Nombre total d'avis + ratio de pertinence pour chaque client.")

df_kpi_m1 = run_query("""
    SELECT
        BUYER_ID,
        COUNT(*) AS TOTAL_REVIEWS,
        SUM(CASE WHEN RELEVANT_STATUS = 'RELEVANT' THEN 1 ELSE 0 END) AS NB_RELEVANT,
        ROUND(
            SUM(CASE WHEN RELEVANT_STATUS = 'RELEVANT' THEN 1 ELSE 0 END) 
            / COUNT(*), 3
        ) AS PCT_RELEVANT
    FROM DB_AMZ.ANALYTICS.REVIEW_RELEVANT
    GROUP BY BUYER_ID
    ORDER BY TOTAL_REVIEWS DESC
    LIMIT 20;
""")

st.dataframe(df_kpi_m1, use_container_width=True)

# -------------------------------------------------------------------
# KPI METIER 6 — Produits les plus commentés
# -------------------------------------------------------------------
show_section("KPI 6 — Produits les plus commentés",
             "Indique les produits générant le plus d'engagement client.")

df_kpi_m4 = run_query("""
    SELECT
        PRODUCT_NAME,
        COUNT(*) AS NB_REVIEWS
    FROM DB_AMZ.ANALYTICS.REVIEW_RELEVANT
    GROUP BY PRODUCT_NAME
    ORDER BY NB_REVIEWS DESC
    LIMIT 20;
""")

st.dataframe(df_kpi_m4, use_container_width=True)

# -------------------------------------------------------------------
# KPI METIER 7 — Les avis catégorisés customer service or support
# -------------------------------------------------------------------
show_section("KPI 7 — Les avis catégories -Customer service or support-",
             "Indique les produits générant le plus d'engagement client.")

df_kpi_m5 = run_query("""
    SELECT
        PRODUCT_NAME,
        RATING,
        RELEVANCE_SCORE,
        CONFIDENCE_SCORE,
        DESCRIPTION
        FROM DB_AMZ.ANALYTICS.REVIEW_RELEVANT
        WHERE CATEGORY_REVIEW = 'customer service or support'
        ORDER BY RATING ASC
;
""")

st.dataframe(df_kpi_m5, use_container_width=True)

