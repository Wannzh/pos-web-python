"""
Service layer untuk business logic produk.
Memisahkan business logic dari akses data (repository).
"""
from typing import List, Optional

from schemas.product import Product, ProductCreate, ProductUpdate
from repositories.product_repository import ProductRepository


class ProductService:
    """
    Service untuk business logic terkait produk.
    Menggunakan ProductRepository untuk akses data.
    """
    
    def __init__(self, repository: ProductRepository):
        """
        Initialize service dengan repository.
        
        Args:
            repository: ProductRepository instance
        """
        self.repository = repository
    
    def get_all_products(self) -> List[Product]:
        """
        Ambil semua produk.
        
        Returns:
            List semua produk diurutkan berdasarkan nama
        """
        products = self.repository.get_all()
        return sorted(products, key=lambda p: p.nama.lower())
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Cari produk berdasarkan ID.
        
        Args:
            product_id: ID produk
            
        Returns:
            Product jika ditemukan
        """
        return self.repository.get_by_id(product_id)
    
    def create_product(self, product_data: ProductCreate) -> Product:
        """
        Buat produk baru dengan validasi.
        
        Args:
            product_data: Data produk baru
            
        Returns:
            Product yang baru dibuat
            
        Raises:
            ValueError: Jika nama produk sudah ada
        """
        # Check for duplicate name
        existing = self.repository.get_all()
        for p in existing:
            if p.nama.lower() == product_data.nama.lower():
                raise ValueError(f"Produk dengan nama '{product_data.nama}' sudah ada")
        
        return self.repository.create(product_data)
    
    def update_product(self, product_id: int, product_data: ProductUpdate) -> Optional[Product]:
        """
        Update produk.
        
        Args:
            product_id: ID produk
            product_data: Data baru
            
        Returns:
            Product yang diupdate, None jika tidak ditemukan
            
        Raises:
            ValueError: Jika nama baru sudah digunakan produk lain
        """
        # Check for duplicate name if updating nama
        if product_data.nama:
            existing = self.repository.get_all()
            for p in existing:
                if p.id != product_id and p.nama.lower() == product_data.nama.lower():
                    raise ValueError(f"Produk dengan nama '{product_data.nama}' sudah ada")
        
        return self.repository.update(product_id, product_data)
    
    def delete_product(self, product_id: int) -> bool:
        """
        Hapus produk.
        
        Args:
            product_id: ID produk
            
        Returns:
            True jika berhasil dihapus
        """
        return self.repository.delete(product_id)
    
    def check_stock_availability(self, product_id: int, quantity: int) -> bool:
        """
        Cek apakah stok cukup.
        
        Args:
            product_id: ID produk
            quantity: Jumlah yang dibutuhkan
            
        Returns:
            True jika stok cukup
        """
        product = self.repository.get_by_id(product_id)
        if not product:
            return False
        return product.stok >= quantity
    
    def reduce_stock(self, product_id: int, quantity: int) -> Optional[Product]:
        """
        Kurangi stok produk (setelah penjualan).
        
        Args:
            product_id: ID produk
            quantity: Jumlah yang dikurangi
            
        Returns:
            Product dengan stok baru
            
        Raises:
            ValueError: Jika stok tidak cukup
        """
        return self.repository.update_stock(product_id, -quantity)
    
    def add_stock(self, product_id: int, quantity: int) -> Optional[Product]:
        """
        Tambah stok produk.
        
        Args:
            product_id: ID produk
            quantity: Jumlah yang ditambah
            
        Returns:
            Product dengan stok baru
        """
        return self.repository.update_stock(product_id, quantity)
    
    def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """
        Ambil produk dengan stok rendah.
        
        Args:
            threshold: Batas stok rendah
            
        Returns:
            List produk dengan stok dibawah threshold
        """
        products = self.repository.get_all()
        return [p for p in products if p.stok <= threshold]
    
    def search_products(self, keyword: str) -> List[Product]:
        """
        Cari produk berdasarkan nama.
        
        Args:
            keyword: Kata kunci pencarian
            
        Returns:
            List produk yang cocok
        """
        products = self.repository.get_all()
        keyword_lower = keyword.lower()
        return [p for p in products if keyword_lower in p.nama.lower()]
