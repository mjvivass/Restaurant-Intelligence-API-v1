from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.db.session import engine, Base
from app.models import user_model, restaurant_model, product_model, sale_model

# Routers
from app.routers import auth, restaurants, products, sales

# Excepciones personalizadas
from app.core.exceptions import (
    NotAuthorizedException,
    ProductNotFoundException,
    InsufficientStockException
)

app = FastAPI()

# =========================
# CREAR TABLAS
# =========================
Base.metadata.create_all(bind=engine)

# =========================
# MANEJO GLOBAL DE ERRORES
# =========================

@app.exception_handler(NotAuthorizedException)
def not_authorized_handler(request, exc):
    return JSONResponse(
        status_code=403,
        content={"error": "Not authorized"}
    )


@app.exception_handler(ProductNotFoundException)
def product_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Product not found"}
    )


@app.exception_handler(InsufficientStockException)
def insufficient_stock_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": "Insufficient stock"}
    )


# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# RUTA RAÍZ
# =========================
@app.get("/")
def root():
    return {"message": "API Restaurant conectada a SQL Server 🚀"}


# =========================
# INCLUIR ROUTERS
# =========================
app.include_router(auth.router, tags=["Auth"])
app.include_router(restaurants.router)
app.include_router(products.router)
app.include_router(sales.router)