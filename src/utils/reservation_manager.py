"""
Gestor de Reservas Temporales de Stock — MAS-CIS
==================================================
Administra reservas temporales de inventario para prevenir conflictos
de concurrencia entre el canal WhatsApp (vendedor físico) y el canal
Web (cliente e-commerce).

Mecanismo:
    Cuando un vendedor en WhatsApp avanza al paso de confirmación de
    venta, el sistema reserva N unidades de una variante por un
    tiempo configurable (por defecto 10 minutos). Durante ese periodo,
    las unidades reservadas se descuentan del stock visible para la
    tienda web, evitando que un cliente online compre el mismo producto.

    Si el vendedor confirma la venta, la reserva se "consume" y el
    CoordinatorAgent ejecuta el descuento real en la BD.
    Si el vendedor cancela o el tiempo expira, la reserva se libera
    automáticamente y las unidades vuelven a estar disponibles.

Thread Safety:
    Todas las operaciones usan threading.Lock para garantizar seguridad
    en accesos concurrentes desde múltiples webhooks simultáneos.
"""
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Duración por defecto de la reserva (en minutos)
DEFAULT_RESERVATION_MINUTES = 10


class ReservationManager:
    """
    Gestor de reservas temporales de stock.
    
    Estructura interna:
        _reservations = {
            "51999888777": {
                "variant_id": 5,
                "quantity": 2,
                "variant_sku": "POLO-BLANCO-M",
                "expires_at": datetime(2026, 7, 13, 20, 30, 0),
            },
            ...
        }
    
    Cada vendedor solo puede tener UNA reserva activa a la vez
    (una transacción en curso en WhatsApp).
    """

    def __init__(self, reservation_minutes: int = DEFAULT_RESERVATION_MINUTES):
        self._reservations: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self._reservation_duration = timedelta(minutes=reservation_minutes)

    def reserve(
        self,
        vendor_phone: str,
        variant_id: int,
        variant_sku: str,
        quantity: int,
    ) -> bool:
        """
        Crea una reserva temporal de stock para un vendedor.
        
        Si el vendedor ya tenía una reserva activa (de una operación
        anterior que no confirmó), se libera la anterior primero.
        
        Args:
            vendor_phone: Teléfono del vendedor (identificador único)
            variant_id: ID de la variante del producto
            variant_sku: SKU de la variante (para logs)
            quantity: Cantidad a reservar
            
        Returns:
            True si la reserva se creó exitosamente
        """
        with self._lock:
            # Limpiar reservas expiradas primero
            self._cleanup_expired_unsafe()

            # Liberar reserva previa del vendedor (si existe)
            if vendor_phone in self._reservations:
                old = self._reservations[vendor_phone]
                logger.info(
                    f"🔓 Reserva anterior liberada para {vendor_phone} "
                    f"({old['variant_sku']} x{old['quantity']})"
                )

            # Crear nueva reserva
            expires_at = datetime.utcnow() + self._reservation_duration
            self._reservations[vendor_phone] = {
                "variant_id": variant_id,
                "variant_sku": variant_sku,
                "quantity": quantity,
                "expires_at": expires_at,
            }

            logger.info(
                f"🔒 Stock RESERVADO | {vendor_phone} | "
                f"{variant_sku} x{quantity} | "
                f"Expira: {expires_at.strftime('%H:%M:%S')}"
            )
            return True

    def release(self, vendor_phone: str) -> bool:
        """
        Libera la reserva de un vendedor (cancelación o reinicio de menú).
        
        Args:
            vendor_phone: Teléfono del vendedor
            
        Returns:
            True si se liberó una reserva, False si no tenía
        """
        with self._lock:
            if vendor_phone in self._reservations:
                released = self._reservations.pop(vendor_phone)
                logger.info(
                    f"🔓 Reserva LIBERADA | {vendor_phone} | "
                    f"{released['variant_sku']} x{released['quantity']}"
                )
                return True
            return False

    def consume(self, vendor_phone: str) -> Optional[dict]:
        """
        Consume la reserva (el vendedor confirmó la venta).
        
        Retorna los datos de la reserva para que el CoordinatorAgent
        pueda verificar que la operación coincide, o None si la
        reserva ya expiró.
        
        Args:
            vendor_phone: Teléfono del vendedor
            
        Returns:
            Dict con datos de la reserva, o None si expiró/no existe
        """
        with self._lock:
            self._cleanup_expired_unsafe()

            reservation = self._reservations.pop(vendor_phone, None)
            if reservation:
                logger.info(
                    f"✅ Reserva CONSUMIDA | {vendor_phone} | "
                    f"{reservation['variant_sku']} x{reservation['quantity']}"
                )
            return reservation

    def get_reserved_quantity(self, variant_id: int) -> int:
        """
        Obtiene la cantidad total reservada de una variante específica.
        
        Usado por la tienda web para mostrar stock disponible real
        (stock_total - reservas_activas).
        
        Args:
            variant_id: ID de la variante
            
        Returns:
            Cantidad total de unidades reservadas para esa variante
        """
        with self._lock:
            self._cleanup_expired_unsafe()

            total_reserved = 0
            for reservation in self._reservations.values():
                if reservation["variant_id"] == variant_id:
                    total_reserved += reservation["quantity"]
            return total_reserved

    def get_vendor_reservation(self, vendor_phone: str) -> Optional[dict]:
        """
        Consulta si un vendedor tiene una reserva activa (no expirada).
        
        Args:
            vendor_phone: Teléfono del vendedor
            
        Returns:
            Dict con datos de la reserva, o None si no tiene o expiró
        """
        with self._lock:
            self._cleanup_expired_unsafe()
            return self._reservations.get(vendor_phone)

    def get_all_active(self) -> Dict[str, dict]:
        """Retorna todas las reservas activas (para debugging/logs)"""
        with self._lock:
            self._cleanup_expired_unsafe()
            return dict(self._reservations)

    def _cleanup_expired_unsafe(self) -> int:
        """
        Limpia reservas expiradas (NO thread-safe, usar dentro de with self._lock).
        
        Returns:
            Cantidad de reservas eliminadas
        """
        now = datetime.utcnow()
        expired = [
            phone for phone, res in self._reservations.items()
            if res["expires_at"] <= now
        ]
        for phone in expired:
            released = self._reservations.pop(phone)
            logger.warning(
                f"⏰ Reserva EXPIRADA | {phone} | "
                f"{released['variant_sku']} x{released['quantity']} | "
                f"Expiró hace {(now - released['expires_at']).seconds}s"
            )
        return len(expired)


# Instancia global del gestor de reservas
reservation_manager = ReservationManager()
