import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Numeric, ForeignKey, DateTime, Float, Date
)
from sqlalchemy.orm import relationship
from database import Base

class Customer(Base):
    __tablename__ = "customer"
    c_id = Column(String, primary_key=True, index=True)  # Utilise les IDs existants du Projet 2
    fname = Column(String, nullable=False)
    lname = Column(String, nullable=False)
    phone = Column(String(10), unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    pwd = Column(String, nullable=False)
    order = relationship("Orders", back_populates="customer")

class Product(Base):
    __tablename__ = "product"
    p_id = Column(String, primary_key=True, index=True)  # Utilise les IDs existants du Projet 2 (ex: B00001234)
    p_name = Column(String, nullable=False)
    p_desc = Column(String, nullable=False)
    price = Column(Numeric, nullable=False)
    qty = Column(Integer, default=0, nullable=False)
    category_id = Column(Integer, ForeignKey("category.category_id"), nullable=True)
    order_items = relationship("OrderItem", back_populates="product")
    cart_items = relationship("CartItem", back_populates="product")
    shipment = relationship("Shipment", back_populates="product")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete")
    reviews = relationship("ProductReview", back_populates="product")

class ProductImage(Base):
    __tablename__ = "product_images"
    p_id    = Column(String(10), ForeignKey("product.p_id", ondelete="CASCADE"), primary_key=True)
    p_image = Column(String(100),                 primary_key=True)

    # optional back‑ref
    product = relationship("Product", back_populates="images")

class Cart(Base):
    __tablename__ = "cart"
    cart_id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(String, ForeignKey("customer.c_id"))
    total_qty = Column(Integer, default=0, nullable=False)
    total_price = Column(Float, default=0.0, nullable=False)
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

class CartItem(Base):
    __tablename__ = "cart_items"
    cart_id = Column(Integer, ForeignKey("cart.cart_id"), primary_key=True)
    p_id = Column(String, ForeignKey("product.p_id"), primary_key=True)
    qty = Column(Integer, default=1, nullable=False)
    cart = relationship("Cart", back_populates="items")
    product = relationship("Product", back_populates="cart_items")

class Orders(Base):
    __tablename__ = "orders"
    order_id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(String, ForeignKey("customer.c_id"))
    order_date = Column(DateTime, default=datetime.utcnow)
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", uselist=False, back_populates="order")
    shipment = relationship("Shipment", uselist=False, back_populates="order")
    customer = relationship("Customer", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    order_id = Column(Integer, ForeignKey("orders.order_id"), primary_key=True)
    p_id = Column(String, ForeignKey("product.p_id"), primary_key=True)
    qty = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)
    order = relationship("Orders", back_populates="items")
    product = relationship("Product", back_populates="order_items")

class Payment(Base):
    __tablename__ = "payment"
    payment_id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    method = Column(String, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    order = relationship("Orders", back_populates="payment")

class Carrier(Base):
    __tablename__ = "carrier"
    carrier_id = Column(Integer, primary_key=True, index=True)
    carrier_name = Column(String, nullable=False)  # Correspond au schéma Projet 2
    shipment = relationship("Shipment", back_populates="carrier")

class Shipment(Base):
    __tablename__ = "shipment"
    shipping_id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"))
    p_id = Column(String(10), ForeignKey("product.p_id"))
    carrier_id = Column(Integer, ForeignKey("carrier.carrier_id"))
    shipment_type = Column(String(2), default='NP')
    status = Column(String(10), nullable=False)
    est_delivery_date = Column(Date, nullable=True)
    actual_delivery_date = Column(Date, nullable=True)
    order = relationship("Orders", back_populates="shipment")
    product = relationship("Product", back_populates="shipment")
    carrier = relationship("Carrier", back_populates="shipment")

# ============================================
# MODÈLES POUR LES REVIEWS (Projet 2)
# ============================================

class Category(Base):
    __tablename__ = "category"
    category_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(30), nullable=True)
    c_desc = Column(String(20), nullable=True)

class Review(Base):
    __tablename__ = "review"
    review_id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(String(40), nullable=True)
    r_desc = Column(String(20000), nullable=True)  # Description de la review
    title = Column(String(300), nullable=True)
    rating = Column(Integer, nullable=False)  # 1-5
    seller_product_flag = Column(String(1), nullable=True)  # 'S' ou 'P'
    product_reviews = relationship("ProductReview", back_populates="review")
    images = relationship("ReviewImage", back_populates="review")

class ProductReview(Base):
    __tablename__ = "product_reviews"
    p_id = Column(String(10), ForeignKey("product.p_id"), primary_key=True)
    review_id = Column(Integer, ForeignKey("review.review_id"), primary_key=True)
    product = relationship("Product", back_populates="reviews")
    review = relationship("Review", back_populates="product_reviews")

class ReviewImage(Base):
    __tablename__ = "review_images"
    review_id = Column(Integer, ForeignKey("review.review_id"), primary_key=True)
    review_img = Column(String(200), primary_key=True)
    review = relationship("Review", back_populates="images")
