"""
DTOs (Data Transfer Objects) para el sistema MAS-CIS
Objetos simples sin dependencia de sesión de base de datos
"""
from dataclasses import dataclass
from typing import Optional, List
from datetime import datetime


@dataclass
class VariantDTO:
    """Representa una variante de producto (talla específica)"""
    id: int
    sku: str
    size: str
    stock_physical: int
    stock_virtual: int
    stock_total: int
    product_id: int
    product_name: str
    product_price: float
    product_color: str


@dataclass
class ProductDTO:
    """Representa un producto padre con sus variantes"""
    id: int
    sku: str
    name: str
    description: Optional[str]
    base_price: float
    category: str
    color: str
    image_url: Optional[str]
    variants: List[VariantDTO]
    
    @property
    def total_stock(self) -> int:
        """Stock total sumando todas las variantes"""
        return sum(v.stock_total for v in self.variants)


@dataclass
class StockUpdateResult:
    """Resultado de una operación de actualización de stock"""
    success: bool
    variant_sku: str
    product_name: str
    size: str
    quantity_changed: int
    new_stock: int
    message: str
