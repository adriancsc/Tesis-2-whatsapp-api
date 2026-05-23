"""
Clase base abstracta para todos los agentes del sistema MAS-CIS
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

from src.utils.logger import setup_logger


class AgentStatus(Enum):
    """Estados posibles de un agente"""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"


class BaseAgent(ABC):
    """Clase base para todos los agentes"""
    
    def __init__(self, agent_id: str, agent_type: str):
        """
        Inicializa el agente base
        
        Args:
            agent_id: Identificador único del agente
            agent_type: Tipo de agente (store, coordinator, gateway)
        """
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.status = AgentStatus.IDLE
        self.logger = setup_logger(f"{agent_type}.{agent_id}")
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
        
        self.logger.info(f"🤖 Agente {self.agent_type} inicializado: {self.agent_id}")
    
    @abstractmethod
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un mensaje recibido
        
        Args:
            message: Mensaje a procesar
        
        Returns:
            Respuesta del agente
        """
        pass
    
    def update_status(self, status: AgentStatus):
        """Actualiza el estado del agente"""
        old_status = self.status
        self.status = status
        self.last_activity = datetime.utcnow()
        self.logger.debug(f"Estado cambiado: {old_status.value} -> {status.value}")
    
    def log_activity(self, action: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Registra una actividad del agente
        
        Args:
            action: Acción realizada
            metadata: Datos adicionales
        """
        self.last_activity = datetime.utcnow()
        log_data = {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "action": action,
            "timestamp": self.last_activity.isoformat(),
            "metadata": metadata or {}
        }
        self.logger.info(f"📊 Actividad: {action}", extra=log_data)
    
    def handle_error(self, error: Exception, context: str = ""):
        """
        Maneja errores del agente
        
        Args:
            error: Excepción ocurrida
            context: Contexto del error
        """
        self.update_status(AgentStatus.ERROR)
        self.logger.error(
            f"❌ Error en {self.agent_type} ({context}): {str(error)}",
            exc_info=True
        )
    
    def get_info(self) -> Dict[str, Any]:
        """Retorna información del agente"""
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }
