"""
Service layer untuk business logic transaksi penjualan.
Mengkoordinasikan antara product dan transaction repository.
"""
from datetime import date
from typing import List, Optional

from schemas.transaction import Transaction, TransactionItem, TransactionCreate
from repositories.transaction_repository import TransactionRepository
from services.product_service import ProductService


class TransactionService:
    """
    Service untuk business logic terkait transaksi.
    Menghubungkan ProductService dan TransactionRepository.
    """
    
    def __init__(
        self, 
        transaction_repository: TransactionRepository,
        product_service: ProductService
    ):
        """
        Initialize service dengan dependencies.
        
        Args:
            transaction_repository: TransactionRepository instance
            product_service: ProductService instance
        """
        self.transaction_repo = transaction_repository
        self.product_service = product_service
    
    def create_transaction(self, transaction_data: TransactionCreate) -> Transaction:
        """
        Proses transaksi penjualan lengkap.
        
        Alur:
        1. Validasi semua item ada dan stok cukup
        2. Hitung total
        3. Kurangi stok untuk setiap item
        4. Simpan transaksi
        
        Args:
            transaction_data: Data transaksi dari request
            
        Returns:
            Transaction yang berhasil dibuat
            
        Raises:
            ValueError: Jika produk tidak ditemukan atau stok tidak cukup
        """
        items: List[TransactionItem] = []
        total = 0
        
        # Step 1: Validate all items and calculate
        for item_data in transaction_data.items:
            product_id = item_data.get("product_id")
            qty = item_data.get("qty", 1)
            
            # Get product
            product = self.product_service.get_product_by_id(product_id)
            if not product:
                raise ValueError(f"Produk dengan ID {product_id} tidak ditemukan")
            
            # Check stock
            if not self.product_service.check_stock_availability(product_id, qty):
                raise ValueError(
                    f"Stok produk '{product.nama}' tidak cukup. "
                    f"Tersedia: {product.stok}, Diminta: {qty}"
                )
            
            # Calculate subtotal
            subtotal = product.harga * qty
            total += subtotal
            
            # Create transaction item
            items.append(TransactionItem(
                product_id=product_id,
                nama=product.nama,
                qty=qty,
                subtotal=subtotal
            ))
        
        # Step 2: Reduce stock for all items
        for item in items:
            self.product_service.reduce_stock(item.product_id, item.qty)
        
        # Step 3: Save transaction
        transaction = self.transaction_repo.create(
            items=items,
            total=total,
            kasir=transaction_data.kasir
        )
        
        return transaction
    
    def get_all_transactions(self) -> List[Transaction]:
        """
        Ambil semua transaksi.
        
        Returns:
            List semua transaksi, terbaru dulu
        """
        transactions = self.transaction_repo.get_all()
        return sorted(transactions, key=lambda t: t.tanggal, reverse=True)
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """
        Cari transaksi berdasarkan ID.
        
        Args:
            transaction_id: ID transaksi
            
        Returns:
            Transaction jika ditemukan
        """
        return self.transaction_repo.get_by_id(transaction_id)
    
    def get_today_transactions(self) -> List[Transaction]:
        """
        Ambil transaksi hari ini.
        
        Returns:
            List transaksi hari ini
        """
        return self.transaction_repo.get_today_transactions()
    
    def get_transactions_by_date(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Transaction]:
        """
        Filter transaksi berdasarkan tanggal.
        
        Args:
            start_date: Tanggal mulai
            end_date: Tanggal akhir
            
        Returns:
            List transaksi dalam range
        """
        transactions = self.transaction_repo.get_by_date_range(start_date, end_date)
        return sorted(transactions, key=lambda t: t.tanggal, reverse=True)
    
    def get_daily_report(self, target_date: Optional[date] = None) -> dict:
        """
        Generate laporan harian.
        
        Args:
            target_date: Tanggal laporan, default hari ini
            
        Returns:
            Dict dengan ringkasan penjualan
        """
        summary = self.transaction_repo.get_daily_summary(target_date)
        
        # Get transactions for details
        if target_date is None:
            target_date = date.today()
        
        transactions = self.transaction_repo.get_by_date_range(target_date, target_date)
        
        return {
            **summary,
            "transactions": transactions
        }
    
    def get_dashboard_stats(self) -> dict:
        """
        Generate statistik untuk dashboard.
        
        Returns:
            Dict dengan berbagai statistik
        """
        today_summary = self.transaction_repo.get_daily_summary()
        all_transactions = self.transaction_repo.get_all()
        all_products = self.product_service.get_all_products()
        low_stock = self.product_service.get_low_stock_products()
        
        return {
            "today": today_summary,
            "total_products": len(all_products),
            "total_transactions_all_time": len(all_transactions),
            "total_revenue_all_time": sum(t.total for t in all_transactions),
            "low_stock_count": len(low_stock),
            "low_stock_products": [
                {"id": p.id, "nama": p.nama, "stok": p.stok}
                for p in low_stock[:5]  # Top 5 only
            ]
        }
