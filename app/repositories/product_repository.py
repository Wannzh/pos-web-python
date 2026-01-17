"""
Repository layer untuk akses data produk (stok.txt).
Bertanggung jawab untuk semua operasi I/O file terkait produk.
"""
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from schemas.product import Product, ProductCreate, ProductUpdate
from utils.file_lock import safe_read_file, safe_write_file, safe_read_file_with_header


class ProductRepository:
    """
    Repository untuk operasi CRUD produk pada file stok.txt.
    Format file: id|nama|harga|stok|created_at
    """
    
    # Header untuk file stok.txt
    HEADER = "id|nama|harga|stok|created_at"
    
    def __init__(self, file_path: str):
        """
        Initialize repository dengan path ke file stok.
        
        Args:
            file_path: Path absolut ke file stok.txt
        """
        self.file_path = file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Pastikan file exists dengan header."""
        path = Path(self.file_path)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            safe_write_file(self.file_path, self.HEADER, [])
    
    def get_all(self) -> List[Product]:
        """
        Ambil semua produk dari file.
        
        Returns:
            List of Product objects
        """
        lines = safe_read_file(self.file_path)
        products = []
        
        for line in lines:
            try:
                product = Product.from_line(line)
                products.append(product)
            except ValueError as e:
                # Log error tapi jangan gagalkan seluruh operasi
                print(f"Warning: Skipping invalid line - {e}")
        
        return products
    
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """
        Cari produk berdasarkan ID.
        
        Args:
            product_id: ID produk yang dicari
            
        Returns:
            Product jika ditemukan, None jika tidak
        """
        products = self.get_all()
        for product in products:
            if product.id == product_id:
                return product
        return None
    
    def create(self, product_data: ProductCreate) -> Product:
        """
        Tambah produk baru ke file.
        
        Args:
            product_data: Data produk baru
            
        Returns:
            Product yang baru dibuat dengan ID
        """
        products = self.get_all()
        
        # Generate new ID (max ID + 1)
        new_id = 1
        if products:
            new_id = max(p.id for p in products) + 1
        
        # Create new product
        new_product = Product(
            id=new_id,
            nama=product_data.nama,
            harga=product_data.harga,
            stok=product_data.stok,
            created_at=datetime.now()
        )
        
        # Append to file
        products.append(new_product)
        lines = [p.to_line() for p in products]
        safe_write_file(self.file_path, self.HEADER, lines)
        
        return new_product
    
    def update(self, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        """
        Update produk berdasarkan ID.
        
        Args:
            product_id: ID produk yang akan diupdate
            product_data: Data baru (field yang None tidak diubah)
            
        Returns:
            Product yang sudah diupdate, None jika tidak ditemukan
        """
        products = self.get_all()
        updated_product = None
        
        for i, product in enumerate(products):
            if product.id == product_id:
                # Update only provided fields
                if product_data.nama is not None:
                    product.nama = product_data.nama
                if product_data.harga is not None:
                    product.harga = product_data.harga
                if product_data.stok is not None:
                    product.stok = product_data.stok
                
                products[i] = product
                updated_product = product
                break
        
        if updated_product:
            lines = [p.to_line() for p in products]
            safe_write_file(self.file_path, self.HEADER, lines)
        
        return updated_product
    
    def delete(self, product_id: int) -> bool:
        """
        Hapus produk berdasarkan ID.
        
        Args:
            product_id: ID produk yang akan dihapus
            
        Returns:
            True jika berhasil dihapus, False jika tidak ditemukan
        """
        products = self.get_all()
        original_count = len(products)
        
        products = [p for p in products if p.id != product_id]
        
        if len(products) < original_count:
            lines = [p.to_line() for p in products]
            safe_write_file(self.file_path, self.HEADER, lines)
            return True
        
        return False
    
    def update_stock(self, product_id: int, quantity_change: int) -> Optional[Product]:
        """
        Update stok produk (tambah atau kurang).
        
        Args:
            product_id: ID produk
            quantity_change: Perubahan stok (positif = tambah, negatif = kurang)
            
        Returns:
            Product yang sudah diupdate, None jika gagal
            
        Raises:
            ValueError: Jika stok menjadi negatif
        """
        products = self.get_all()
        updated_product = None
        
        for i, product in enumerate(products):
            if product.id == product_id:
                new_stock = product.stok + quantity_change
                if new_stock < 0:
                    raise ValueError(f"Stok tidak cukup untuk produk {product.nama}")
                
                product.stok = new_stock
                products[i] = product
                updated_product = product
                break
        
        if updated_product:
            lines = [p.to_line() for p in products]
            safe_write_file(self.file_path, self.HEADER, lines)
        
        return updated_product
