"""
Route layer untuk endpoint produk.
Menangani HTTP request dan response terkait produk.
"""
from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from schemas.product import Product, ProductCreate, ProductUpdate
from services.product_service import ProductService
from repositories.product_repository import ProductRepository


router = APIRouter(tags=["Products"])

# Setup templates
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Setup repository dan service
DATA_DIR = BASE_DIR / "data"
product_repo = ProductRepository(str(DATA_DIR / "stok.txt"))
product_service = ProductService(product_repo)


# ============ HTML ROUTES (untuk browser) ============

@router.get("/products", response_class=HTMLResponse, name="products_list")
async def products_page(request: Request):
    """
    Halaman daftar produk (HTML).
    URL: GET /products
    """
    products = product_service.get_all_products()
    low_stock = product_service.get_low_stock_products()
    
    return templates.TemplateResponse("products.html", {
        "request": request,
        "products": products,
        "low_stock_count": len(low_stock),
        "total_products": len(products)
    })


@router.get("/products/add", response_class=HTMLResponse, name="add_product_form")
async def add_product_page(request: Request):
    """
    Halaman form tambah produk baru (HTML).
    URL: GET /products/add
    """
    return templates.TemplateResponse("add_product.html", {
        "request": request
    })


@router.post("/products/add", response_class=HTMLResponse, name="add_product_submit")
async def add_product_submit(
    request: Request,
    nama: str = Form(...),
    harga: int = Form(...),
    stok: int = Form(...)
):
    """
    Handle form submit tambah produk.
    URL: POST /products/add
    """
    try:
        product_data = ProductCreate(nama=nama, harga=harga, stok=stok)
        product_service.create_product(product_data)
        return RedirectResponse(url="/products", status_code=303)
    except ValueError as e:
        return templates.TemplateResponse("add_product.html", {
            "request": request,
            "error": str(e),
            "nama": nama,
            "harga": harga,
            "stok": stok
        })


@router.get("/products/{product_id}/edit", response_class=HTMLResponse, name="edit_product_form")
async def edit_product_page(request: Request, product_id: int):
    """
    Halaman edit produk (HTML).
    URL: GET /products/{id}/edit
    """
    product = product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    
    return templates.TemplateResponse("edit_product.html", {
        "request": request,
        "product": product
    })


@router.post("/products/{product_id}/edit", response_class=HTMLResponse, name="edit_product_submit")
async def edit_product_submit(
    request: Request,
    product_id: int,
    nama: str = Form(...),
    harga: int = Form(...),
    stok: int = Form(...)
):
    """
    Handle form submit edit produk.
    URL: POST /products/{id}/edit
    """
    try:
        product_data = ProductUpdate(nama=nama, harga=harga, stok=stok)
        updated = product_service.update_product(product_id, product_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
        return RedirectResponse(url="/products", status_code=303)
    except ValueError as e:
        product = product_service.get_product_by_id(product_id)
        return templates.TemplateResponse("edit_product.html", {
            "request": request,
            "product": product,
            "error": str(e)
        })


@router.post("/products/{product_id}/delete", name="delete_product")
async def delete_product(product_id: int):
    """
    Hapus produk.
    URL: POST /products/{id}/delete
    """
    deleted = product_service.delete_product(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    return RedirectResponse(url="/products", status_code=303)


# ============ API ROUTES (untuk AJAX / external) ============

@router.get("/api/products", response_model=List[Product], name="api_get_products")
async def api_get_products(search: str = None):
    """
    API: Get semua produk (JSON).
    URL: GET /api/products
    Query: ?search=keyword (optional)
    """
    if search:
        return product_service.search_products(search)
    return product_service.get_all_products()


@router.get("/api/products/{product_id}", response_model=Product, name="api_get_product")
async def api_get_product(product_id: int):
    """
    API: Get produk by ID (JSON).
    URL: GET /api/products/{id}
    """
    product = product_service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    return product


@router.post("/api/products", response_model=Product, name="api_create_product")
async def api_create_product(product_data: ProductCreate):
    """
    API: Create produk baru (JSON).
    URL: POST /api/products
    Body: {"nama": "...", "harga": ..., "stok": ...}
    """
    try:
        return product_service.create_product(product_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/api/products/{product_id}", response_model=Product, name="api_update_product")
async def api_update_product(product_id: int, product_data: ProductUpdate):
    """
    API: Update produk (JSON).
    URL: PUT /api/products/{id}
    Body: {"nama": "...", "harga": ..., "stok": ...}
    """
    try:
        updated = product_service.update_product(product_id, product_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/api/products/{product_id}", name="api_delete_product")
async def api_delete_product(product_id: int):
    """
    API: Delete produk (JSON).
    URL: DELETE /api/products/{id}
    """
    deleted = product_service.delete_product(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    return {"message": "Produk berhasil dihapus", "id": product_id}
