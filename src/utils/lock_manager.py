"""
Administrador de Bloqueos en Memoria (Semáforos)
================================================
Provee control de concurrencia a nivel de aplicación (Táctico).
Se utiliza temporalmente para resolver el CU-05 con SQLite,
hasta que se realice la migración a SQL Server.
"""
import threading
from typing import Dict
from contextlib import contextmanager

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class InventoryLockManager:
    """Administrador de locks por SKU de variante"""
    
    def __init__(self):
        self._locks: Dict[str, threading.Lock] = {}
        self._global_lock = threading.Lock()

    def _get_lock(self, sku: str) -> threading.Lock:
        """Obtiene o crea un lock específico para un SKU"""
        with self._global_lock:
            if sku not in self._locks:
                self._locks[sku] = threading.Lock()
            return self._locks[sku]

    @contextmanager
    def acquire(self, sku: str, timeout: float = 2.0):
        """
        Adquiere el lock para un SKU con un timeout.
        Lanza TimeoutError si no se puede adquirir a tiempo.
        """
        lock = self._get_lock(sku)
        
        logger.debug(f"🔒 Intentando adquirir lock para SKU: {sku}")
        acquired = lock.acquire(timeout=timeout)
        
        if not acquired:
            logger.warning(f"⏳ TIMEOUT: No se pudo adquirir lock para SKU: {sku} en {timeout}s")
            raise TimeoutError(f"El recurso {sku} está ocupado por otra transacción.")
            
        try:
            logger.debug(f"🔑 Lock adquirido para SKU: {sku}")
            yield
        finally:
            lock.release()
            logger.debug(f"🔓 Lock liberado para SKU: {sku}")


# Instancia global del Lock Manager
inventory_lock = InventoryLockManager()
