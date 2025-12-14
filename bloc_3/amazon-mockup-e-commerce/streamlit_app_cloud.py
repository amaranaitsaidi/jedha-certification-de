import streamlit as st
import snowflake.connector
from typing import List, Dict

# Configuration de la page
st.set_page_config(
    page_title="Amazon Reviews Analysis",
    page_icon="🛒",
    layout="wide"
)

# Connexion à Snowflake en utilisant st.secrets (pour Streamlit Cloud)
# ou variables d'environnement (pour local)
@st.cache_resource
def get_snowflake_connection():
    """Crée une connexion à Snowflake avec cache"""
    try:
        # Sur Streamlit Cloud, utilise st.secrets
        if hasattr(st, 'secrets') and 'snowflake' in st.secrets:
            conn = snowflake.connector.connect(
                user=st.secrets.snowflake.user,
                password=st.secrets.snowflake.password,
                account=st.secrets.snowflake.account,
                warehouse=st.secrets.snowflake.warehouse,
                database=st.secrets.snowflake.database,
                schema=st.secrets.snowflake.schema,
                role=st.secrets.snowflake.role
            )
        else:
            # En local, utilise les variables d'environnement
            import os
            from dotenv import load_dotenv
            load_dotenv()

            conn = snowflake.connector.connect(
                user=os.getenv('SNOWFLAKE_USER'),
                password=os.getenv('SNOWFLAKE_PASSWORD'),
                account=os.getenv('SNOWFLAKE_ACCOUNT'),
                warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
                database=os.getenv('SNOWFLAKE_DATABASE'),
                schema=os.getenv('SNOWFLAKE_SCHEMA'),
                role=os.getenv('SNOWFLAKE_ROLE')
            )
        return conn
    except Exception as e:
        st.error(f" Erreur de connexion à Snowflake: {str(e)}")
        return None

def execute_query(query: str, params: dict = None) -> List[Dict]:
    """Exécute une requête Snowflake et retourne les résultats"""
    conn = get_snowflake_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        # Convertir en liste de dictionnaires
        result_dicts = []
        for row in results:
            result_dicts.append(dict(zip(columns, row)))

        cursor.close()
        return result_dicts
    except Exception as e:
        st.error(f" Erreur lors de l'exécution de la requête: {str(e)}")
        return []

def get_all_products(limit: int = 100) -> List[Dict]:
    """Récupère tous les produits depuis Snowflake"""
    query = """
        SELECT DISTINCT
            P_ID,
            PRODUCT_NAME,
            CATEGORY
        FROM AMAZON_REVIEWS.STAGING.REVIEW_RELEVANT
        ORDER BY PRODUCT_NAME
        LIMIT %(limit)s
    """
    return execute_query(query, {"limit": limit})

def get_product_reviews(p_id: str, limit: int = 10) -> List[Dict]:
    """Récupère les reviews pertinentes pour un produit"""
    query = """
        SELECT
            REVIEW_ID,
            BUYER_ID,
            P_ID,
            PRODUCT_NAME,
            CATEGORY,
            TITLE,
            DESCRIPTION,
            RATING,
            TEXT_LENGTH,
            HAS_IMAGE,
            HAS_ORDERS,
            TEXT_LENGTH_SCORE,
            IS_EXTREME_RATING,
            KEYWORD_SCORE,
            RELEVANCE_SCORE,
            CATEGORY_REVIEW,
            CONFIDENCE_SCORE,
            RELEVANT_STATUS,
            REVIEW_IMG
        FROM AMAZON_REVIEWS.STAGING.REVIEW_RELEVANT
        WHERE P_ID = %(p_id)s
          AND RELEVANT_STATUS = 'RELEVANT'
        ORDER BY RELEVANCE_SCORE DESC
        LIMIT %(limit)s
    """

    reviews = execute_query(query, {"p_id": p_id, "limit": limit})

    # Transformer les résultats pour correspondre au format attendu
    for review in reviews:
        # Gérer les images
        review_img = review.get("REVIEW_IMG")
        if review_img:
            if isinstance(review_img, str) and ',' in review_img:
                images = [img.strip() for img in review_img.split(',') if img.strip()]
            elif isinstance(review_img, str):
                images = [review_img] if review_img else []
            else:
                images = []
        else:
            images = []

        # Renommer les champs (Snowflake retourne en majuscules)
        review["review_id"] = review.pop("REVIEW_ID")
        review["buyer_id"] = review.pop("BUYER_ID")
        review["p_id"] = review.pop("P_ID")
        review["product_name"] = review.pop("PRODUCT_NAME")
        review["category"] = review.pop("CATEGORY")
        review["title"] = review.pop("TITLE")
        review["r_desc"] = review.pop("DESCRIPTION")
        review["rating"] = review.pop("RATING")
        review["text_length"] = review.pop("TEXT_LENGTH")
        review["has_image"] = bool(review.pop("HAS_IMAGE"))
        review["has_orders"] = bool(review.pop("HAS_ORDERS"))
        review["text_length_score"] = review.pop("TEXT_LENGTH_SCORE")
        review["is_extreme_rating"] = bool(review.pop("IS_EXTREME_RATING"))
        review["keyword_score"] = review.pop("KEYWORD_SCORE")
        review["relevance_score"] = review.pop("RELEVANCE_SCORE")
        review["category_review"] = review.pop("CATEGORY_REVIEW")
        review["confidence_score"] = review.pop("CONFIDENCE_SCORE")
        review["relevant_status"] = review.pop("RELEVANT_STATUS")
        review["images"] = images
        review.pop("REVIEW_IMG", None)

    return reviews

# ============================================
# INTERFACE STREAMLIT
# ============================================

st.title("🛒 Amazon Product Reviews - Relevance Analysis")

st.markdown("""
Browse products and view their **most relevant reviews** based on:
- ⭐ Rating score
- 📝 Text quality and length
- 🔑 Keyword relevance
- 📸 Presence of images
""")

st.divider()

# Vérifier la connexion Snowflake
conn = get_snowflake_connection()
if not conn:
    st.stop()

# Search method selection
search_method = st.radio(
    "🔍 How do you want to search?",
    ["Browse Products", "Search by Product ID"],
    horizontal=True
)

st.divider()

selected_p_id = None
selected_product = None

if search_method == "Browse Products":
    # Fetch all products from Snowflake
    try:
        all_products = get_all_products(limit=100)

        if all_products:
            st.success(f" {len(all_products)} produits disponibles")

            # Add search filter
            search_filter = st.text_input("🔎 Filter products by name:", placeholder="Type to search...")

            # Filter products based on search
            if search_filter:
                filtered_products = [
                    p for p in all_products
                    if search_filter.lower() in p['PRODUCT_NAME'].lower()
                ]
            else:
                filtered_products = all_products

            if filtered_products:
                st.info(f"📊 Showing {len(filtered_products)} product(s)")

                # Create dropdown with product names
                product_options = [
                    f"{p['PRODUCT_NAME']} ({p.get('CATEGORY', 'N/A')})"
                    for p in filtered_products
                ]

                selected_product_display = st.selectbox("📦 Select a Product:", product_options, key="product_selector")

                # Find the selected product
                selected_index = product_options.index(selected_product_display)
                selected_product = filtered_products[selected_index]
                selected_p_id = selected_product['P_ID']
            else:
                st.warning(" No products match your search filter.")
        else:
            st.warning(" No products found in Snowflake.")
    except Exception as e:
        st.error(f" Could not load products from Snowflake: {str(e)}")

else:  # Search by Product ID
    product_id_input = st.text_input(
        "📦 Enter Product ID:",
        placeholder="Ex: B076LFDBKD",
        help="Enter the exact Product ID (case-sensitive)"
    )

    if product_id_input:
        selected_p_id = product_id_input.strip()

# Only proceed if we have a product ID
if selected_p_id:
    st.divider()

    # Display product info if we have it from browsing
    if selected_product:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(f"📦 {selected_product['PRODUCT_NAME']}")
        with col2:
            st.metric("🏷️ Category", selected_product.get('CATEGORY', 'N/A'))
    else:
        # If searching by ID, show the ID
        st.subheader(f"📦 Product ID: {selected_p_id}")

    st.divider()

    # Display "Most Relevant Reviews"
    st.subheader("⭐ Most Relevant Reviews")

    # Number of reviews to display
    num_reviews = st.slider("Number of reviews to display:", min_value=5, max_value=20, value=10)

    # Get reviews for the selected product from Snowflake
    try:
        product_reviews = get_product_reviews(selected_p_id, limit=num_reviews)

        if product_reviews:
            st.info(f"📊 **{len(product_reviews)}** review(s) pertinente(s) trouvée(s)")

            for idx, review in enumerate(product_reviews, 1):
                rating_display = "⭐" * review['rating']
                relevance_score = review.get('relevance_score', 0.0)
                confidence_score = review.get('confidence_score', 0.0)

                # Titre de l'expander avec rating et relevance score
                with st.expander(
                    f"**Review #{idx}** | {rating_display} ({review['rating']}/5) - "
                    f"{review['title'] or '[No title]'} | "
                    f"🎯 Relevance: {relevance_score:.2f}",
                    expanded=(idx == 1)  # Only expand first review
                ):
                    # Description de la review
                    if review['r_desc']:
                        st.write("**📝 Description:**")
                        st.write(review['r_desc'])
                        st.caption(f"Longueur du texte: {review.get('text_length', 'N/A')} caractères")
                    else:
                        st.write("*No description provided*")

                    st.divider()

                    # Scores et métriques
                    st.write("**📊 Scores et Métriques:**")
                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        st.metric("⭐ Rating", f"{review['rating']}/5")
                        st.metric("🎯 Relevance Score", f"{relevance_score:.3f}")

                    with col2:
                        st.metric("🔍 Confidence Score", f"{confidence_score:.3f}")
                        st.metric("📏 Text Length Score", f"{review.get('text_length_score', 0):.3f}")

                    with col3:
                        st.metric("🔑 Keyword Score", f"{review.get('keyword_score', 0):.3f}")
                        extreme = "Yes" if review.get('is_extreme_rating') else "No"
                        st.metric("⚡ Extreme Rating", extreme)

                    with col4:
                        has_img = "Yes " if review.get('has_image') else "No ❌"
                        st.metric("📸 Has Images", has_img)
                        has_orders = "Yes " if review.get('has_orders') else "No ❌"
                        st.metric("🛍️ Has Orders", has_orders)

                    st.divider()

                    # Informations produit et catégorie
                    st.write("**ℹ️ Informations:**")
                    info_col1, info_col2, info_col3 = st.columns(3)

                    with info_col1:
                        st.caption(f"👤 **Buyer ID:** {review['buyer_id']}")
                        st.caption(f"📦 **Product ID:** {review['p_id']}")

                    with info_col2:
                        st.caption(f"🏷️ **Product:** {review.get('product_name', 'N/A')}")
                        st.caption(f"📂 **Category:** {review.get('category', 'N/A')}")

                    with info_col3:
                        st.caption(f"🏷️ **Review Category:** {review.get('category_review', 'N/A')}")
                        st.caption(f" **Status:** {review.get('relevant_status', 'N/A')}")

                    # Display review images
                    if review.get('images') and len(review['images']) > 0:
                        st.divider()
                        st.write("**📸 Review Images:**")

                        # Afficher les images en colonnes
                        num_images = len(review['images'])
                        if num_images <= 3:
                            cols = st.columns(num_images)
                            for i, img_url in enumerate(review['images']):
                                with cols[i]:
                                    st.image(img_url, caption=f"Image {i+1}", use_container_width=True)
                        else:
                            # Si plus de 3 images, afficher en grille 3x3
                            for i in range(0, num_images, 3):
                                cols = st.columns(3)
                                for j in range(3):
                                    if i + j < num_images:
                                        with cols[j]:
                                            st.image(
                                                review['images'][i+j],
                                                caption=f"Image {i+j+1}",
                                                use_container_width=True
                                            )

        else:
            st.warning(" No relevant reviews found for this product.")

    except Exception as e:
        st.error(f"Could not load reviews from Snowflake: {str(e)}")
        st.exception(e)  # Afficher la stack trace complète pour debug
