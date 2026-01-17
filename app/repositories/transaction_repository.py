"""
Repository layer untuk akses data transaksi (laporan_penjualan.txt).
Bertanggung jawab untuk semua operasi I/O file terkait transaksi.
"""
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional

from schemas.transaction import Transaction, TransactionItem
from utils.file_lock import safe_read_file, safe_write_file, safe_append_file


class TransactionRepository:
    """
    Repository untuk operasi transaksi pada file laporan_penjualan.txt.
    Format file: id|tanggal|items|total|kasir
    """
    
    # Header untuk file laporan penjualan
    HEADER = "id|tanggal|items|total|kasir"
    
    def __init__(self, file_path: str):
        """
        Initialize repository dengan path ke file laporan.
        
        Args:
            file_path: Path absolut ke file laporan_penjualan.txt
        """
        self.file_path = file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Pastikan file exists dengan header."""
        path = Path(self.file_path)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            safe_write_file(self.file_path, self.HEADER, [])
    
    def get_all(self) -> List[Transaction]:
        """
        Ambil semua transaksi dari file.
        
        Returns:
            List of Transaction objects
        """
        lines = safe_read_file(self.file_path)
        transactions = []
        
        for line in lines:
            try:
                transaction = Transaction.from_line(line)
                transactions.append(transaction)
            except ValueError as e:
                print(f"Warning: Skipping invalid transaction line - {e}")
        
        return transactions
    
    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        """
        Cari transaksi berdasarkan ID.
        
        Args:
            transaction_id: ID transaksi
            
        Returns:
            Transaction jika ditemukan, None jika tidak
        """
        transactions = self.get_all()
        for trx in transactions:
            if trx.id == transaction_id:
                return trx
        return None
    
    def create(self, items: List[TransactionItem], total: int, kasir: str = "admin") -> Transaction:
        """
        Simpan transaksi baru ke file.
        
        Args:
            items: List item yang dibeli
            total: Total harga transaksi
            kasir: Nama kasir
            
        Returns:
            Transaction yang baru dibuat
        """
        transactions = self.get_all()
        
        # Generate new ID
        new_id = 1
        if transactions:
            new_id = max(t.id for t in transactions) + 1
        
        # Create new transaction
        new_transaction = Transaction(
            id=new_id,
            tanggal=datetime.now(),
            items=items,
            total=total,
            kasir=kasir
        )
        
        # Append to file (more efficient than rewriting entire file)
        safe_append_file(self.file_path, new_transaction.to_line())
        
        return new_transaction
    
    def get_by_date_range(
        self, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> List[Transaction]:
        """
        Filter transaksi berdasarkan range tanggal.
        
        Args:
            start_date: Tanggal mulai (inclusive)
            end_date: Tanggal akhir (inclusive)
            
        Returns:
            List transaksi dalam range
        """
        transactions = self.get_all()
        
        if start_date is None and end_date is None:
            return transactions
        
        filtered = []
        for trx in transactions:
            trx_date = trx.tanggal.date()
            
            if start_date and trx_date < start_date:
                continue
            if end_date and trx_date > end_date:
                continue
            
            filtered.append(trx)
        
        return filtered
    
    def get_today_transactions(self) -> List[Transaction]:
        """
        Ambil semua transaksi hari ini.
        
        Returns:
            List transaksi hari ini
        """
        today = date.today()
        return self.get_by_date_range(today, today)
    
    def get_daily_summary(self, target_date: Optional[date] = None) -> dict:
        """
        Hitung ringkasan penjualan per hari.
        
        Args:
            target_date: Tanggal target, default hari ini
            
        Returns:
            Dict berisi total_transactions, total_revenue, items_sold
        """
        if target_date is None:
            target_date = date.today()
        
        transactions = self.get_by_date_range(target_date, target_date)
        
        total_revenue = sum(t.total for t in transactions)
        items_sold = sum(sum(item.qty for item in t.items) for t in transactions)
        
        return {
            "date": target_date.isoformat(),
            "total_transactions": len(transactions),
            "total_revenue": total_revenue,
            "items_sold": items_sold
        }
