"""
Nodo del Agente Coordinador (Coordinator Agent) — LangGraph
=============================================================
Agente autónomo responsable de garantizar la integridad ACID
del Kárdex Digital y resolver conflictos de concurrencia.

Propiedades MAS (Wooldridge & Jennings, 1995):
    - Autonomía:    Puede RECHAZAR solicitudes (refuse) si violan
                    reglas de negocio. Aplica límite de 1000 unidades
                    por transacción. Detecta anomalías autónomamente.
    - Reactividad:  Percibe el estado del Kárdex en cada operación
                    y reacciona a condiciones de stock bajo/agotado.
    - Proactividad: Post-transacción, evalúa si se requiere una alerta
                    y activa al AlertAgent de forma autónoma.
    - Habilidad Social: Recibe mensajes request del StoreAgent/SyncAgent
                    y responde con inform (éxito) o refuse (rechazo).

Casos de Uso implementados:
    - CU-01/02/03: Transacciones de stock (sell/add/remove)
    - CU-04: Venta digital desde e-commerce (sell_web)
    - CU-07: Consulta de inventario (query)
    - CU-08: Resumen del día (daily_summary)
"""
from typing import Dict, Any
from datetime import datetime, date
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from src.agents.state import MASState, create_message
from src.database.connection import get_db
from src.database.models import (
    Product, ProductVariant, Transaction, TransactionType,
    AgentLog, AgentType,
)
from src.utils.validators import InventoryValidator
from src.utils.reservation_manager import reservation_manager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Nombre del agente (para mensajes inter-agente)
AGENT_NAME = "coordinator_agent"

ACTION_NAMES = {
    "sell": "VENTA PRESENCIAL",
    "sell_web": "VENTA WEB",
    "add": "INGRESO",
    "remove": "MERMA",
}


# =============================================================================
# Nodo Principal: coordinator_agent_node
# =============================================================================

def coordinator_agent_node(state: MASState) -> Dict[str, Any]:
    """
    Nodo del Agente Coordinador en el grafo LangGraph.

    Lee el último mensaje de tipo request en la cola de mensajes,
    ejecuta la operación solicitada (transacción, consulta o resumen),
    y responde con un mensaje inform (éxito) o refuse (rechazo).

    Post-transacción, evalúa si se requiere una alerta y activa
    la señal requires_alert para el AlertAgent.

    Args:
        state: Estado actual del grafo MAS (MASState)

    Returns:
        Dict con actualizaciones parciales del estado, incluyendo
        mensajes de respuesta inter-agente.
    """
    # --- Leer la solicitud del agente emisor ---
    request_msg = _find_last_request(state.get("messages", []))
    if not request_msg:
        logger.warning("⚠️ CoordinatorAgent: No se encontró mensaje request")
        return {
            "operation_success": False,
            "response_text": "❌ Error interno: No se recibió solicitud.\n\nEscribe *menu* para volver.",
        }

    sender = request_msg["sender"]
    content = request_msg["content"]
    action = content.get("action", state.get("action"))

    logger.info(
        f"🎯 CoordinatorAgent | Recibido request de {sender} | "
        f"action={action}"
    )

    # --- Despachar según el tipo de acción ---
    if action == "query":
        return _handle_inventory_query(sender)

    elif action == "daily_summary":
        return _handle_daily_summary(sender)

    elif action in ("sell", "sell_web", "add", "remove"):
        return _handle_stock_transaction(state, action, content, sender)

    else:
        refuse_msg = create_message(
            performative="refuse",
            sender=AGENT_NAME,
            receiver=sender,
            content={"reason": "unknown_action", "action": action},
        )
        logger.warning(f"🎯 CoordinatorAgent REFUSE: Acción desconocida '{action}'")
        return {
            "operation_success": False,
            "response_text": f"❌ Acción no reconocida: {action}\n\nEscribe *menu* para volver.",
            "messages": [refuse_msg],
        }


# =============================================================================
# Handler: Transacciones de Stock (CU-01, CU-02, CU-03, CU-04)
# =============================================================================

def _handle_stock_transaction(
    state: MASState, action: str, content: dict, sender: str,
) -> Dict[str, Any]:
    """
    Ejecuta una transacción atómica de stock.

    Autonomía del agente:
    - Puede RECHAZAR la operación si viola reglas de negocio
    - Aplica límite de 100 unidades por transacción
    - Detecta anomalías en mermas diarias

    Args:
        state: Estado actual del grafo
        action: Tipo de operación (sell/add/remove/sell_web)
        content: Payload del mensaje request
        sender: Nombre del agente emisor
    """
    variant_sku = content.get("variant_sku") or state.get("variant_sku")
    quantity = content.get("quantity") or state.get("quantity")
    vendor_phone = state.get("vendor_phone", "API")

    logger.info(
        f"🎯 CoordinatorAgent | Procesando {action} | "
        f"sku={variant_sku} | qty={quantity}"
    )

    # --- Autonomía: Límite por operación ---
    if quantity and quantity > 1000:
        refuse_msg = create_message(
            performative="refuse",
            sender=AGENT_NAME,
            receiver=sender,
            content={
                "reason": "quantity_limit_exceeded",
                "max_allowed": 1000,
                "requested": quantity,
            },
        )
        logger.warning(f"🎯 CoordinatorAgent REFUSE: Cantidad {quantity} > 1000")
        return {
            "operation_success": False,
            "requires_alert": False,
            "response_text": (
                f"⛔ *OPERACIÓN RECHAZADA (Agente Coordinador)*\n\n"
                f"Por seguridad, no se permite procesar más de 1000 unidades "
                f"en una sola transacción.\n"
                f"Has solicitado {quantity} unidades.\n\n"
                f"Escribe *menu* para volver y dividir la operación."
            ),
            "messages": [refuse_msg],
        }

    validator = InventoryValidator()
    
    # Importar el Lock Manager (Solución táctica CU-05)
    from src.utils.lock_manager import inventory_lock

    try:
        # Adquirir el lock para este SKU antes de abrir la transacción
        with inventory_lock.acquire(variant_sku, timeout=3.0):
            with get_db() as db:
                # --- Buscar la variante en la BD ---
                variant = (
                    db.query(ProductVariant)
                    .options(joinedload(ProductVariant.product))
                    .filter(ProductVariant.sku == variant_sku)
                    .first()
                )
    
                if not variant:
                    refuse_msg = create_message(
                        performative="refuse",
                        sender=AGENT_NAME,
                        receiver=sender,
                        content={"reason": "variant_not_found", "sku": variant_sku},
                    )
                    logger.error(f"🎯 CoordinatorAgent REFUSE: Variante no encontrada: {variant_sku}")
                    return {
                        "operation_success": False,
                        "response_text": f"❌ Error: Variante no encontrada ({variant_sku}).\n\nEscribe *menu* para volver.",
                        "messages": [refuse_msg],
                    }
    
                # --- Validar operación con reglas de negocio ---
                current_stock = variant.stock_physical
                base_action = action.replace("_web", "")  # sell_web → sell
                validation = validator.validate_stock_operation(
                    product_sku=variant_sku,
                    quantity=quantity,
                    operation=base_action,
                    current_stock=(
                        current_stock if base_action in ["sell", "remove"] else None
                    ),
                )
    
                if not validation["valid"]:
                    error_msg_text = ", ".join(validation["errors"])
                    refuse_msg = create_message(
                        performative="refuse",
                        sender=AGENT_NAME,
                        receiver=sender,
                        content={
                            "reason": "validation_failed",
                            "errors": validation["errors"],
                        },
                    )
                    logger.warning(f"🎯 CoordinatorAgent REFUSE: {error_msg_text}")
                    return {
                        "operation_success": False,
                        "response_text": f"❌ Error de validación: {error_msg_text}\n\nEscribe *menu* para volver.",
                        "messages": [refuse_msg],
                    }
    
                # --- Ejecutar operación atómica sobre ProductVariant ---
                previous_stock = variant.stock_physical
                
                # --- Validar stock suficiente para VENTAS (WhatsApp o Web) ---
                if action in ["sell", "sell_web"]:
                    # Cuántas reservas hay de ESTE producto que NO son mías
                    # (Si era sell de WhatsApp, mi reserva ya fue consumida)
                    reserved_by_others = reservation_manager.get_reserved_quantity(variant.id)
                    stock_available = variant.stock_total - reserved_by_others

                    if quantity > stock_available:
                        refuse_msg = create_message(
                            performative="refuse",
                            sender=AGENT_NAME,
                            receiver=sender,
                            content={"reason": "insufficient_stock", "available": stock_available},
                        )
                        logger.warning(
                            f"🎯 CoordinatorAgent REFUSE: Stock insuficiente. "
                            f"Req: {quantity}, Disp: {stock_available} (Reservado: {reserved_by_others})"
                        )
                        return {
                            "operation_success": False,
                            "response_text": (
                                f"❌ *STOCK INSUFICIENTE (Agente Coordinador)*\n\n"
                                f"Producto: {variant.product.name} (Talla {variant.size})\n"
                                f"Stock disponible: {stock_available}\n"
                                f"Stock en reservas web/whatsapp: {reserved_by_others}\n"
                                f"Cantidad solicitada: {quantity}\n\n"
                                f"Escribe *menu* para volver."
                            ),
                            "messages": [refuse_msg],
                        }
                    
                    # Validar límites atómicos de ventas
                    if quantity > 1000:
                        refuse_msg = create_message(
                            performative="refuse",
                            sender=AGENT_NAME,
                            receiver=sender,
                            content={"reason": "limit_exceeded", "limit": 1000},
                        )
                        return {
                            "operation_success": False,
                            "response_text": "❌ La cantidad excede el límite máximo por transacción (1000 unidades).\n\nEscribe *menu* para volver.",
                            "messages": [refuse_msg],
                        }
                    
                    # Descontar stock físico
                    variant.stock_physical -= quantity
                    
                    tx_type = TransactionType.SELL
                    channel = "web" if action == "sell_web" else "presencial"
                    notes = f"Venta {channel} registrada por {vendor_phone}"
                elif action == "add":
                    variant.stock_physical += quantity
                    tx_type = TransactionType.ADD
                    notes = f"Ingreso registrado por {vendor_phone}"
                elif action == "remove":
                    variant.stock_physical -= quantity
                    tx_type = TransactionType.REMOVE
                    notes = f"Merma registrada por {vendor_phone}"
                else:
                    return {
                        "operation_success": False,
                        "response_text": f"❌ Acción no reconocida: {action}\n\nEscribe *menu* para volver.",
                    }
    
                # Recalcular stock total
                variant.stock_total = variant.stock_physical + variant.stock_virtual
                variant.updated_at = datetime.utcnow()
                variant.product.updated_at = datetime.utcnow()
    
                # --- Registrar transacción en el Kárdex (Append-Only, RF-04) ---
                transaction = Transaction(
                    variant_id=variant.id,
                    transaction_type=tx_type,
                    quantity=quantity,
                    previous_stock=previous_stock,
                    new_stock=variant.stock_physical,
                    vendor_phone=vendor_phone,
                    notes=notes,
                )
                db.add(transaction)
    
                # --- Registrar log del agente ---
                agent_log = AgentLog(
                    agent_type=AgentType.COORDINATOR,
                    action=f"inventory_{action}",
                    message=(
                        f"Operación {action} en variante {variant_sku} | "
                        f"Qty: {quantity} | Stock: {previous_stock} → {variant.stock_physical}"
                    ),
                    log_metadata=str({
                        "variant_sku": variant_sku,
                        "quantity": quantity,
                        "previous_stock": previous_stock,
                        "new_stock": variant.stock_physical,
                        "vendor_phone": vendor_phone,
                        "channel": "web" if "web" in action else "physical",
                    }),
                    status="success",
                )
                db.add(agent_log)
    
                # Commit atómico (connection.py hace auto-rollback en error)
                db.commit()
    
                # Capturar datos antes de cerrar sesión
                product_name = variant.product.name
                variant_size = variant.size
                new_stock = variant.stock_physical
                stock_total = variant.stock_total
                variant_id_captured = variant.id
    
        # --- Evaluar si se requiere alerta (Proactividad) ---
        needs_alert = False
        alert_data = {}

        if new_stock == 0:
            needs_alert = True
            alert_data = {
                "type": "stock_depleted",
                "variant_sku": variant_sku,
                "product_name": product_name,
                "size": variant_size,
            }
        elif new_stock <= 2:
            needs_alert = True
            alert_data = {
                "type": "low_stock",
                "variant_sku": variant_sku,
                "product_name": product_name,
                "size": variant_size,
                "remaining": new_stock,
            }

        # Detectar anomalía de mermas (Autonomía)
        if action == "remove":
            anomaly = _check_merma_anomaly(variant_id_captured, stock_total)
            if anomaly:
                needs_alert = True
                alert_data["merma_anomaly"] = anomaly

        # --- Generar respuesta de éxito ---
        logger.info(
            f"✅ CoordinatorAgent: Operación exitosa {action} | {variant_sku} | "
            f"Qty: {quantity} | Stock: {previous_stock} → {new_stock}"
        )

        op_name = ACTION_NAMES.get(action, "OPERACIÓN")
        response = (
            f"✅ *{op_name} COMPLETADA*\n\n"
            f"📦 {product_name} - Talla {variant_size}\n"
            f"   SKU: {variant_sku}\n"
            f"📊 Stock anterior: {previous_stock}\n"
            f"📊 Stock nuevo: {new_stock}\n"
            f"📊 Stock total (físico + virtual): {stock_total}\n\n"
            f"✨ El inventario ha sido actualizado.\n\n"
            f"Escribe *menu* para volver al menú principal."
        )

        # --- Crear mensaje inform de éxito ---
        inform_msg = create_message(
            performative="inform",
            sender=AGENT_NAME,
            receiver=sender,
            content={
                "success": True,
                "action": action,
                "variant_sku": variant_sku,
                "product_name": product_name,
                "size": variant_size,
                "quantity": quantity,
                "previous_stock": previous_stock,
                "new_stock": new_stock,
                "stock_total": stock_total,
                "alert_data": alert_data if needs_alert else None,
            },
        )

        result = {
            "operation_success": True,
            "response_text": response,
            "requires_alert": needs_alert,
            "requires_sync": action in ("sell", "add", "remove"),
            "messages": [inform_msg],
        }

        return result

    except TimeoutError as te:
        logger.warning(f"🎯 CoordinatorAgent REFUSE (Concurrency): {te}")
        refuse_msg = create_message(
            performative="refuse",
            sender=AGENT_NAME,
            receiver=sender,
            content={"reason": "concurrency_conflict", "error": str(te)},
        )
        return {
            "operation_success": False,
            "conflict_detected": True,
            "response_text": (
                "⚠️ *CONFLICTO DE CONCURRENCIA*\n\n"
                "Otro proceso está actualizando este producto en este instante.\n"
                "Por favor, intenta de nuevo en unos segundos."
            ),
            "messages": [refuse_msg],
        }

    except Exception as e:
        logger.error(f"❌ Error en CoordinatorAgent: {e}", exc_info=True)
        _log_error(action, variant_sku, quantity, str(e))

        refuse_msg = create_message(
            performative="refuse",
            sender=AGENT_NAME,
            receiver=sender,
            content={"reason": "internal_error", "error": str(e)},
        )
        return {
            "operation_success": False,
            "response_text": "❌ Error interno al procesar la operación.\n\nEscribe *menu* para volver.",
            "messages": [refuse_msg],
        }


# =============================================================================
# Handler: Consulta de Inventario (CU-07)
# =============================================================================

def _handle_inventory_query(sender: str) -> Dict[str, Any]:
    """
    Procesa la solicitud de consulta de inventario.
    Ejecuta SELECT en el Kárdex bajo aislamiento transaccional.
    """
    logger.info(f"🎯 CoordinatorAgent | Procesando consulta de inventario para {sender}")

    try:
        with get_db() as db:
            products = (
                db.query(Product)
                .options(joinedload(Product.variants))
                .all()
            )

            if not products:
                text = "📭 No hay productos registrados en el inventario.\n\nEscribe *menu* para volver."
            else:
                text = "📋 *INVENTARIO ACTUAL*\n"
                text += "═" * 20 + "\n\n"
                low_stock_variants = []

                for product in products:
                    total = sum(v.stock_total for v in product.variants) if product.variants else 0
                    text += f"📦 *{product.name}*\n"
                    text += f"   📊 Stock total: {total} unidades\n"

                    if product.variants:
                        for v in product.variants:
                            if v.stock_total > 1:
                                emoji = "✅"
                            elif v.stock_total == 1:
                                emoji = "⚠️"
                                low_stock_variants.append(f"{product.name} talla {v.size}")
                            else:
                                emoji = "❌"
                                low_stock_variants.append(f"{product.name} talla {v.size}")
                            text += f"      {emoji} Talla {v.size}: {v.stock_total}\n"
                    text += "\n"

                text += "─" * 20 + "\n"

                # Sugerencia proactiva (Proactividad del Agente)
                if low_stock_variants:
                    text += "💡 *SUGERENCIA DEL AGENTE:*\n"
                    text += (
                        f"Detecté stock bajo o agotado en {len(low_stock_variants)} "
                        f"variante(s) (ej: {low_stock_variants[0]}).\n"
                        f"Te sugiero registrar un *Ingreso* (opción 2) pronto.\n\n"
                    )
                text += "Escribe *menu* para volver."

        # --- Log de actividad ---
        try:
            with get_db() as db2:
                log = AgentLog(
                    agent_type=AgentType.COORDINATOR,
                    action="inventory_query",
                    message=f"Consulta de inventario solicitada por {sender}",
                    status="success",
                )
                db2.add(log)
                db2.commit()
        except Exception:
            pass

        inform_msg = create_message(
            performative="inform",
            sender=AGENT_NAME,
            receiver=sender,
            content={"action": "query", "success": True},
        )

        return {
            "operation_success": True,
            "requires_alert": False,
            "response_text": text,
            "messages": [inform_msg],
        }

    except Exception as e:
        logger.error(f"Error en consulta de inventario: {e}", exc_info=True)
        return {
            "operation_success": False,
            "response_text": "❌ Error al consultar inventario.\n\nEscribe *menu* para volver.",
        }


# =============================================================================
# Handler: Resumen del Día (CU-08)
# =============================================================================

def _handle_daily_summary(sender: str) -> Dict[str, Any]:
    """
    Genera un consolidado de todos los movimientos del día actual.

    Implementa CU-08: El Agente Coordinador invoca funciones de
    agregación relacional (SUM/COUNT) filtrando por la fecha del día.
    """
    logger.info(f"🎯 CoordinatorAgent | Generando resumen del día para {sender}")

    try:
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())

        with get_db() as db:
            # Consultas de agregación por tipo de transacción
            def _sum_by_type(tx_type: TransactionType) -> tuple:
                result = db.query(
                    func.count(Transaction.id),
                    func.coalesce(func.sum(Transaction.quantity), 0),
                ).filter(
                    Transaction.transaction_type == tx_type,
                    Transaction.created_at >= today_start,
                    Transaction.created_at <= today_end,
                ).first()
                return result[0] or 0, result[1] or 0

            sell_count, sell_qty = _sum_by_type(TransactionType.SELL)
            add_count, add_qty = _sum_by_type(TransactionType.ADD)
            remove_count, remove_qty = _sum_by_type(TransactionType.REMOVE)

            total_transactions = sell_count + add_count + remove_count
            balance_neto = add_qty - sell_qty - remove_qty

        # --- Formatear reporte ---
        date_str = today.strftime("%d/%m/%Y")
        text = (
            f"📊 *RESUMEN DEL DÍA — {date_str}*\n"
            f"═══════════════════\n\n"
            f"📤 Ventas: {sell_qty} unidades ({sell_count} transacciones)\n"
            f"📥 Ingresos: {add_qty} unidades ({add_count} transacciones)\n"
            f"⚠️ Mermas: {remove_qty} unidades ({remove_count} transacciones)\n"
            f"───────────────────\n"
            f"📊 Balance Neto: {'+' if balance_neto >= 0 else ''}{balance_neto} unidades\n"
            f"📋 Transacciones Totales: {total_transactions}\n\n"
        )

        if total_transactions == 0:
            text += "ℹ️ No se registran movimientos asentados hoy.\n\n"
        elif remove_qty > sell_qty and remove_qty > 0:
            text += (
                "⚠️ *OBSERVACIÓN DEL AGENTE:* Las mermas superan a las ventas hoy. "
                "Revisa si hay un problema con la calidad del lote.\n\n"
            )

        text += "Escribe *menu* para volver al menú principal."

        # --- Log de actividad ---
        try:
            with get_db() as db2:
                log = AgentLog(
                    agent_type=AgentType.COORDINATOR,
                    action="daily_summary",
                    message=(
                        f"Resumen del día generado | Ventas: {sell_qty} | "
                        f"Ingresos: {add_qty} | Mermas: {remove_qty}"
                    ),
                    status="success",
                )
                db2.add(log)
                db2.commit()
        except Exception:
            pass

        inform_msg = create_message(
            performative="inform",
            sender=AGENT_NAME,
            receiver=sender,
            content={
                "action": "daily_summary",
                "success": True,
                "data": {
                    "sells": sell_qty,
                    "adds": add_qty,
                    "removes": remove_qty,
                    "total": total_transactions,
                    "balance": balance_neto,
                },
            },
        )

        return {
            "operation_success": True,
            "requires_alert": False,
            "response_text": text,
            "messages": [inform_msg],
        }

    except Exception as e:
        logger.error(f"Error generando resumen del día: {e}", exc_info=True)
        return {
            "operation_success": False,
            "response_text": "❌ Error al generar el resumen del día.\n\nEscribe *menu* para volver.",
        }


# =============================================================================
# Funciones Auxiliares
# =============================================================================

from typing import Optional

def _find_last_request(messages: list) -> Optional[dict]:
    """Encuentra el último mensaje de tipo request en la cola"""
    for msg in reversed(messages):
        if isinstance(msg, dict) and msg.get("performative") == "request":
            return msg
    return None


def _check_merma_anomaly(variant_id: int, stock_total: int) -> Optional[dict]:
    """
    Detecta anomalías en mermas del día (Autonomía/Reactividad).
    Si las mermas de hoy superan el 30% del stock total, es anómalo.
    """
    try:
        today_start = datetime.combine(date.today(), datetime.min.time())
        with get_db() as db:
            removed_today = db.query(
                func.sum(Transaction.quantity)
            ).filter(
                Transaction.variant_id == variant_id,
                Transaction.transaction_type == TransactionType.REMOVE,
                Transaction.created_at >= today_start,
            ).scalar() or 0

        base = stock_total + removed_today
        if base > 0 and removed_today >= (base * 0.3):
            return {
                "removed_today": removed_today,
                "threshold_pct": 30,
                "message": (
                    f"Se han registrado {removed_today} unidades como merma hoy, "
                    f"lo cual es inusualmente alto."
                ),
            }
    except Exception as e:
        logger.error(f"Error calculando anomalía diaria: {e}")

    return None


def _log_error(action: str, variant_sku: str, quantity: int, error: str):
    """Registra errores en logs de agente"""
    try:
        with get_db() as db:
            error_log = AgentLog(
                agent_type=AgentType.COORDINATOR,
                action=f"inventory_{action}_error",
                message=f"Error en operación {action}: {error}",
                log_metadata=str({
                    "variant_sku": variant_sku,
                    "quantity": quantity,
                }),
                status="error",
            )
            db.add(error_log)
            db.commit()
    except Exception:
        logger.error("Error adicional al registrar log de error")
