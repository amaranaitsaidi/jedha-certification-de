import streamlit as st
import requests

API_URL = "http://backend:8000"
st.title("E‑commerce Store")

# Authentication placeholder
buyer_id = st.text_input("Enter your Buyer ID:")

if buyer_id:
    # NEW SECTION: Show products purchased by this buyer
    try:
        products_resp = requests.get(f"{API_URL}/buyers/{buyer_id}/products")
        products_resp.raise_for_status()
        buyer_products = products_resp.json()

        if buyer_products:
            # Create dropdown with product IDs
            product_options = [f"{p['p_id']} - {p['product_name']}" for p in buyer_products]
            selected_buyer_product = st.selectbox("Select a Product ID:", product_options)

            # Extract selected product ID
            selected_p_id = selected_buyer_product.split(" - ")[0]

            # Display "Most Relevant Reviews" AFTER product selection
            st.subheader("⭐ Most Relevant Reviews")

            # Display reviews from THIS BUYER ONLY for the selected product
            try:
                # Get reviews filtered by buyer_id and p_id
                reviews_resp = requests.get(
                    f"{API_URL}/buyers/{buyer_id}/products/{selected_p_id}/reviews"
                )
                reviews_resp.raise_for_status()
                buyer_reviews = reviews_resp.json()

                if buyer_reviews:
                    for review in buyer_reviews:
                        rating_display = f"{review['rating']}/5"
                        confidence_score = review.get('confidence_score', 0.0)

                        with st.expander(
                            f"{rating_display} - {review['title'] or '[No title]'} "
                            f"(Confidence: {confidence_score:.2f})"
                        ):
                            if review['r_desc']:
                                st.write(review['r_desc'])
                            else:
                                st.write("No description provided")

                            st.caption(f"Buyer: {review['buyer_id']}")

                            # Display review images
                            if review.get('images') and len(review['images']) > 0:
                                st.caption("Has images")
                                st.image(
                                    review['images'],
                                    caption=[f"Review image {i+1}" for i in range(len(review['images']))],
                                    width=200
                                )
                else:
                    st.info("No reviews available for this product.")

            except requests.RequestException as e:
                st.warning(f"Could not load reviews: {str(e)}")

    except requests.RequestException as e:
        st.warning(f"Could not load buyer products: {str(e)}")

    st.divider()

    # ORIGINAL E-COMMERCE SECTION
    # Fetch products
    products = requests.get(f"{API_URL}/products/").json()
    options = [f"{p['p_name']} — ${p['price']}" for p in products]
    choice = st.selectbox("Select a product to add to cart", options)

    # Determine selected product
    idx = options.index(choice)
    selected = products[idx]

    # Fetch and display product images
    try:
        imgs_resp = requests.get(
            f"{API_URL}/products/{selected['p_id']}/images"
        )
        imgs_resp.raise_for_status()
        images_data = imgs_resp.json()
        # images_data may be list of URLs or list of dicts with 'p_image'
        image_urls = []
        for item in images_data:
            if isinstance(item, str):
                image_urls.append(item)
            elif isinstance(item, dict) and 'p_image' in item:
                image_urls.append(item['p_image'])
        if image_urls:
            st.image(
                image_urls,
                caption=[f"image {i+1}" for i in range(len(image_urls))],
                width=200,
            )
    except requests.RequestException:
        st.error("Failed to load product images.")

    qty = st.number_input("Quantity", min_value=1, value=1)
    if st.button("Add to cart"):
        idx = options.index(choice)
        p_id = products[idx]['p_id']
        requests.post(f"{API_URL}/cart/{buyer_id}", params={"p_id": p_id, "qty": qty})
        st.success(f"Added {qty}×{products[idx]['p_name']} to cart!")

    # Display Cart
    st.header("Your Cart")
    cart = requests.get(f"{API_URL}/cart/{buyer_id}").json()
    if cart['total_qty'] > 0:
        for item in cart['items']:
            st.write(f"{item['p_id']}: Qty {item['qty']}")
        st.write(f"**Total items:** {cart['total_qty']}")
        st.write(f"**Total price:** ${cart['total_price']:.2f}")

        # Checkout
        st.subheader("Checkout")
        payment_method = st.selectbox(
            "Choose payment method", ["Credit Card", "PayPal", "Bank Transfer"]
        )
        if st.button("Buy Now"):
            order = requests.post(
                f"{API_URL}/checkout/{buyer_id}", params={"payment_method": payment_method}
            ).json()
            # compute total from returned items
            total_price = sum(item["qty"] * item["price_at_purchase"] for item in order["items"])
            st.success(f"Order {order['order_id']} placed! Total: ${total_price:.2f}")
            # Fetch shipments
            shipments = requests.get(f"{API_URL}/shipments/{order['order_id']}").json()
            st.subheader("Shipments")
            for s in shipments:
                st.write(f"Item {s['p_id']} via carrier {s['carrier_id']} - Status: {s['status']}")
                if s.get('est_delivery_date'):
                    st.write(f"Estimated Delivery: {s['est_delivery_date']}")
    else:
        st.info("Your cart is empty.")
