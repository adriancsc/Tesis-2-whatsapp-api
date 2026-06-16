"""
Gestión de Estado de Conversación en Memoria
=============================================
Almacena temporalmente el estado (current_step) y datos acumulados
de las sesiones de WhatsApp por número de teléfono.
Sirve como puente entre los webhooks stateless y el grafo stateful (LangGraph).
"""
from dataclasses import dataclass, field
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ConversationContext:
    """Datos acumulados de una sesión de vendedor en curso"""
    current_step: str = "MAIN_MENU"
    action: Optional[str] = None
    product_sku: Optional[str] = None
    product_name: Optional[str] = None
    variant_id: Optional[int] = None
    variant_sku: Optional[str] = None
    size: Optional[str] = None
    quantity: Optional[int] = None
    size_options: Optional[dict] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def reset(self):
        """Reinicia el contexto al estado inicial"""
        self.current_step = "MAIN_MENU"
        self.action = None
        self.product_sku = None
        self.product_name = None
        self.variant_id = None
        self.variant_sku = None
        self.size = None
        self.quantity = None
        self.size_options = None
        self.updated_at = datetime.utcnow()

    def update_from_state(self, state: dict):
        """Actualiza el contexto en memoria desde el estado retornado por LangGraph"""
        self.current_step = state.get("current_step", "MAIN_MENU")
        self.action = state.get("action")
        self.product_sku = state.get("product_sku")
        self.product_name = state.get("product_name")
        self.variant_id = state.get("variant_id")
        self.variant_sku = state.get("variant_sku")
        self.size = state.get("size")
        self.quantity = state.get("quantity")
        self.size_options = state.get("size_options")
        self.updated_at = datetime.utcnow()

    def is_expired(self, timeout_seconds: int = 300) -> bool:
        """Verifica si la conversación expiró"""
        return datetime.utcnow() - self.updated_at > timedelta(seconds=timeout_seconds)


class ConversationManager:
    """Administrador de sesiones en memoria"""
    
    def __init__(self, timeout_seconds: int = 300):
        self._sessions: Dict[str, ConversationContext] = {}
        self._timeout = timeout_seconds

    def get_context(self, phone: str) -> ConversationContext:
        """Obtiene o crea el contexto de una sesión"""
        context = self._sessions.get(phone)
        
        if context is None or context.is_expired(self._timeout):
            if context and context.is_expired(self._timeout):
                logger.info(f"⏰ Sesión expirada para {phone}, reiniciando")
            context = ConversationContext()
            self._sessions[phone] = context
            
        return context

    def reset_context(self, phone: str):
        """Fuerza el reinicio de una sesión"""
        context = self._sessions.get(phone)
        if context:
            context.reset()
            logger.info(f"🔄 Contexto reiniciado para {phone}")

    def cleanup_expired(self):
        """Limpia sesiones antiguas"""
        expired = [
            phone for phone, ctx in self._sessions.items()
            if ctx.is_expired(self._timeout)
        ]
        for phone in expired:
            del self._sessions[phone]


# Instancia global (Singleton en memoria)
conversation_manager = ConversationManager()
