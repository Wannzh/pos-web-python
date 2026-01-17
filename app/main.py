"""
POS System - Main Application Entry Point
==========================================

Aplikasi Point of Sale berbasis web dengan arsitektur berlapis.
Menggunakan FastAPI sebagai framework dan file .txt sebagai data storage.

Cara menjalankan:
    cd app
    uvicorn main:app --reload --port 8000

Endpoint:
    - Dashboard: http://localhost:8000/
    - Kasir/POS: http://localhost:8000/pos
    - Produk: http://localhost:8000/products
    - Transaksi: http://localhost:8000/transactions
    - API Docs: http://localhost:8000/docs
"""
import sys
from pathlib import Path

# Add app directory to path for imports
APP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(APP_DIR))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from routes.product_routes import router as product_router
from routes.transaction_routes import router as transaction_router


# ============ Application Setup ============

app = FastAPI(
    title="POS System",
    description="Point of Sale Web Application dengan File-Based Storage",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files (CSS, JS, images)
static_dir = APP_DIR / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))


# ============ Include Routers ============

app.include_router(product_router)
app.include_router(transaction_router)


# ============ Startup Event ============

@app.on_event("startup")
async def startup_event():
    """
    Dijalankan saat aplikasi startup.
    Memastikan folder dan file data exists.
    """
    data_dir = APP_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Ensure stok.txt exists
    stok_file = data_dir / "stok.txt"
    if not stok_file.exists():
        with open(stok_file, "w", encoding="utf-8") as f:
            f.write("id|nama|harga|stok|created_at\n")
        print(f"Created: {stok_file}")
    
    # Ensure laporan_penjualan.txt exists
    laporan_file = data_dir / "laporan_penjualan.txt"
    if not laporan_file.exists():
        with open(laporan_file, "w", encoding="utf-8") as f:
            f.write("id|tanggal|items|total|kasir\n")
        print(f"Created: {laporan_file}")
    
    print("=" * 50)
    print("🛒 POS System Started!")
    print("=" * 50)
    print(f"📁 Data directory: {data_dir}")
    print(f"📦 Stok file: {stok_file}")
    print(f"📋 Laporan file: {laporan_file}")
    print("=" * 50)
    print("🌐 Open http://localhost:8000 in your browser")
    print("📚 API Docs: http://localhost:8000/docs")
    print("=" * 50)


# ============ Health Check ============

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns status aplikasi dan info storage.
    """
    data_dir = APP_DIR / "data"
    stok_file = data_dir / "stok.txt"
    laporan_file = data_dir / "laporan_penjualan.txt"
    
    return {
        "status": "healthy",
        "storage": {
            "type": "file-based (.txt)",
            "stok_file": str(stok_file),
            "stok_exists": stok_file.exists(),
            "laporan_file": str(laporan_file),
            "laporan_exists": laporan_file.exists()
        }
    }


# ============ Run with Python ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
