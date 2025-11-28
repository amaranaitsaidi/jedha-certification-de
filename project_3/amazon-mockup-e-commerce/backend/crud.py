import uuid
from sqlalchemy.orm import Session
from passlib.hash import bcrypt
import models, schemas
from datetime import datetime, date, timedelta

# Customer

def get_customer_by_email(db: Session, email: str):
    return db.query(models.Customer).filter(models.Customer.email == email).first()


def create_customer(db: Session, customer: schemas.CustomerCreate):
    hashed = bcrypt.hash(customer.pwd)
    db_obj = models.Customer(
        c_id=str(uuid.uuid4()),
        fname=customer.fname,
        lname=customer.lname,
        phone=customer.phone,
        email=customer.email,
        pwd=hashed,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# Product

def list_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

# Cart

def get_or_create_cart(db: Session, buyer_id: str):
    cart = db.query(models.Cart).filter(models.Cart.buyer_id == buyer_id).first()
    if not cart:
        cart = models.Cart(buyer_id=buyer_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def add_to_cart(db: Session, buyer_id: str, p_id: str, qty: int = 1):
    cart = get_or_create_cart(db, buyer_id)
    item = (
        db.query(models.CartItem)
        .filter(models.CartItem.cart_id == cart.cart_id, models.CartItem.p_id == p_id)
        .first()
    )
    if item:
        item.qty += qty
    else:
        item = models.CartItem(cart_id=cart.cart_id, p_id=p_id, qty=qty)
        db.add(item)
    cart.total_qty += qty
    # Recompute price
    prod = db.query(models.Product).get(p_id)
    cart.total_price += float(prod.price) * qty
    db.commit()
    db.refresh(cart)
    return cart

# Existing customer, product, cart logic omitted for brevity...

def checkout_cart(db: Session, buyer_id: str, payment_method: str):
    cart = db.query(models.Cart).filter(models.Cart.buyer_id == buyer_id).first()
    if not cart or cart.total_qty == 0:
        raise ValueError("Cart is empty or does not exist")
    # Create order
    order = models.Orders(
        buyer_id=buyer_id
    )
    db.add(order)
    db.flush()  # populate order_id
    # Create order items
    for item in cart.items:
        prod = db.query(models.Product).get(item.p_id)
        order_item = models.OrderItem(
            order_id=order.order_id,
            p_id=item.p_id,
            qty=item.qty,
            price_at_purchase=float(prod.price),
        )
        db.add(order_item)
        # Create shipment per item
        shipment = models.Shipment(
            order_id=order.order_id,
            p_id=item.p_id,
            carrier_id=None,
            shipment_type='NP',
            status='processing',
            est_delivery_date=(date.today() + timedelta(days=7)),
        )
        db.add(shipment)
    # Create payment record
    payment = models.Payment(
        payment_id=str(uuid.uuid4()),
        order_id=order.order_id,
        method=payment_method,
        status="completed",
    )
    db.add(payment)
    # Clear cart
    db.query(models.CartItem).filter(models.CartItem.cart_id == cart.cart_id).delete()
    cart.total_qty = 0
    cart.total_price = 0.0
    db.commit()
    db.refresh(order)
    return order


def get_order(db: Session, order_id: str):
    return db.query(models.Orders).filter(models.Orders.order_id == order_id).first()

def list_orders(db: Session, buyer_id: str):
    return db.query(models.Orders).filter(models.Orders.buyer_id == buyer_id).all()

def list_shipments(db: Session, order_id: int):
    return db.query(models.Shipment).filter(models.Shipment.order_id == order_id).all()

def get_product_images(db: Session, p_id: str):
    """
    Return all ProductImage rows for the given product ID.
    """
    return db.query(models.ProductImage).filter(models.ProductImage.p_id == p_id).all()

# ============================================
# FONCTIONS POUR LES REVIEWS
# ============================================

def get_most_relevant_reviews(db: Session, p_id: str, limit: int = 5):
    """
    Récupère les reviews les plus pertinentes pour un produit depuis la table reviews_score.
    Filtre uniquement les reviews avec relevant_status = 'RELEVANT'.

    Returns:
        List of reviews with confidence_score from reviews_score table
    """
    from sqlalchemy import text

    query = text("""
        SELECT
            rs.review_id,
            rs.buyer_id,
            rs.description,
            rs.title,
            rs.rating,
            rs.has_image,
            rs.confidence_score,
            rs.product_name
        FROM reviews_score rs
        WHERE rs.p_id = :p_id
          AND rs.relevant_status = 'RELEVANT'
        ORDER BY rs.confidence_score DESC
        LIMIT :limit
    """)

    result = db.execute(query, {"p_id": p_id, "limit": limit})
    rows = result.fetchall()

    reviews = []
    for row in rows:
        review_dict = {
            "review_id": row[0],
            "buyer_id": row[1],
            "r_desc": row[2],  # description from reviews_score
            "title": row[3],
            "rating": row[4],
            "has_image": bool(row[5]),
            "confidence_score": float(row[6]) if row[6] is not None else 0.0,
            "product_name": row[7]  # Optionnel, au cas où vous en avez besoin
        }
        reviews.append(review_dict)

    return reviews

def get_buyer_product_ids(db: Session, buyer_id: str):
    """
    Récupère la liste des Product IDs achetés par un buyer depuis reviews_score.

    Args:
        db: Session de base de données
        buyer_id: ID de l'acheteur

    Returns:
        Liste des product IDs uniques achetés par le buyer
    """
    from sqlalchemy import text

    query = text("""
        SELECT DISTINCT p_id, product_name
        FROM reviews_score
        WHERE buyer_id = :buyer_id
        ORDER BY p_id
    """)

    result = db.execute(query, {"buyer_id": buyer_id})
    rows = result.fetchall()

    products = []
    for row in rows:
        products.append({
            "p_id": row[0],
            "product_name": row[1]
        })

    return products

def get_buyer_reviews_for_product(db: Session, buyer_id: str, p_id: str):
    """
    Récupère les reviews d'un buyer spécifique pour un produit spécifique avec les images.
    Filtre uniquement les reviews avec relevant_status = 'RELEVANT'.

    Args:
        db: Session de base de données
        buyer_id: ID de l'acheteur
        p_id: ID du produit

    Returns:
        Liste des reviews du buyer pour ce produit avec leurs images
    """
    from sqlalchemy import text

    query = text("""
        SELECT
            rs.review_id,
            rs.buyer_id,
            rs.description,
            rs.title,
            rs.rating,
            rs.has_image,
            rs.confidence_score,
            rs.product_name
        FROM reviews_score rs
        WHERE rs.buyer_id = :buyer_id
          AND rs.p_id = :p_id
          AND rs.relevant_status = 'RELEVANT'
        ORDER BY rs.confidence_score DESC
    """)

    result = db.execute(query, {"buyer_id": buyer_id, "p_id": p_id})
    rows = result.fetchall()

    reviews = []
    for row in rows:
        review_id = row[0]

        # Get review images
        image_query = text("""
            SELECT review_img
            FROM review_images
            WHERE review_id = :review_id
        """)
        image_result = db.execute(image_query, {"review_id": review_id})
        image_rows = image_result.fetchall()
        images = [img[0] for img in image_rows]

        review_dict = {
            "review_id": review_id,
            "buyer_id": row[1],
            "r_desc": row[2],
            "title": row[3],
            "rating": row[4],
            "has_image": bool(row[5]),
            "confidence_score": float(row[6]) if row[6] is not None else 0.0,
            "product_name": row[7],
            "images": images
        }
        reviews.append(review_dict)

    return reviews
