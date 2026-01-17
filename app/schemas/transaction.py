"""
Pydantic models untuk Transaction entity.
Digunakan untuk validasi input/output data transaksi penjualan.
"""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class TransactionItem(BaseModel):
    """Item dalam transaksi."""
    product_id: int = Field(..., description="ID produk")
    nama: str = Field(..., description="Nama produk")
    qty: int = Field(..., gt=0, description="Jumlah item")
    subtotal: int = Field(..., ge=0, description="Subtotal (harga x qty)")

    def to_string(self) -> str:
        """Convert item to string format untuk file .txt"""
        return f"{self.product_id}:{self.nama}:{self.qty}:{self.subtotal}"

    @classmethod
    def from_string(cls, s: str) -> "TransactionItem":
        """Parse item from string format."""
        parts = s.split(":")
        if len(parts) != 4:
            raise ValueError(f"Invalid item format: {s}")
        
        return cls(
            product_id=int(parts[0]),
            nama=parts[1],
            qty=int(parts[2]),
            subtotal=int(parts[3])
        )


class TransactionCreate(BaseModel):
    """Model untuk membuat transaksi baru."""
    items: List[dict] = Field(..., min_length=1, description="List item yang dibeli")
    kasir: str = Field(default="admin", description="Nama kasir")


class Transaction(BaseModel):
    """Model lengkap transaksi."""
    id: int
    tanggal: datetime
    items: List[TransactionItem]
    total: int
    kasir: str

    def to_line(self) -> str:
        """Convert transaction to pipe-delimited line untuk file .txt"""
        items_str = ";".join([item.to_string() for item in self.items])
        return f"{self.id}|{self.tanggal.isoformat()}|{items_str}|{self.total}|{self.kasir}"

    @classmethod
    def from_line(cls, line: str) -> "Transaction":
        """Parse transaction from pipe-delimited line."""
        parts = line.strip().split("|")
        if len(parts) != 5:
            raise ValueError(f"Invalid transaction line format: {line}")
        
        items_str = parts[2]
        items = []
        if items_str:
            for item_str in items_str.split(";"):
                items.append(TransactionItem.from_string(item_str))
        
        return cls(
            id=int(parts[0]),
            tanggal=datetime.fromisoformat(parts[1]),
            items=items,
            total=int(parts[3]),
            kasir=parts[4]
        )
