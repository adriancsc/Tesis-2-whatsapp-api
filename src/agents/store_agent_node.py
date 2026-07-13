"""
Nodo del Agente de Tienda (Store Agent) — LangGraph
=====================================================
Agente autónomo responsable de la interacción bidireccional
con el vendedor del stand a través de WhatsApp.

Propiedades MAS (Wooldridge & Jennings, 1995):
    - Autonomía:    Rechaza inputs inválidos, bloquea operaciones sin stock.
    - Reactividad:  Percibe el inventario en tiempo real para construir menús
                    dinámicos con indicadores de stock (✅/⚠️/❌).
    - Proactividad: Advierte al vendedor cuando una operación consume >50%
                    del stock o cuando el producto está agotado.
    - Habilidad Social: Se comunica con el CoordinatorAgent mediante
                    mensajes estructurados (request/inform/refuse).

Casos de Uso implementados:
    - CU-01: Registrar Venta Presencial vía WhatsApp
    - CU-02: Registrar Abastecimiento de Mercadería vía WhatsApp
    - CU-03: Registrar Merma / Prenda Fallada vía WhatsApp
    - CU-07: Consultar Inventario (delegado al Coordinador)
    - CU-08: Resumen del Día (delegado al Coordinador)

Transiciones del FSM:
    MAIN_MENU      → SELECT_PRODUCT (si elige acción 1/2/3)
    MAIN_MENU      → coordinator (si elige inventario 4 o resumen 5)
    SELECT_PRODUCT → SELECT_SIZE
    SELECT_SIZE    → ENTER_QUANTITY
    ENTER_QUANTITY → CONFIRM
    CONFIRM        → coordinator_agent (si confirma)
    CONFIRM        → MAIN_MENU       (si cancela)
    Cualquiera     → MAIN_MENU       (si escribe 0, menu, salir, cancelar)
"""
from typing import Dict, Any

from src.agents.state import MASState, create_message
from src.database.repository import product_repository
from src.utils.reservation_manager import reservation_manager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Nombre del agente (para mensajes inter-agente)
AGENT_NAME = "store_agent"


# =============================================================================
# Catálogo de Productos y Mapas de Acciones
# =============================================================================

PRODUCT_CATALOG = {
    "1": {"sku": "POLO-BLANCO", "name": "Polo Blanco"},
    "2": {"sku": "POLO-NEGRO", "name": "Polo Negro"},
    "3": {"sku": "POLO-AZUL", "name": "Polo Azul"},
}

ACTION_MAP = {
    "1": "sell",
    "2": "add",
    "3": "remove",
}

ACTION_NAMES = {
    "sell": "VENTA",
    "add": "INGRESO",
    "remove": "MERMA",
}

ACTION_VERBS = {
    "sell": "vendiste",
    "add": "ingresó del taller",
    "remove": "presenta falla",
}


# =============================================================================
# Nodo Principal: store_agent_node
# =============================================================================

def store_agent_node(state: MASState) -> Dict[str, Any]:
    """
    Nodo del Agente de Tienda en el grafo LangGraph.

    Procesa el input numérico del vendedor según el paso actual del FSM
    (current_step), genera los menús de texto correspondientes para WhatsApp,
    y cuando se requiere una transacción o consulta, crea un mensaje
    estructurado (request) dirigido al Agente Coordinador.

    Args:
        state: Estado actual del grafo MAS (MASState)

    Returns:
        Dict con las actualizaciones parciales del estado, incluyendo
        mensajes inter-agente en la cola `messages`.
    """
    raw_text = state["raw_text"].strip().lower()
    current_step = state["current_step"]

    logger.info(
        f"🏪 StoreAgent | step={current_step} | "
        f"input='{raw_text}' | phone={state.get('vendor_phone', 'N/A')}"
    )

    # --- Comandos globales de reinicio ---
    if raw_text in ["menu", "menú", "salir", "cancelar", "hola"]:
        return _reset_to_main_menu(vendor_phone=state.get("vendor_phone"))

    # Opción "0" = volver al menú (en cualquier paso excepto ENTER_QUANTITY)
    if raw_text == "0" and current_step != "ENTER_QUANTITY":
        return _reset_to_main_menu(vendor_phone=state.get("vendor_phone"))

    # === MAIN_MENU ===
    if current_step == "MAIN_MENU":
        return _handle_main_menu(raw_text)

    # === SELECT_PRODUCT ===
    elif current_step == "SELECT_PRODUCT":
        return _handle_product_selection(raw_text, state)

    # === SELECT_SIZE ===
    elif current_step == "SELECT_SIZE":
        return _handle_size_selection(raw_text, state)

    # === ENTER_QUANTITY ===
    elif current_step == "ENTER_QUANTITY":
        return _handle_quantity_input(raw_text, state)

    # === CONFIRM ===
    elif current_step == "CONFIRM":
        return _handle_confirmation(raw_text, state)

    # Estado desconocido → reiniciar al menú principal
    logger.warning(f"Estado FSM desconocido: {current_step}. Reiniciando.")
    return _reset_to_main_menu()


# =============================================================================
# Handlers Internos (lógica por paso del FSM)
# =============================================================================

def _reset_to_main_menu(vendor_phone: str = None) -> Dict[str, Any]:
    """Reinicia todos los campos y muestra el menú principal.
    Libera cualquier reserva temporal activa del vendedor."""
    # Liberar reserva activa si existe (el vendedor canceló o reinició)
    if vendor_phone:
        reservation_manager.release(vendor_phone)
    return {
        "current_step": "MAIN_MENU",
        "action": None,
        "product_sku": None,
        "product_name": None,
        "variant_id": None,
        "variant_sku": None,
        "size": None,
        "quantity": None,
        "requires_coordinator": False,
        "response_text": _build_main_menu(),
        "size_options": None,
    }


def _handle_main_menu(raw_text: str) -> Dict[str, Any]:
    """
    Procesa la selección del menú principal.

    Opciones 1-3: Transacciones (sell/add/remove) → navega FSM
    Opción 4: Consultar Inventario → delega al Coordinador (CU-07)
    Opción 5: Resumen del Día → delega al Coordinador (CU-08)
    """
    # --- Opción 4: Consultar Inventario (CU-07) ---
    # Comunicación inter-agente: StoreAgent → request → CoordinatorAgent
    if raw_text == "4":
        msg = create_message(
            performative="request",
            sender=AGENT_NAME,
            receiver="coordinator_agent",
            content={
                "action": "query",
                "description": "Solicitud de consulta de inventario completo",
            },
        )
        logger.info("🏪 StoreAgent envía request(query) → CoordinatorAgent")
        return {
            "current_step": "MAIN_MENU",
            "action": "query",
            "requires_coordinator": True,
            "response_text": "",
            "messages": [msg],
        }

    # --- Opción 5: Resumen del Día (CU-08) ---
    # Comunicación inter-agente: StoreAgent → request → CoordinatorAgent
    if raw_text == "5":
        msg = create_message(
            performative="request",
            sender=AGENT_NAME,
            receiver="coordinator_agent",
            content={
                "action": "daily_summary",
                "description": "Solicitud de consolidado de movimientos del día",
            },
        )
        logger.info("🏪 StoreAgent envía request(daily_summary) → CoordinatorAgent")
        return {
            "current_step": "MAIN_MENU",
            "action": "daily_summary",
            "requires_coordinator": True,
            "response_text": "",
            "messages": [msg],
        }

    # --- Opciones 1, 2, 3: Acciones transaccionales ---
    if raw_text in ACTION_MAP:
        action = ACTION_MAP[raw_text]
        return {
            "current_step": "SELECT_PRODUCT",
            "action": action,
            "product_sku": None,
            "product_name": None,
            "variant_id": None,
            "variant_sku": None,
            "size": None,
            "quantity": None,
            "requires_coordinator": False,
            "response_text": _build_product_menu(action),
            "size_options": None,
        }

    # Input no reconocido
    return {
        "requires_coordinator": False,
        "response_text": "❌ Opción no válida.\n\n" + _build_main_menu(),
    }


def _handle_product_selection(raw_text: str, state: MASState) -> Dict[str, Any]:
    """Procesa la selección de producto"""
    if raw_text not in PRODUCT_CATALOG:
        return {
            "requires_coordinator": False,
            "response_text": (
                "❌ Opción no válida.\n\n"
                + _build_product_menu(state["action"])
            ),
        }

    product = PRODUCT_CATALOG[raw_text]
    size_text, size_options = _build_size_menu(product["sku"], product["name"])

    if not size_options:
        return {
            "current_step": "MAIN_MENU",
            "requires_coordinator": False,
            "response_text": (
                f"❌ No se encontraron tallas para {product['name']}.\n\n"
                + _build_main_menu()
            ),
            "size_options": None,
        }

    # Bloqueo preventivo (Autonomía): Si quiere vender pero no hay stock
    if state["action"] == "sell":
        total_stock = sum(v["stock"] for v in size_options.values())
        if total_stock == 0:
            return {
                "current_step": "MAIN_MENU",
                "requires_coordinator": False,
                "response_text": (
                    f"⛔ *OPERACIÓN DENEGADA (Agente de Tienda)*\n\n"
                    f"El producto *{product['name']}* está 100% agotado "
                    f"en todas sus tallas.\n"
                    f"No puedes registrar ventas de este producto en "
                    f"este momento.\n\n"
                    + _build_main_menu()
                ),
                "size_options": None,
            }

    return {
        "current_step": "SELECT_SIZE",
        "product_sku": product["sku"],
        "product_name": product["name"],
        "requires_coordinator": False,
        "response_text": size_text,
        "size_options": size_options,
    }


def _handle_size_selection(raw_text: str, state: MASState) -> Dict[str, Any]:
    """Procesa la selección de talla"""
    size_options = state.get("size_options") or {}

    if raw_text not in size_options:
        size_text, _ = _build_size_menu(
            state["product_sku"], state["product_name"]
        )
        return {
            "requires_coordinator": False,
            "response_text": "❌ Opción no válida.\n\n" + size_text,
        }

    variant_info = size_options[raw_text]
    return {
        "current_step": "ENTER_QUANTITY",
        "variant_id": variant_info["id"],
        "variant_sku": variant_info["sku"],
        "size": variant_info["size"],
        "requires_coordinator": False,
        "response_text": _build_quantity_prompt(
            state["action"],
            state["product_name"],
            variant_info["size"],
            variant_info["stock"],
        ),
    }


def _handle_quantity_input(raw_text: str, state: MASState) -> Dict[str, Any]:
    """Procesa y valida la cantidad ingresada"""
    try:
        quantity = int(raw_text)
        if quantity <= 0:
            raise ValueError("Cantidad debe ser mayor a 0")
    except ValueError:
        return {
            "requires_coordinator": False,
            "response_text": (
                "❌ Ingresa un número válido mayor a 0.\n"
                "👉 Escribe la cantidad:"
            ),
        }

    # Validar stock para ventas y mermas (Autonomía del agente)
    if state["action"] in ["sell", "remove"]:
        variant = product_repository.find_variant(sku=state["variant_sku"])
        stock_in_db = variant.stock_total if variant else 0
        # Descontar reservas activas de OTROS vendedores para este producto
        reserved_by_others = reservation_manager.get_reserved_quantity(
            variant.id if variant else 0
        )
        stock_available = stock_in_db - reserved_by_others

        if quantity > stock_available:
            return {
                "current_step": "MAIN_MENU",
                "quantity": None,
                "requires_coordinator": False,
                "response_text": (
                    f"❌ *STOCK INSUFICIENTE*\n\n"
                    f"Producto: {state['product_name']} - Talla {state['size']}\n"
                    f"Stock disponible: {stock_available}\n"
                    f"Cantidad solicitada: {quantity}\n\n"
                    f"No se puede procesar la operación.\n\n"
                    + _build_main_menu()
                ),
                "size_options": None,
            }

    # Crear reserva temporal para ventas (protege el stock por 10 min)
    if state["action"] == "sell":
        variant = product_repository.find_variant(sku=state["variant_sku"])
        if variant:
            reservation_manager.reserve(
                vendor_phone=state.get("vendor_phone", "unknown"),
                variant_id=variant.id,
                variant_sku=state["variant_sku"],
                quantity=quantity,
            )

    return {
        "current_step": "CONFIRM",
        "quantity": quantity,
        "requires_coordinator": False,
        "response_text": _build_confirmation(
            state["action"],
            state["product_name"],
            state["size"],
            quantity,
            state.get("variant_sku"),
        ),
    }


def _handle_confirmation(raw_text: str, state: MASState) -> Dict[str, Any]:
    """
    Procesa la confirmación o cancelación de la operación.

    Si confirma (1): Crea un mensaje request al CoordinatorAgent
    con todos los datos de la transacción (Habilidad Social).

    Si cancela (2): Reinicia al menú principal.
    """
    if raw_text == "2":
        # Cancelar operación — liberar reserva temporal si existe
        reservation_manager.release(state.get("vendor_phone", ""))
        return {
            "current_step": "MAIN_MENU",
            "action": None,
            "product_sku": None,
            "product_name": None,
            "variant_id": None,
            "variant_sku": None,
            "size": None,
            "quantity": None,
            "requires_coordinator": False,
            "response_text": "❌ Operación cancelada.\n\n" + _build_main_menu(),
            "size_options": None,
        }

    if raw_text == "1":
        # Verificar que la reserva temporal no haya expirado (para ventas)
        vendor_phone = state.get("vendor_phone", "")
        if state["action"] == "sell":
            active_reservation = reservation_manager.get_vendor_reservation(vendor_phone)
            if not active_reservation:
                # La reserva expiró (pasaron más de 10 minutos)
                return {
                    "current_step": "MAIN_MENU",
                    "action": None,
                    "product_sku": None,
                    "product_name": None,
                    "variant_id": None,
                    "variant_sku": None,
                    "size": None,
                    "quantity": None,
                    "requires_coordinator": False,
                    "response_text": (
                        "⏰ *RESERVA EXPIRADA*\n\n"
                        "Pasaron más de 10 minutos desde que seleccionaste "
                        "el producto. El stock fue liberado para otros canales.\n"
                        "Por favor, inicia la venta de nuevo.\n\n"
                        + _build_main_menu()
                    ),
                    "size_options": None,
                }

        # Consumir la reserva (ya no se necesita, el Coordinador ejecutará la BD)
        if state["action"] == "sell":
            reservation_manager.consume(vendor_phone)

        # Confirmar → crear mensaje request al CoordinatorAgent
        msg = create_message(
            performative="request",
            sender=AGENT_NAME,
            receiver="coordinator_agent",
            content={
                "action": state["action"],
                "variant_sku": state["variant_sku"],
                "variant_id": state["variant_id"],
                "product_name": state["product_name"],
                "size": state["size"],
                "quantity": state["quantity"],
                "channel": "physical",
                "description": (
                    f"Solicitud de {ACTION_NAMES.get(state['action'], 'operación')} "
                    f"de {state['quantity']} unidad(es) de {state['product_name']} "
                    f"talla {state['size']}"
                ),
            },
        )
        logger.info(
            f"🏪 StoreAgent envía request({state['action']}) → CoordinatorAgent | "
            f"SKU={state['variant_sku']} | Qty={state['quantity']}"
        )

        return {
            "current_step": "MAIN_MENU",
            "requires_coordinator": True,
            "response_text": "",  # Lo completará el CoordinatorAgent
            "size_options": None,
            "messages": [msg],
        }

    # Input no válido
    return {
        "requires_coordinator": False,
        "response_text": (
            "❌ Opción no válida.\n\n"
            + _build_confirmation(
                state["action"],
                state["product_name"],
                state["size"],
                state["quantity"],
                state.get("variant_sku"),
            )
        ),
    }


# =============================================================================
# Funciones Auxiliares — Generación de Menús de Texto
# =============================================================================

def _build_main_menu() -> str:
    """Genera el texto del menú principal numerado (incluye CU-08)"""
    return (
        "🤖 *MAS-CIS - Menú Principal*\n"
        "═══════════════════\n\n"
        "Selecciona una opción:\n\n"
        "1️⃣  📦 Registrar Venta\n"
        "2️⃣  ➕ Registrar Ingreso\n"
        "3️⃣  ⚠️ Registrar Merma\n"
        "4️⃣  📋 Ver Inventario\n"
        "5️⃣  📊 Resumen del Día\n\n"
        "👉 Escribe el número de la opción:"
    )


def _build_product_menu(action: str) -> str:
    """
    Genera el menú de selección de producto con percepción de inventario.

    Reactividad (Wooldridge): El agente percibe el estado actual del
    inventario en la base de datos y muestra indicadores visuales
    (✅/⚠️/❌) junto a cada producto.
    """
    verb = ACTION_VERBS.get(action, "seleccionas")

    # Percepción del inventario (Reactividad)
    products = product_repository.list_all_products()
    product_status = {}

    for p in products:
        if not p.variants:
            product_status[p.sku] = ""
            continue

        total_stock = sum(v.stock_total for v in p.variants)
        if total_stock == 0:
            product_status[p.sku] = " ❌ (Agotado)"
        elif total_stock <= 1 * len(p.variants):
            product_status[p.sku] = " ⚠️ (Stock bajo)"
        else:
            product_status[p.sku] = ""

    return (
        f"📦 ¿Qué polo {verb}?\n\n"
        f"1️⃣  Polo Blanco{product_status.get('POLO-BLANCO', '')}\n"
        f"2️⃣  Polo Negro{product_status.get('POLO-NEGRO', '')}\n"
        f"3️⃣  Polo Azul{product_status.get('POLO-AZUL', '')}\n"
        "0️⃣  ↩️ Volver al menú\n\n"
        "👉 Escribe el número:"
    )


def _build_size_menu(product_sku: str, product_name: str) -> tuple:
    """
    Genera el menú de tallas con stock desde la base de datos.

    Returns:
        Tupla (texto_menu, mapa_opciones)
    """
    products = product_repository.list_all_products()
    product = next(
        (p for p in products if p.sku == product_sku),
        None,
    )

    if not product or not product.variants:
        return ("", {})

    text = f"📏 Selecciona la talla — *{product_name}*\n\n"
    size_options = {}

    for i, v in enumerate(product.variants, 1):
        stock = v.stock_total
        if stock > 1:
            emoji = "✅"
        elif stock == 1:
            emoji = "⚠️"
        else:
            emoji = "❌"

        text += f"{i}️⃣  Talla {v.size}  (Stock: {stock} {emoji})\n"
        size_options[str(i)] = {
            "id": v.id,
            "sku": v.sku,
            "size": v.size,
            "stock": v.stock_total,
        }

    text += "0️⃣  ↩️ Volver\n\n"
    text += "👉 Escribe el número:"

    return (text, size_options)


def _build_quantity_prompt(
    action: str, product_name: str, size: str, stock: int
) -> str:
    """Genera el prompt para ingresar la cantidad"""
    verb = ACTION_VERBS.get(action, "seleccionaste")
    return (
        f"🔢 ¿Cuántas unidades {verb}?\n\n"
        f"Producto: *{product_name}* — Talla *{size}*\n"
        f"Stock disponible: {stock}\n\n"
        f"👉 Escribe la cantidad (ejemplo: 2):"
    )


def _build_confirmation(
    action: str, product_name: str, size: str, quantity: int,
    variant_sku: str = None,
) -> str:
    """Genera el resumen de confirmación con opciones numéricas"""
    op_name = ACTION_NAMES.get(action, "OPERACIÓN")

    # Contexto adaptativo (Reactividad): Advertencia si consume mucho stock
    warning_text = ""
    if action in ["sell", "remove"] and variant_sku:
        variant = product_repository.find_variant(sku=variant_sku)
        if variant and variant.stock_total > 0:
            if quantity >= (variant.stock_total * 0.5) and variant.stock_total >= 4:
                warning_text = (
                    "\n⚠️ *ADVERTENCIA (Agente de Tienda)*: "
                    "Esta operación consumirá el 50% o más del "
                    "stock disponible de esta variante.\n"
                )

    return (
        f"📋 *Confirma la operación:*\n\n"
        f"Operación: *{op_name}*\n"
        f"Producto: {product_name}\n"
        f"Talla: {size}\n"
        f"Cantidad: {quantity} unidades\n"
        f"{warning_text}\n"
        f"¿Es correcto?\n\n"
        f"1️⃣  ✅ Confirmar\n"
        f"2️⃣  ❌ Cancelar\n\n"
        f"👉 Escribe el número:"
    )
