-- Load data from CSV files into PostgreSQL tables
-- This script runs automatically when the container is first initialized

-- Disable triggers during data load
SET session_replication_role = replica;

-- Load carrier data
\echo 'Loading carrier data...'
COPY carrier(carrier_id, carrier_name)
FROM '/data/origin/carrier.csv'
DELIMITER ','
CSV HEADER;

-- Load category data
\echo 'Loading category data...'
COPY category(category_id, name, c_desc)
FROM '/data/origin/category.csv'
DELIMITER ','
CSV HEADER;

-- Load buyer data
\echo 'Loading buyer data...'
COPY buyer
FROM '/data/origin/buyer.csv'
DELIMITER ','
CSV HEADER;

-- Load customer data
\echo 'Loading customer data...'
COPY customer
FROM '/data/origin/customer.csv'
DELIMITER ','
CSV HEADER;

-- Load seller data
\echo 'Loading seller data...'
COPY seller
FROM '/data/origin/seller.csv'
DELIMITER ','
CSV HEADER;

-- Load product data
\echo 'Loading product data...'
COPY product
FROM '/data/origin/product.csv'
DELIMITER ','
CSV HEADER;

-- Load product_images data
\echo 'Loading product_images data...'
COPY product_images
FROM '/data/origin/product_images.csv'
DELIMITER ','
CSV HEADER;

-- Load seller_products data
\echo 'Loading seller_products data...'
COPY seller_products
FROM '/data/origin/seller_products.csv'
DELIMITER ','
CSV HEADER;

-- Load customer_payment data
\echo 'Loading customer_payment data...'
COPY customer_payment
FROM '/data/origin/customer_payment.csv'
DELIMITER ','
CSV HEADER;

-- Load customer_shipping data
\echo 'Loading customer_shipping data...'
COPY customer_shipping
FROM '/data/origin/customer_shipping.csv'
DELIMITER ','
CSV HEADER;

-- Load cart data
\echo 'Loading cart data...'
COPY cart
FROM '/data/origin/cart.csv'
DELIMITER ','
CSV HEADER;

-- Load cart_items data
\echo 'Loading cart_items data...'
COPY cart_items
FROM '/data/origin/cart_items.csv'
DELIMITER ','
CSV HEADER;

-- Load wishlist_item data
\echo 'Loading wishlist_item data...'
COPY wishlist_item
FROM '/data/origin/wishlist_item.csv'
DELIMITER ','
CSV HEADER;

-- Load discount data
\echo 'Loading discount data...'
COPY discount
FROM '/data/origin/discount.csv'
DELIMITER ','
CSV HEADER;

-- Load daily_deals data
\echo 'Loading daily_deals data...'
COPY daily_deals
FROM '/data/origin/daily_deals.csv'
DELIMITER ','
CSV HEADER;

-- Load subscription data
\echo 'Loading subscription data...'
COPY subscription
FROM '/data/origin/subscription.csv'
DELIMITER ','
CSV HEADER;

-- Load payment_details data
\echo 'Loading payment_details data...'
COPY payment_details
FROM '/data/origin/payment_details.csv'
DELIMITER ','
CSV HEADER;

-- Load orders data
\echo 'Loading orders data...'
COPY orders
FROM '/data/origin/orders.csv'
DELIMITER ','
CSV HEADER;

-- Load shipment data
\echo 'Loading shipment data...'
COPY shipment
FROM '/data/origin/shipment.csv'
DELIMITER ','
CSV HEADER;

-- Load shipping_details data
\echo 'Loading shipping_details data...'
COPY shipping_details
FROM '/data/origin/shipping_details.csv'
DELIMITER ','
CSV HEADER;

-- Load returns data
\echo 'Loading returns data...'
COPY returns
FROM '/data/origin/returns.csv'
DELIMITER ','
CSV HEADER;

-- Load review data
\echo 'Loading review data...'
COPY review
FROM '/data/origin/review.csv'
DELIMITER ','
CSV HEADER;

-- Load review_images data
\echo 'Loading review_images data...'
COPY review_images
FROM '/data/origin/review_images.csv'
DELIMITER ','
CSV HEADER;

-- Load product_reviews data
\echo 'Loading product_reviews data...'
COPY product_reviews
FROM '/data/origin/product_reviews.csv'
DELIMITER ','
CSV HEADER;

-- Load seller_reviews data
\echo 'Loading seller_reviews data...'
COPY seller_reviews
FROM '/data/origin/seller_reviews.csv'
DELIMITER ','
CSV HEADER;

-- Re-enable triggers
SET session_replication_role = DEFAULT;

\echo 'Data loading completed successfully!'
