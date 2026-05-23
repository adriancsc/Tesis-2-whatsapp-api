"""
Esquemas Pydantic para validación de requests/responses
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ============= Product Schemas =============

class ProductBase(BaseModel):
    """Schema base de producto"""
    sku: str = Field(..., description="SKU único del producto")
    name: str = Field(..., description="Nombre del producto")
    description: Optional[str] = Field(None, description="Descripción del producto")
    price: float = Field(..., ge=0, description="Precio del producto")
    category: Optional[str] = Field(None, description="Categoría")
    size: Optional[str] = Field(None, description="Talla")
    color: Optional[str] = Field(None, description="Color")
    image_url: Optional[str] = Field(None, description="URL de imagen")


class ProductCreate(ProductBase):
    """Schema para crear producto"""
    stock_physical: int = Field(0, ge=0, description="Stock físico inicial")
    stock_virtual: int = Field(0, ge=0, description="Stock virtual inicial")


class ProductUpdate(BaseModel):
    """Schema para actualizar producto"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    image_url: Optional[str] = None


class ProductResponse(ProductBase):
    """Schema de respuesta de producto"""
    id: int
    stock_physical: int
    stock_virtual: int
    stock_total: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============= Stock Schemas =============

class StockUpdate(BaseModel):
    """Schema para actualizar stock"""
    action: str = Field(..., description="Acción: sell, add, update, remove")
    quantity: int = Field(..., ge=0, description="Cantidad")
    vendor_phone: Optional[str] = Field(None, description="Teléfono del vendedor")
    notes: Optional[str] = Field(None, description="Notas adicionales")


class StockResponse(BaseModel):
    """Schema de respuesta de actualización de stock"""
    success: bool
    product: Optional[ProductResponse] = None
    transaction_id: Optional[int] = None
    error: Optional[str] = None
    timestamp: datetime


# ============= Transaction Schemas =============

class TransactionResponse(BaseModel):
    """Schema de respuesta de transacción"""
    id: int
    product_id: int
    transaction_type: str
    quantity: int
    previous_stock: int
    new_stock: int
    vendor_phone: Optional[str]
    notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============= Sync Schemas =============

class SyncStatusResponse(BaseModel):
    """Schema de estado de sincronización"""
    status: str
    last_sync: Optional[datetime] = None
    products_synced: int = 0
    pending_operations: int = 0


# ============= Agent Schemas =============

class AgentInfoResponse(BaseModel):
    """Schema de información de agente"""
    agent_id: str
    agent_type: str
    status: str
    created_at: datetime
    last_activity: datetime


# ============= Webhook Schemas =============

class WhatsAppWebhook(BaseModel):
    """Schema para webhook de WhatsApp"""
    object: str
    entry: List[dict]


class WebhookVerification(BaseModel):
    """Schema para verificación de webhook"""
    mode: str = Field(..., alias="hub.mode")
    token: str = Field(..., alias="hub.verify_token")
    challenge: str = Field(..., alias="hub.challenge")
    
    class Config:
        populate_by_name = True


# ============= Dashboard Schemas =============

class DashboardStats(BaseModel):
    """Schema de estadísticas del dashboard"""
    total_products: int
    total_stock: int
    low_stock_products: int
    transactions_today: int
    active_sessions: int


class InventoryItem(BaseModel):
    """Schema de item de inventario para dashboard"""
    sku: str
    name: str
    stock_physical: int
    stock_virtual: int
    stock_total: int
    price: float
    category: Optional[str]
    last_updated: datetime
