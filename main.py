import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import db, create_document, get_documents

app = FastAPI(title="Shoe Store API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductIn(BaseModel):
    title: str
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    category: str = "shoes"
    in_stock: bool = True
    image: Optional[str] = None
    brand: Optional[str] = None
    colors: Optional[List[str]] = None


class ProductOut(ProductIn):
    id: Optional[str] = None


@app.get("/")
def read_root():
    return {"message": "Shoe Store Backend Running"}


# Helper to seed database with sample shoes
SAMPLE_PRODUCTS = [
    {
        "title": "Air Nova Runner",
        "description": "Featherlight daily trainer with responsive foam midsole.",
        "price": 149.0,
        "category": "running",
        "in_stock": True,
        "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?q=80&w=1200&auto=format&fit=crop",
        "brand": "Nova",
        "colors": ["black", "volt", "white"],
    },
    {
        "title": "Atlas Court Pro",
        "description": "Premium leather court shoe with heritage styling.",
        "price": 179.0,
        "category": "lifestyle",
        "in_stock": True,
        "image": "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?q=80&w=1200&auto=format&fit=crop",
        "brand": "Atlas",
        "colors": ["white", "navy", "gold"],
    },
    {
        "title": "Storm Glide TR",
        "description": "Trail-ready outsole and water-repellent upper.",
        "price": 159.0,
        "category": "trail",
        "in_stock": True,
        "image": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?q=80&w=1200&auto=format&fit=crop",
        "brand": "Storm",
        "colors": ["slate", "orange", "charcoal"],
    },
    {
        "title": "Pulse React 2",
        "description": "Max cushioning with dynamic energy return.",
        "price": 199.0,
        "category": "running",
        "in_stock": True,
        "image": "https://images.unsplash.com/photo-1603808033192-6aa3c0d03ff2?q=80&w=1200&auto=format&fit=crop",
        "brand": "Pulse",
        "colors": ["crimson", "white", "black"],
    },
]


def ensure_seed():
    if db is None:
        return
    try:
        count = db["product"].count_documents({})
        if count == 0:
            for p in SAMPLE_PRODUCTS:
                create_document("product", p)
    except Exception:
        pass


@app.get("/api/products", response_model=List[ProductOut])
def list_products(limit: int = 20, category: Optional[str] = None):
    ensure_seed()
    filter_dict = {}
    if category:
        filter_dict["category"] = category
    try:
        items = get_documents("product", filter_dict=filter_dict, limit=limit)
    except Exception:
        # Fallback to in-memory sample if DB isn't available
        items = SAMPLE_PRODUCTS[:limit]
    # Normalize ids and fields
    out: List[ProductOut] = []
    for it in items:
        obj = {
            "id": str(it.get("_id", "")) or None,
            "title": it.get("title"),
            "description": it.get("description"),
            "price": float(it.get("price", 0)),
            "category": it.get("category", "shoes"),
            "in_stock": bool(it.get("in_stock", True)),
            "image": it.get("image"),
            "brand": it.get("brand"),
            "colors": it.get("colors"),
        }
        out.append(ProductOut(**obj))
    return out


@app.get("/api/products/featured", response_model=List[ProductOut])
def featured_products():
    ensure_seed()
    try:
        items = get_documents("product", limit=4)
    except Exception:
        items = SAMPLE_PRODUCTS[:4]
    out = []
    for it in items:
        obj = {
            "id": str(it.get("_id", "")) or None,
            "title": it.get("title"),
            "description": it.get("description"),
            "price": float(it.get("price", 0)),
            "category": it.get("category", "shoes"),
            "in_stock": bool(it.get("in_stock", True)),
            "image": it.get("image"),
            "brand": it.get("brand"),
            "colors": it.get("colors"),
        }
        out.append(ProductOut(**obj))
    return out


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
