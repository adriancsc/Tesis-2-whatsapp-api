"""
Modelos de base de datos para el sistema MAS-CIS
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum


Base = declarative_base()


class TransactionType(enum.Enum):
    """Tipos de transacciones de inventario"""
    SELL = "sell"
    ADD = "add"
    UPDATE = "update"
    REMOVE = "remove"
    ADJUSTMENT = "adjustment"


class AgentType(enum.Enum):
    """Tipos de agentes en el sistema"""
    STORE = "store"
    COORDINATOR = "coordinator"
    GATEWAY = "gateway"


class Product(Base):
    """Modelo de Producto (Padre)"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)  # SKU base sin talla
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    base_price = Column(Float, nullable=False)  # Precio base del producto
    category = Column(String(100), nullable=True)
    color = Column(String(50), nullable=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(sku={self.sku}, name={self.name})>"


class ProductVariant(Base):
    """Modelo de Variante de Producto (por talla)"""
    __tablename__ = "product_variants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    sku = Column(String(50), unique=True, nullable=False, index=True)  # SKU con talla
    size = Column(String(20), nullable=False)  # S, M, L, XL, 2XL, etc.
    stock_physical = Column(Integer, default=0)  # Stock físico en tienda
    stock_virtual = Column(Integer, default=0)   # Stock reservado para e-commerce
    stock_total = Column(Integer, default=0)     # Stock total disponible
    price_adjustment = Column(Float, default=0.0)  # Ajuste de precio (opcional)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    product = relationship("Product", back_populates="variants")
    transactions = relationship("Transaction", back_populates="variant")
    
    def __repr__(self):
        return f"<ProductVariant(sku={self.sku}, size={self.size}, stock_total={self.stock_total})>"


class Transaction(Base):
    """Modelo de Transacción de Inventario"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Integer, nullable=False)
    previous_stock = Column(Integer, nullable=False)
    new_stock = Column(Integer, nullable=False)
    vendor_phone = Column(String(20), nullable=True)  # Teléfono del vendedor
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    variant = relationship("ProductVariant", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(type={self.transaction_type.value}, quantity={self.quantity})>"


class ChatSession(Base):
    """Modelo de Sesión de Chat con Vendedor"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    vendor_phone = Column(String(20), nullable=False, index=True)
    vendor_name = Column(String(100), nullable=True)
    status = Column(String(20), default="active")  # active, completed, expired
    context_data = Column(Text, nullable=True)  # JSON con contexto de conversación
    last_message_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ChatSession(vendor={self.vendor_phone}, status={self.status})>"


class AgentLog(Base):
    """Modelo de Log de Actividad de Agentes"""
    __tablename__ = "agent_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_type = Column(Enum(AgentType), nullable=False)
    action = Column(String(100), nullable=False)
    message = Column(Text, nullable=True)
    log_metadata = Column(Text, nullable=True)  # JSON con datos adicionales
    status = Column(String(20), default="success")  # success, error, warning
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AgentLog(agent={self.agent_type.value}, action={self.action})>"


class SyncHistory(Base):
    """Modelo de Historial de Sincronizaciones"""
    __tablename__ = "sync_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_type = Column(String(50), nullable=False)  # full, partial, product
    products_synced = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending, success, failed
    error_message = Column(Text, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<SyncHistory(type={self.sync_type}, status={self.status})>"
