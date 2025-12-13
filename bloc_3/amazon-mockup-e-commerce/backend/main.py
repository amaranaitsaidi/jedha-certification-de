import uvicorn
from fastapi import FastAPI, Depends, HTTPException, APIRouter
from typing import List, Optional
from sqlalchemy.orm import Session
import models, schemas, crud
from database import engine, SessionLocal
import snowflake_crud

# Rendre PostgreSQL optionnel - ne crash pas si la DB n'est pas disponible
try:
    models.Base.metadata.create_all(bind=engine)
    POSTGRES_AVAILABLE = True
except Exception as e:
    print(f"WARNING: PostgreSQL not available: {e}")
    print("INFO: Only Snowflake endpoints will work")
    POSTGRES_AVAILABLE = False

app = FastAPI(title="Mock E‑commerce API")

def get_db():
    if not POSTGRES_AVAILABLE:
        raise HTTPException(status_code=503, detail="PostgreSQL database is not available")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_db_optional():
    """Optional DB dependency that returns None if PostgreSQL is not available"""
    if not POSTGRES_AVAILABLE:
        yield None
    else:
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

@app.post("/customers/", response_model=schemas.Customer)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    if crud.get_customer_by_email(db, email=customer.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_customer(db, customer)

@app.get("/products/", response_model=List[schemas.Product])
def read_products(skip: int = 0, limit: int = 100, db: Optional[Session] = Depends(get_db_optional)):
    if db is None:
        raise HTTPException(status_code=503, detail="PostgreSQL not available. Please use Snowflake endpoints.")
    return crud.list_products(db, skip=skip, limit=limit)

@app.get("/cart/{buyer_id}", response_model=schemas.Cart)
def read_cart(buyer_id: str, db: Session = Depends(get_db)):
    cart = crud.get_or_create_cart(db, buyer_id)
    return cart

@app.post("/cart/{buyer_id}", response_model=schemas.Cart)
def add_cart_item(buyer_id: str, p_id: str, qty: int = 1, db: Session = Depends(get_db)):
    return crud.add_to_cart(db, buyer_id, p_id, qty)

@app.post("/checkout/{buyer_id}", response_model=schemas.Orders)
def checkout(buyer_id: str, payment_method: str, db: Session = Depends(get_db)):
    try:
        return crud.checkout_cart(db, buyer_id, payment_method)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/orders/{buyer_id}", response_model=List[schemas.Orders])
def get_orders(buyer_id: str, db: Session = Depends(get_db)):
    return crud.list_orders(db, buyer_id)

@app.get("/shipments/{order_id}", response_model=List[schemas.Shipment])
def get_shipments(order_id: int, db: Session = Depends(get_db)):
    shipments = crud.list_shipments(db, order_id)
    if not shipments:
        raise HTTPException(status_code=404, detail="No shipments found for this order")
    return shipments

@app.get(
    "/products/{p_id}/images",
    response_model=List[str],
    summary="List image URLs for a product",
)
def read_product_images(p_id: str, db: Optional[Session] = Depends(get_db_optional)):
    """
    Fetch all image URLs for product `p_id` from the product_images table.
    """
    if db is None:
        raise HTTPException(status_code=503, detail="PostgreSQL not available. Please use Snowflake endpoints.")
    imgs = crud.get_product_images(db, p_id)
    if not imgs:
        # Retourner une liste vide au lieu d'une erreur 404
        return []
    return [img.p_image for img in imgs]

@app.get(
    "/products/{p_id}/reviews/relevant",
    response_model=List[schemas.Review],
    summary="Get most relevant reviews for a product",
)
def get_relevant_reviews(p_id: str, limit: int = 5, db: Optional[Session] = Depends(get_db_optional)):
    """
    Récupère les reviews les plus pertinentes pour un produit.

    L'algorithme de pertinence prend en compte:
    - Le rating de la review (40%)
    - La longueur de la description (30%)
    - La présence d'images (30%)

    Args:
        p_id: ID du produit
        limit: Nombre maximum de reviews à retourner (par défaut: 5)

    Returns:
        Liste des reviews triées par pertinence décroissante
    """
    if db is None:
        raise HTTPException(status_code=503, detail="PostgreSQL not available. Please use Snowflake endpoints.")
    reviews = crud.get_most_relevant_reviews(db, p_id, limit)
    if not reviews:
        return []  # Retourner une liste vide au lieu d'une erreur 404
    return reviews

@app.get(
    "/buyers/{buyer_id}/products",
    response_model=List[schemas.BuyerProduct],
    summary="Get list of product IDs purchased by a buyer",
)
def get_buyer_products(buyer_id: str, db: Optional[Session] = Depends(get_db_optional)):
    """
    Récupère la liste des Product IDs achetés par un buyer.

    Args:
        buyer_id: ID de l'acheteur

    Returns:
        Liste des product IDs uniques achetés par le buyer
    """
    if db is None:
        raise HTTPException(status_code=503, detail="PostgreSQL not available. Please use Snowflake endpoints.")
    products = crud.get_buyer_product_ids(db, buyer_id)
    return products

@app.get(
    "/buyers/{buyer_id}/products/{p_id}/reviews",
    response_model=List[schemas.Review],
    summary="Get reviews from a specific buyer for a specific product",
)
def get_buyer_product_reviews(buyer_id: str, p_id: str, db: Optional[Session] = Depends(get_db_optional)):
    """
    Récupère les reviews d'un buyer spécifique pour un produit spécifique.

    Args:
        buyer_id: ID de l'acheteur
        p_id: ID du produit

    Returns:
        Liste des reviews du buyer pour ce produit
    """
    if db is None:
        raise HTTPException(status_code=503, detail="PostgreSQL not available. Please use Snowflake endpoints.")
    reviews = crud.get_buyer_reviews_for_product(db, buyer_id, p_id)
    return reviews


# ============================================
# ENDPOINTS SNOWFLAKE
# ============================================

@app.get(
    "/snowflake/products",
    response_model=List[schemas.BuyerProduct],
    summary="Get all products from Snowflake",
)
def get_all_products_snowflake(limit: int = 100):
    """
    Récupère la liste de tous les produits disponibles depuis Snowflake.

    Args:
        limit: Nombre maximum de produits à retourner (par défaut: 100)

    Returns:
        Liste des produits uniques
    """
    try:
        products = snowflake_crud.get_all_products_from_snowflake(limit)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Snowflake error: {str(e)}")


@app.get(
    "/snowflake/products/{p_id}/reviews",
    response_model=List[schemas.Review],
    summary="Get relevant reviews for a product from Snowflake",
)
def get_product_reviews_snowflake(p_id: str, limit: int = 10):
    """
    Récupère les reviews pertinentes (RELEVANT_STATUS = 'RELEVANT')
    pour un produit depuis Snowflake (tous les buyers).

    Args:
        p_id: ID du produit
        limit: Nombre maximum de reviews à retourner (par défaut: 10)

    Returns:
        Liste des reviews avec relevance_score et images
    """
    try:
        reviews = snowflake_crud.get_product_reviews_from_snowflake(p_id, limit)
        return reviews
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Snowflake error: {str(e)}")


@app.get(
    "/snowflake/buyers/{buyer_id}/products",
    response_model=List[schemas.BuyerProduct],
    summary="Get products purchased by a buyer from Snowflake",
)
def get_buyer_products_snowflake(buyer_id: str):
    """
    Récupère la liste des produits achetés par un buyer depuis Snowflake.

    Args:
        buyer_id: ID de l'acheteur

    Returns:
        Liste des produits uniques achetés par le buyer
    """
    try:
        products = snowflake_crud.get_buyer_products_from_snowflake(buyer_id)
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Snowflake error: {str(e)}")


@app.get(
    "/snowflake/buyers/{buyer_id}/products/{p_id}/reviews",
    response_model=List[schemas.Review],
    summary="Get relevant reviews from Snowflake for a buyer and product",
)
def get_relevant_reviews_snowflake(buyer_id: str, p_id: str):
    """
    Récupère les reviews pertinentes (RELEVANT_STATUS = 'RELEVANT')
    d'un buyer pour un produit depuis Snowflake.

    Args:
        buyer_id: ID de l'acheteur
        p_id: ID du produit

    Returns:
        Liste des reviews avec relevance_score et images
    """
    try:
        reviews = snowflake_crud.get_relevant_reviews_from_snowflake(buyer_id, p_id)
        return reviews
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Snowflake error: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
