"""
Route layer untuk endpoint transaksi.
Menangani HTTP request dan response terkait transaksi penjualan.
"""
from pathlib import Path
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from schemas.transaction import Transaction, TransactionCreate
from services.transaction_service import TransactionService
from services.product_service import ProductService
from repositories.transaction_repository import TransactionRepository
from repositories.product_repository import ProductRepository


router = APIRouter(tags=["Transactions"])

# Setup templates
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Setup repositories dan services
DATA_DIR = BASE_DIR / "data"
product_repo = ProductRepository(str(DATA_DIR / "stok.txt"))
transaction_repo = TransactionRepository(str(DATA_DIR / "laporan_penjualan.txt"))
product_service = ProductService(product_repo)
transaction_service = TransactionService(transaction_repo, product_service)


# ============ HTML ROUTES (untuk browser) ============

@router.get("/", response_class=HTMLResponse, name="dashboard")
async def dashboard(request: Request):
    """
    Halaman dashboard utama (HTML).
    URL: GET /
    """
    stats = transaction_service.get_dashboard_stats()
    products = product_service.get_all_products()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": stats,
        "products": products[:10]  # Top 10 products for quick view
    })


@router.get("/pos", response_class=HTMLResponse, name="pos_page")
async def pos_page(request: Request):
    """
    Halaman Point of Sale / Kasir (HTML).
    URL: GET /pos
    """
    products = product_service.get_all_products()
    
    return templates.TemplateResponse("pos.html", {
        "request": request,
        "products": products
    })


@router.get("/transactions", response_class=HTMLResponse, name="transactions_list")
async def transactions_page(request: Request):
    """
    Halaman daftar transaksi / laporan (HTML).
    URL: GET /transactions
    """
    transactions = transaction_service.get_all_transactions()
    today_report = transaction_service.get_daily_report()
    
    return templates.TemplateResponse("transactions.html", {
        "request": request,
        "transactions": transactions,
        "today_report": today_report
    })


@router.get("/transactions/{transaction_id}", response_class=HTMLResponse, name="transaction_detail")
async def transaction_detail(request: Request, transaction_id: int):
    """
    Halaman detail transaksi (HTML).
    URL: GET /transactions/{id}
    """
    transaction = transaction_service.get_transaction_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    
    return templates.TemplateResponse("transaction_detail.html", {
        "request": request,
        "transaction": transaction
    })


# ============ API ROUTES (untuk AJAX / external) ============

@router.get("/api/transactions", response_model=List[Transaction], name="api_get_transactions")
async def api_get_transactions(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """
    API: Get semua transaksi (JSON).
    URL: GET /api/transactions
    Query: ?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD (optional)
    """
    return transaction_service.get_transactions_by_date(start_date, end_date)


@router.get("/api/transactions/today", response_model=List[Transaction], name="api_get_today_transactions")
async def api_get_today_transactions():
    """
    API: Get transaksi hari ini (JSON).
    URL: GET /api/transactions/today
    """
    return transaction_service.get_today_transactions()


@router.get("/api/transactions/{transaction_id}", response_model=Transaction, name="api_get_transaction")
async def api_get_transaction(transaction_id: int):
    """
    API: Get transaksi by ID (JSON).
    URL: GET /api/transactions/{id}
    """
    transaction = transaction_service.get_transaction_by_id(transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    return transaction


@router.post("/api/transactions", response_model=Transaction, name="api_create_transaction")
async def api_create_transaction(transaction_data: TransactionCreate):
    """
    API: Create transaksi baru (JSON).
    URL: POST /api/transactions
    Body: {
        "items": [
            {"product_id": 1, "qty": 2},
            {"product_id": 2, "qty": 1}
        ],
        "kasir": "admin"
    }
    
    Response: Transaction object dengan items dan total
    
    Notes:
    - Stok akan dikurangi otomatis
    - Validasi stok cukup dilakukan sebelum proses
    """
    try:
        return transaction_service.create_transaction(transaction_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/api/reports/daily", name="api_daily_report")
async def api_daily_report(target_date: Optional[date] = Query(None)):
    """
    API: Get laporan harian (JSON).
    URL: GET /api/reports/daily
    Query: ?target_date=YYYY-MM-DD (optional, default hari ini)
    """
    return transaction_service.get_daily_report(target_date)


@router.get("/api/dashboard/stats", name="api_dashboard_stats")
async def api_dashboard_stats():
    """
    API: Get statistik dashboard (JSON).
    URL: GET /api/dashboard/stats
    """
    return transaction_service.get_dashboard_stats()
