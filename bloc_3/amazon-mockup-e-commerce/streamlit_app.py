import streamlit as st
import requests
import os

# URL de l'API - utilise localhost en local, backend dans Docker
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Configuration de la page
st.set_page_config(
    page_title="Amazon Reviews Analysis",
    page_icon="🛒",
    layout="wide"
)

st.title("🛒 Amazon Product Reviews - Relevance Analysis")

st.markdown("""
Browse products and view their **most relevant reviews** based on:
- ⭐ Rating score
- 📝 Text quality and length
- 🔑 Keyword relevance
- 📸 Presence of images
""")

st.divider()

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
        products_resp = requests.get(f"{API_URL}/snowflake/products?limit=100")
        products_resp.raise_for_status()
        all_products = products_resp.json()

        if all_products:
            st.success(f"✅ {len(all_products)} produits disponibles")

            # Add search filter
            search_filter = st.text_input("🔎 Filter products by name:", placeholder="Type to search...")

            # Filter products based on search
            if search_filter:
                filtered_products = [
                    p for p in all_products
                    if search_filter.lower() in p['product_name'].lower()
                ]
            else:
                filtered_products = all_products

            if filtered_products:
                st.info(f"📊 Showing {len(filtered_products)} product(s)")

                # Create dropdown with product names
                product_options = [
                    f"{p['product_name']} ({p.get('category', 'N/A')})"
                    for p in filtered_products
                ]

                selected_product_display = st.selectbox("📦 Select a Product:", product_options, key="product_selector")

                # Find the selected product
                selected_index = product_options.index(selected_product_display)
                selected_product = filtered_products[selected_index]
                selected_p_id = selected_product['p_id']
            else:
                st.warning("⚠️ No products match your search filter.")
    except requests.RequestException as e:
        st.error(f"❌ Could not load products from Snowflake: {str(e)}")
        st.info("💡 Please check that the backend API is running and Snowflake is accessible.")

else:  # Search by Product ID
    product_id_input = st.text_input(
        "📦 Enter Product ID:",
        placeholder="Ex: B076LFDBKD",
        help="Enter the exact Product ID (case-sensitive)"
    )

    if product_id_input:
        selected_p_id = product_id_input.strip()
        # We'll fetch product info from the reviews later

# Only proceed if we have a product ID
if selected_p_id:
    st.divider()

    # Display product info if we have it from browsing
    if selected_product:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.subheader(f"📦 {selected_product['product_name']}")
        with col2:
            st.metric("🏷️ Category", selected_product.get('category', 'N/A'))
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
        reviews_resp = requests.get(
            f"{API_URL}/snowflake/products/{selected_p_id}/reviews?limit={num_reviews}"
        )
        reviews_resp.raise_for_status()
        product_reviews = reviews_resp.json()

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
                        has_img = "Yes ✅" if review.get('has_image') else "No ❌"
                        st.metric("📸 Has Images", has_img)
                        has_orders = "Yes ✅" if review.get('has_orders') else "No ❌"
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
                        st.caption(f"✅ **Status:** {review.get('relevant_status', 'N/A')}")

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
            st.warning("⚠️ No relevant reviews found for this product.")

    except requests.RequestException as e:
        st.error(f"❌ Could not load reviews from Snowflake: {str(e)}")
