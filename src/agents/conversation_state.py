"""
Gestión de Estado de Conversación para el flujo interactivo de WhatsApp
Máquina de estados que rastrea en qué paso se encuentra cada vendedor
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional
from datetime import datetime, timedelta

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ConversationStep(str, Enum):
    """Pasos del flujo conversacional"""
    IDLE = "idle"                          # Sin conversación activa
    AWAITING_PRODUCT = "awaiting_product"  # Esperando selección de producto (polo)
    AWAITING_SIZE = "awaiting_size"        # Esperando selección de talla
    AWAITING_QUANTITY = "awaiting_quantity" # Esperando cantidad (texto libre)
    AWAITING_CONFIRM = "awaiting_confirm"  # Esperando confirmación final


@dataclass
class ConversationContext:
    """Datos acumulados durante el flujo conversacional de un vendedor"""
    step: ConversationStep = ConversationStep.IDLE
    action: Optional[str] = None        # "sell" | "add" | "remove"
    product_sku: Optional[str] = None   # SKU base del producto (ej: POLO-NEGRO)
    product_name: Optional[str] = None  # Nombre para mostrar (ej: Polo Negro)
    variant_id: Optional[int] = None    # ID de la variante seleccionada
    variant_sku: Optional[str] = None   # SKU de la variante (ej: POLO-NEGRO-M)
    size: Optional[str] = None          # Talla seleccionada
    quantity: Optional[int] = None      # Cantidad ingresada
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def reset(self):
        """Reinicia el contexto al estado inicial"""
        self.step = ConversationStep.IDLE
        self.action = None
        self.product_sku = None
        self.product_name = None
        self.variant_id = None
        self.variant_sku = None
        self.size = None
        self.quantity = None
        self.updated_at = datetime.utcnow()
    
    def is_expired(self, timeout_seconds: int = 300) -> bool:
        """Verifica si la conversación expiró (default: 5 minutos)"""
        return datetime.utcnow() - self.updated_at > timedelta(seconds=timeout_seconds)
    
    def touch(self):
        """Actualiza el timestamp de última actividad"""
        self.updated_at = datetime.utcnow()


class ConversationManager:
    """
    Administrador de conversaciones activas.
    Almacena en memoria el estado de cada vendedor por número de teléfono.
    """
    
    def __init__(self, timeout_seconds: int = 300):
        self._sessions: Dict[str, ConversationContext] = {}
        self._timeout = timeout_seconds
    
    def get_context(self, phone: str) -> ConversationContext:
        """
        Obtiene el contexto de conversación de un vendedor.
        Si no existe o expiró, crea uno nuevo en estado IDLE.
        
        Args:
            phone: Número de teléfono del vendedor
        
        Returns:
            ConversationContext del vendedor
        """
        context = self._sessions.get(phone)
        
        if context is None or context.is_expired(self._timeout):
            if context and context.is_expired(self._timeout):
                logger.info(f"⏰ Sesión expirada para {phone}, reiniciando")
            context = ConversationContext()
            self._sessions[phone] = context
        
        return context
    
    def reset_context(self, phone: str):
        """
        Reinicia el contexto de un vendedor al estado IDLE.
        
        Args:
            phone: Número de teléfono del vendedor
        """
        context = self._sessions.get(phone)
        if context:
            context.reset()
            logger.info(f"🔄 Contexto reiniciado para {phone}")
    
    def cleanup_expired(self):
        """Limpia sesiones expiradas de la memoria"""
        expired = [
            phone for phone, ctx in self._sessions.items()
            if ctx.is_expired(self._timeout)
        ]
        for phone in expired:
            del self._sessions[phone]
        
        if expired:
            logger.info(f"🧹 {len(expired)} sesiones expiradas limpiadas")


# Instancia global del administrador de conversaciones
conversation_manager = ConversationManager()
