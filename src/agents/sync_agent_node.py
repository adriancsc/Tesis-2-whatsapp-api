"""
Nodo del Agente de Sincronización (Sync Agent) — LangGraph
============================================================
Agente autónomo responsable de mantener sincronizado el stock
entre el Kárdex Digital y la plataforma e-commerce.

Propiedades MAS (Wooldridge & Jennings, 1995):
    - Reactividad:  Percibe webhooks del e-commerce y cambios en el
                    Kárdex post-transacción para sincronizar el catálogo web.
    - Autonomía:    Puede iniciar cancelaciones de órdenes y gestionar
                    reembolsos de forma autónoma si detecta conflictos.
    - Habilidad Social: Se comunica con el CoordinatorAgent mediante
                    mensajes request para procesar ventas web, y recibe
                    instrucciones de cancelación.

Casos de Uso implementados:
    - CU-04: Procesar Venta Digital (Compra Online)
    - CU-06: Cancelación de orden web por conflicto (parcial)
    - CU-11: Sincronización Reactiva Post-Venta con E-Commerce (nuevo)
"""
from typing import Dict, Any
from datetime import datetime

from src.agents.state import MASState, create_message
from src.database.connection import get_db
from src.database.models import AgentLog, AgentType
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Nombre del agente (para mensajes inter-agente)
AGENT_NAME = "sync_agent"


# =============================================================================
# Nodo Principal: sync_agent_node
# =============================================================================

def sync_agent_node(state: MASState) -> Dict[str, Any]:
    """
    Nodo del Agente de Sincronización en el grafo LangGraph.

    Dos modos de operación:

    1. MODO ENTRADA (source="ecommerce"):
       Procesa un webhook de compra del e-commerce, crea un mensaje
       request al CoordinatorAgent para ejecutar la venta web.

    2. MODO POST-TRANSACCIÓN (requires_sync=True):
       Después de una transacción exitosa del CoordinatorAgent,
       empuja la actualización de stock hacia la plataforma e-commerce
       para cumplir con RF-05 (Sincronización reactiva ≤ 5 segundos).

    Args:
        state: Estado actual del grafo MAS (MASState)

    Returns:
        Dict con actualizaciones parciales del estado.
    """
    source = state.get("source", "")
    requires_sync = state.get("requires_sync", False)

    # --- MODO ENTRADA: Procesar orden web (CU-04) ---
    if source == "ecommerce" and not state.get("operation_success", False):
        return _process_ecommerce_order(state)

    # --- MODO POST-TRANSACCIÓN: Sincronizar con e-commerce (CU-11) ---
    if requires_sync:
        return _push_stock_update(state)

    # --- MODO CONFLICTO: Cancelación/Reembolso (CU-06) ---
    if state.get("conflict_detected", False) and source == "ecommerce":
        return _process_ecommerce_cancellation(state)

    logger.info("🔄 SyncAgent | Sin acción requerida. No-op.")
    return {"requires_sync": False}


# =============================================================================
# Handler: Procesar Orden Web (CU-04)
# =============================================================================

def _process_ecommerce_order(state: MASState) -> Dict[str, Any]:
    """
    Procesa un webhook de compra del e-commerce.

    Flujo (CU-04):
    1. Parsea los datos del webhook (order_id, sku, quantity)
    2. Crea un mensaje request al CoordinatorAgent
    3. El grafo enruta al CoordinatorAgent para ejecutar la venta

    Args:
        state: Estado con datos del webhook e-commerce
    """
    order_id = state.get("ecommerce_order_id", "UNKNOWN")
    variant_sku = state.get("variant_sku")
    quantity = state.get("quantity", 1)

    logger.info(
        f"🔄 SyncAgent | Procesando orden web {order_id} | "
        f"SKU={variant_sku} | Qty={quantity}"
    )

    if not variant_sku:
        logger.error("🔄 SyncAgent | ERROR: No se proporcionó SKU de variante")
        return {
            "operation_success": False,
            "requires_coordinator": False,
            "response_text": f"❌ Orden web {order_id}: SKU no proporcionado.",
        }

    # --- Crear mensaje request al CoordinatorAgent ---
    msg = create_message(
        performative="request",
        sender=AGENT_NAME,
        receiver="coordinator_agent",
        content={
            "action": "sell_web",
            "variant_sku": variant_sku,
            "quantity": quantity,
            "order_id": order_id,
            "channel": "digital",
            "description": (
                f"Venta digital — Orden #{order_id} | "
                f"SKU: {variant_sku} | Cantidad: {quantity}"
            ),
        },
    )

    logger.info(f"🔄 SyncAgent envía request(sell_web) → CoordinatorAgent | Orden #{order_id}")

    # --- Log de actividad ---
    try:
        with get_db() as db:
            log = AgentLog(
                agent_type=AgentType.GATEWAY,
                action="ecommerce_order_received",
                message=f"Orden web #{order_id} recibida | SKU: {variant_sku} | Qty: {quantity}",
                log_metadata=str({
                    "order_id": order_id,
                    "variant_sku": variant_sku,
                    "quantity": quantity,
                }),
                status="success",
            )
            db.add(log)
            db.commit()
    except Exception as e:
        logger.error(f"Error registrando log de orden: {e}")

    return {
        "action": "sell_web",
        "requires_coordinator": True,
        "response_text": "",
        "messages": [msg],
    }


# =============================================================================
# Handler: Sincronización Post-Transacción (CU-11)
# =============================================================================

def _push_stock_update(state: MASState) -> Dict[str, Any]:
    """
    Empuja la actualización de stock hacia el e-commerce.

    Implementa RF-05: Sincronización reactiva del catálogo web
    inmediatamente después de consolidar un movimiento válido.

    En el prototipo, simula el push al e-commerce y registra
    el evento en el log de agentes. En producción, aquí se
    invocaría la API real del e-commerce (WooCommerce, Shopify, etc.).
    """
    # Buscar el inform del coordinador para obtener datos de la transacción
    coordinator_inform = None
    for msg in reversed(state.get("messages", [])):
        if (
            isinstance(msg, dict)
            and msg.get("performative") == "inform"
            and msg.get("sender") == "coordinator_agent"
        ):
            coordinator_inform = msg
            break

    if not coordinator_inform:
        logger.info("🔄 SyncAgent | Sin datos de transacción para sincronizar.")
        return {"requires_sync": False}

    content = coordinator_inform.get("content", {})
    variant_sku = content.get("variant_sku", "")
    new_stock = content.get("new_stock", 0)
    stock_total = content.get("stock_total", 0)
    action = content.get("action", "")

    logger.info(
        f"🔄 SyncAgent | Sincronizando stock con e-commerce | "
        f"SKU={variant_sku} | Stock={stock_total}"
    )

    # --- Simular push al e-commerce ---
    # En producción: requests.put(f"{ECOMMERCE_API}/products/{variant_sku}", json={...})
    sync_success = True  # Simulado como exitoso
    sync_timestamp = datetime.utcnow().isoformat()

    # --- Crear mensaje inform de sincronización ---
    sync_msg = create_message(
        performative="inform",
        sender=AGENT_NAME,
        receiver="coordinator_agent",
        content={
            "action": "sync_stock",
            "success": sync_success,
            "variant_sku": variant_sku,
            "synced_stock": stock_total,
            "timestamp": sync_timestamp,
            "platform": "ecommerce_api",
        },
    )

    # --- Log de actividad ---
    try:
        with get_db() as db:
            log = AgentLog(
                agent_type=AgentType.GATEWAY,
                action="ecommerce_sync",
                message=(
                    f"Stock sincronizado con e-commerce | "
                    f"SKU: {variant_sku} | Stock: {stock_total} | "
                    f"Resultado: {'OK' if sync_success else 'ERROR'}"
                ),
                log_metadata=str({
                    "variant_sku": variant_sku,
                    "stock_total": stock_total,
                    "sync_timestamp": sync_timestamp,
                    "trigger_action": action,
                }),
                status="success" if sync_success else "error",
            )
            db.add(log)
            db.commit()
    except Exception as e:
        logger.error(f"Error registrando log de sincronización: {e}")

    # Enriquecer respuesta con info de sincronización
    current_response = state.get("response_text", "")
    if sync_success and current_response:
        sync_note = "\n🔄 _Sincronización con e-commerce completada._"
        current_response = current_response.replace(
            "Escribe *menu* para volver al menú principal.",
            f"{sync_note}\n\nEscribe *menu* para volver al menú principal."
        )

    return {
        "requires_sync": False,
        "response_text": current_response,
        "messages": [sync_msg],
    }


def _process_ecommerce_cancellation(state: MASState) -> Dict[str, Any]:
    """
    Procesa la cancelación de una orden y solicita reembolso (CU-06).
    Se ejecuta cuando el CoordinatorAgent rechaza una orden web
    debido a conflictos de concurrencia o falta de stock.
    """
    order_id = state.get("ecommerce_order_id", "UNKNOWN")
    variant_sku = state.get("variant_sku")
    
    logger.warning(
        f"🔄 SyncAgent | Cancelando orden {order_id} por conflicto en SKU {variant_sku} (CU-06)"
    )

    # Simular la llamada a la pasarela de pagos (Stripe/PayPal) para el reembolso
    refund_success = True
    refund_msg = "Reembolso procesado a la pasarela de pagos."
    
    # Simular cancelación en plataforma E-Commerce
    ecommerce_msg = "Orden marcada como Cancelada en E-Commerce."

    try:
        with get_db() as db:
            log = AgentLog(
                agent_type=AgentType.GATEWAY,
                action="ecommerce_cancellation",
                message=f"Orden #{order_id} cancelada por conflicto de stock. {refund_msg}",
                log_metadata=str({
                    "order_id": order_id,
                    "variant_sku": variant_sku,
                    "refund_status": "success" if refund_success else "pending",
                }),
                status="warning",
            )
            db.add(log)
            db.commit()
    except Exception as e:
        logger.error(f"Error registrando cancelación: {e}")

    # Enviar mensaje al Coordinator (Solo informativo)
    cancel_msg = create_message(
        performative="inform",
        sender=AGENT_NAME,
        receiver="coordinator_agent",
        content={
            "action": "cancel_order",
            "order_id": order_id,
            "status": "refunded",
        },
    )

    return {
        "conflict_detected": False,  # Resuelto
        "response_text": state.get("response_text", "") + "\n\n" + f"🔄 _SyncAgent: {ecommerce_msg} {refund_msg}_",
        "messages": [cancel_msg],
    }
