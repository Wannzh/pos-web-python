"""
Pydantic models untuk Product entity.
Digunakan untuk validasi input/output data produk.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    """Base model dengan field umum produk."""
    nama: str = Field(..., min_length=1, max_length=100, description="Nama produk")
    harga: int = Field(..., gt=0, description="Harga produk dalam Rupiah")
    stok: int = Field(..., ge=0, description="Jumlah stok tersedia")


class ProductCreate(ProductBase):
    """Model untuk membuat produk baru."""
    pass


class ProductUpdate(BaseModel):
    """Model untuk update produk (semua field optional)."""
    nama: Optional[str] = Field(None, min_length=1, max_length=100)
    harga: Optional[int] = Field(None, gt=0)
    stok: Optional[int] = Field(None, ge=0)


class Product(ProductBase):
    """Model lengkap produk dengan ID dan timestamp."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

    def to_line(self) -> str:
        """Convert product to pipe-delimited line untuk file .txt"""
        return f"{self.id}|{self.nama}|{self.harga}|{self.stok}|{self.created_at.isoformat()}"

    @classmethod
    def from_line(cls, line: str) -> "Product":
        """Parse product from pipe-delimited line."""
        parts = line.strip().split("|")
        if len(parts) != 5:
            raise ValueError(f"Invalid product line format: {line}")
        
        return cls(
            id=int(parts[0]),
            nama=parts[1],
            harga=int(parts[2]),
            stok=int(parts[3]),
            created_at=datetime.fromisoformat(parts[4])
        )
