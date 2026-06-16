"""
Grafo de Inventario MAS-CIS — LangGraph StateGraph
===================================================
Implementa el Sistema Multiagente como una Máquina de Estados Finitos formal
usando LangGraph para gestionar el ciclo de vida y las transiciones de estados.

Nodos:
  - store_node:       Agente de Tienda (procesa menú numérico del vendedor)
  - coordinator_node: Agente Coordinador (valida y ejecuta transacciones atómicas)

Aristas:
  START → store_node → route_after_store → (coordinator_node | END)
  coordinator_node → END

Universidad Nacional Mayor de San Marcos — Tesis MAS-CIS
"""
from typing import TypedDict, Optional, Dict, Any, Literal
from datetime import datetime
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import joinedload

from src.database.connection import get_db
from src.database.models import (
    ProductVariant, Transaction, TransactionType,
    AgentLog, AgentType
)
from src.database.repository import product_repository
from src.utils.validators import InventoryValidator
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# =============================================================================
# Estado del Grafo (TypedDict requerido por LangGraph)
# =============================================================================

class AgentState(TypedDict):
    """
    Estado inmutable del grafo LangGraph.
    Representa el contexto completo de una interacción del vendedor.
    Cada campo es actualizado por los nodos del grafo mediante retorno parcial.
    """
    vendor_phone: str              # Número del vendedor (identifica la sesión)
    raw_text: str                  # Texto que envió el usuario ("1", "2", "3", etc.)
    current_step: str              # Estado FSM: MAIN_MENU, SELECT_PRODUCT, SELECT_SIZE, ENTER_QUANTITY, CONFIRM
    action: Optional[str]          # Acción seleccionada: "sell" | "add" | "remove" | None
    product_sku: Optional[str]     # SKU base del producto (ej: "POLO-BLANCO")
    product_name: Optional[str]    # Nombre para mostrar (ej: "Polo Blanco")
    variant_id: Optional[int]      # ID de la variante seleccionada en BD
    variant_sku: Optional[str]     # SKU de la variante (ej: "POLO-BLANCO-M")
    size: Optional[str]            # Talla seleccionada (ej: "M", "L")
    quantity: Optional[int]        # Cantidad ingresada por el vendedor
    response_text: str             # Texto de respuesta final para enviar por WhatsApp
    requires_coordinator: bool     # Flag de enrutamiento: True → coordinator_node
    operation_success: bool        # Resultado de la transacción del coordinador
    size_options: Optional[dict]   # Mapa temporal: "1" → {id, sku, size, stock}


# =============================================================================
# Catálogo de Productos y Mapas de Acciones (Fijos para el prototipo)
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
# Nodo: Agente de Tienda (store_node)
# =============================================================================

def store_node(state: AgentState) -> Dict[str, Any]:
    """
    Nodo del Agente de Tienda.
    Procesa el input numérico del vendedor según el paso actual del FSM
    (current_step) y genera el menú de texto correspondiente.

    Transiciones:
        MAIN_MENU      → SELECT_PRODUCT (si elige acción 1/2/3)
        MAIN_MENU      → MAIN_MENU      (si elige inventario 4)
        SELECT_PRODUCT → SELECT_SIZE
        SELECT_SIZE    → ENTER_QUANTITY
        ENTER_QUANTITY → CONFIRM
        CONFIRM        → coordinator_node (si confirma)
        CONFIRM        → MAIN_MENU       (si cancela)
        Cualquiera     → MAIN_MENU       (si escribe 0, menu, salir, cancelar)
    """
    raw_text = state["raw_text"].strip().lower()
    current_step = state["current_step"]

    logger.info(
        f"📱 store_node | step={current_step} | "
        f"input='{raw_text}' | phone={state['vendor_phone']}"
    )

    # --- Comandos globales de reinicio ---
    if raw_text in ["menu", "menú", "salir", "cancelar", "hola"]:
        return _reset_to_main_menu()

    # Opción "0" = volver al menú (en cualquier paso excepto ENTER_QUANTITY)
    if raw_text == "0" and current_step != "ENTER_QUANTITY":
        return _reset_to_main_menu()

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
    logger.warning(f"Estado desconocido: {current_step}. Reiniciando.")
    return _reset_to_main_menu()


# =============================================================================
# Handlers internos del store_node (lógica por paso)
# =============================================================================

def _reset_to_main_menu() -> Dict[str, Any]:
    """Reinicia todos los campos y muestra el menú principal"""
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
    """Procesa la selección del menú principal"""
    # Opción 4: Ver inventario
    if raw_text == "4":
        return {
            "current_step": "MAIN_MENU",
            "requires_coordinator": False,
            "response_text": _build_inventory_text(),
        }

    # Opciones 1, 2, 3: Acciones transaccionales
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


def _handle_product_selection(raw_text: str, state: AgentState) -> Dict[str, Any]:
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

    return {
        "current_step": "SELECT_SIZE",
        "product_sku": product["sku"],
        "product_name": product["name"],
        "requires_coordinator": False,
        "response_text": size_text,
        "size_options": size_options,
    }


def _handle_size_selection(raw_text: str, state: AgentState) -> Dict[str, Any]:
    """Procesa la selección de talla"""
    size_options = state.get("size_options") or {}

    if raw_text not in size_options:
        # Regenerar menú de tallas para el mensaje de error
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


def _handle_quantity_input(raw_text: str, state: AgentState) -> Dict[str, Any]:
    """Procesa y valida la cantidad ingresada"""
    # Validar que sea un número entero positivo
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

    # Validar stock para ventas y mermas
    if state["action"] in ["sell", "remove"]:
        variant = product_repository.find_variant(sku=state["variant_sku"])
        stock_available = variant.stock_total if variant else 0

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

    return {
        "current_step": "CONFIRM",
        "quantity": quantity,
        "requires_coordinator": False,
        "response_text": _build_confirmation(
            state["action"],
            state["product_name"],
            state["size"],
            quantity,
        ),
    }


def _handle_confirmation(raw_text: str, state: AgentState) -> Dict[str, Any]:
    """Procesa la confirmación o cancelación de la operación"""
    if raw_text == "2":
        # Cancelar operación
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
        # Confirmar → delegar al coordinator_node
        return {
            "current_step": "MAIN_MENU",
            "requires_coordinator": True,
            "response_text": "",  # Lo completará el coordinator_node
            "size_options": None,
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
            )
        ),
    }


# =============================================================================
# Nodo: Agente Coordinador (coordinator_node)
# =============================================================================

def coordinator_node(state: AgentState) -> Dict[str, Any]:
    """
    Nodo del Agente Coordinador.
    Ejecuta la transacción atómica sobre ProductVariant,
    registra en las tablas Transaction (Kárdex) y AgentLog,
    y genera el mensaje de resultado.

    Operaciones soportadas:
      - sell:   Reduce stock_physical (venta)
      - add:    Incrementa stock_physical (ingreso del taller)
      - remove: Reduce stock_physical (merma/daño)
    """
    action = state["action"]
    variant_sku = state["variant_sku"]
    quantity = state["quantity"]
    vendor_phone = state["vendor_phone"]

    logger.info(
        f"🔄 coordinator_node | action={action} | "
        f"sku={variant_sku} | qty={quantity}"
    )

    validator = InventoryValidator()

    try:
        with get_db() as db:
            # --- Buscar la variante en la BD ---
            variant = (
                db.query(ProductVariant)
                .options(joinedload(ProductVariant.product))
                .filter(ProductVariant.sku == variant_sku)
                .first()
            )

            if not variant:
                logger.error(f"Variante no encontrada: {variant_sku}")
                return {
                    "operation_success": False,
                    "response_text": (
                        f"❌ Error: Variante no encontrada ({variant_sku}).\n\n"
                        f"Escribe *menu* para volver."
                    ),
                }

            # --- Validar operación con reglas de negocio ---
            current_stock = variant.stock_physical
            validation = validator.validate_stock_operation(
                product_sku=variant_sku,
                quantity=quantity,
                operation=action,
                current_stock=(
                    current_stock if action in ["sell", "remove"] else None
                ),
            )

            if not validation["valid"]:
                error_msg = ", ".join(validation["errors"])
                logger.warning(f"Validación fallida: {error_msg}")
                return {
                    "operation_success": False,
                    "response_text": (
                        f"❌ Error de validación: {error_msg}\n\n"
                        f"Escribe *menu* para volver."
                    ),
                }

            # --- Ejecutar operación atómica sobre ProductVariant ---
            previous_stock = variant.stock_physical

            if action == "sell":
                variant.stock_physical -= quantity
                tx_type = TransactionType.SELL
                notes = f"Venta registrada por {vendor_phone}"
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
                    "response_text": (
                        f"❌ Acción no reconocida: {action}\n\n"
                        f"Escribe *menu* para volver."
                    ),
                }

            # Recalcular stock total
            variant.stock_total = variant.stock_physical + variant.stock_virtual
            variant.updated_at = datetime.utcnow()

            # Actualizar timestamp del producto padre
            variant.product.updated_at = datetime.utcnow()

            # --- Registrar transacción en el Kárdex ---
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
                }),
                status="success",
            )
            db.add(agent_log)

            # Commit atómico (connection.py hace auto-rollback en error)
            db.commit()

            # Capturar datos para respuesta (antes de cerrar sesión)
            product_name = variant.product.name
            variant_size = variant.size
            new_stock = variant.stock_physical
            stock_total = variant.stock_total

        # --- Generar respuesta de éxito ---
        logger.info(
            f"✅ Operación exitosa: {action} | {variant_sku} | "
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

        return {
            "operation_success": True,
            "response_text": response,
        }

    except Exception as e:
        logger.error(f"❌ Error en coordinator_node: {e}", exc_info=True)

        # Registrar error en logs de agente
        try:
            with get_db() as db:
                error_log = AgentLog(
                    agent_type=AgentType.COORDINATOR,
                    action=f"inventory_{action}_error",
                    message=f"Error en operación {action}: {str(e)}",
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

        return {
            "operation_success": False,
            "response_text": (
                "❌ Error interno al procesar la operación.\n\n"
                "Escribe *menu* para volver al menú principal."
            ),
        }


# =============================================================================
# Función de Enrutamiento Condicional
# =============================================================================

def route_after_store(state: AgentState) -> Literal["coordinator_node", "__end__"]:
    """
    Arista condicional del grafo LangGraph.
    Determina si el flujo debe continuar hacia el coordinator_node
    (transacción confirmada) o finalizar el grafo (navegación/consulta).
    """
    if state.get("requires_coordinator", False):
        logger.info("🔀 Enrutando → coordinator_node (transacción pendiente)")
        return "coordinator_node"

    logger.info("🔀 Finalizando grafo (sin transacción)")
    return END


# =============================================================================
# Funciones Auxiliares — Generación de Menús de Texto
# =============================================================================

def _build_main_menu() -> str:
    """Genera el texto del menú principal numerado"""
    return (
        "🤖 *MAS-CIS - Menú Principal*\n"
        "═══════════════════\n\n"
        "Selecciona una opción:\n\n"
        "1️⃣  📦 Registrar Venta\n"
        "2️⃣  ➕ Registrar Ingreso\n"
        "3️⃣  ⚠️ Registrar Merma\n"
        "4️⃣  📋 Ver Inventario\n\n"
        "👉 Escribe el número de la opción:"
    )


def _build_product_menu(action: str) -> str:
    """Genera el menú de selección de producto (polos)"""
    verb = ACTION_VERBS.get(action, "seleccionas")
    return (
        f"📦 ¿Qué polo {verb}?\n\n"
        "1️⃣  Polo Blanco\n"
        "2️⃣  Polo Negro\n"
        "3️⃣  Polo Azul\n"
        "0️⃣  ↩️ Volver al menú\n\n"
        "👉 Escribe el número:"
    )


def _build_size_menu(product_sku: str, product_name: str) -> tuple:
    """
    Genera el menú de tallas con stock desde la base de datos.

    Args:
        product_sku: SKU base del producto
        product_name: Nombre del producto para mostrar

    Returns:
        Tupla (texto_menu, mapa_opciones)
        mapa_opciones: {"1": {"id": int, "sku": str, "size": str, "stock": int}, ...}
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
        if stock > 5:
            emoji = "✅"
        elif stock > 0:
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
    action: str, product_name: str, size: str, quantity: int
) -> str:
    """Genera el resumen de confirmación con opciones numéricas"""
    op_name = ACTION_NAMES.get(action, "OPERACIÓN")
    return (
        f"📋 *Confirma la operación:*\n\n"
        f"Operación: *{op_name}*\n"
        f"Producto: {product_name}\n"
        f"Talla: {size}\n"
        f"Cantidad: {quantity} unidades\n\n"
        f"¿Es correcto?\n\n"
        f"1️⃣  ✅ Confirmar\n"
        f"2️⃣  ❌ Cancelar\n\n"
        f"👉 Escribe el número:"
    )


def _build_inventory_text() -> str:
    """Genera el texto del inventario completo desde la BD"""
    products = product_repository.list_all_products()

    if not products:
        return (
            "📭 No hay productos registrados en el inventario.\n\n"
            "Escribe *menu* para volver."
        )

    text = "📋 *INVENTARIO ACTUAL*\n"
    text += "═" * 20 + "\n\n"

    for product in products:
        text += f"📦 *{product.name}*\n"
        text += f"   📊 Stock total: {product.total_stock} unidades\n"

        if product.variants:
            for v in product.variants:
                if v.stock_total > 5:
                    emoji = "✅"
                elif v.stock_total > 0:
                    emoji = "⚠️"
                else:
                    emoji = "❌"
                text += f"      {emoji} Talla {v.size}: {v.stock_total}\n"

        text += "\n"

    text += "─" * 20 + "\n"
    text += "Escribe *menu* para volver."

    return text


# =============================================================================
# Funciones de Info para la API del Dashboard
# =============================================================================

def get_store_agent_info() -> Dict[str, Any]:
    """Retorna información del agente de tienda para el endpoint /api/dashboard/agents"""
    return {
        "agent_id": "store_agent_langgraph",
        "agent_type": "store",
        "status": "idle",
        "created_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat(),
    }


def get_coordinator_agent_info() -> Dict[str, Any]:
    """Retorna información del agente coordinador para el endpoint /api/dashboard/agents"""
    return {
        "agent_id": "coordinator_agent_langgraph",
        "agent_type": "coordinator",
        "status": "idle",
        "created_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Helper para invocaciones desde la API REST (no WhatsApp)
# =============================================================================

def process_api_stock_update(
    action: str, variant_sku: str, quantity: int, vendor_phone: str = "API"
) -> Dict[str, Any]:
    """
    Procesa una actualización de stock desde la API REST.
    Invoca el grafo con un estado que va directo al coordinator_node.

    Args:
        action: "sell" | "add" | "remove"
        variant_sku: SKU de la variante a actualizar
        quantity: Cantidad a operar
        vendor_phone: Identificador del origen (default: "API")

    Returns:
        Dict con success, error, y response_text
    """
    initial_state: AgentState = {
        "vendor_phone": vendor_phone,
        "raw_text": "1",
        "current_step": "CONFIRM",
        "action": action,
        "product_sku": None,
        "product_name": None,
        "variant_id": None,
        "variant_sku": variant_sku,
        "size": None,
        "quantity": quantity,
        "response_text": "",
        "requires_coordinator": True,
        "operation_success": False,
        "size_options": None,
    }

    result = inventory_graph.invoke(initial_state)

    return {
        "success": result.get("operation_success", False),
        "error": (
            result.get("response_text", "")
            if not result.get("operation_success")
            else None
        ),
        "response_text": result.get("response_text", ""),
    }


# =============================================================================
# Construcción y Compilación del Grafo LangGraph
# =============================================================================

def _build_graph() -> StateGraph:
    """
    Construye el StateGraph de LangGraph con los nodos y aristas del sistema.

    Topología:
        START → store_node → route_after_store → coordinator_node → END
                                              └→ END
    """
    workflow = StateGraph(AgentState)

    # Registrar nodos
    workflow.add_node("store_node", store_node)
    workflow.add_node("coordinator_node", coordinator_node)

    # Punto de entrada del grafo
    workflow.set_entry_point("store_node")

    # Arista condicional: store_node → coordinator_node | END
    workflow.add_conditional_edges(
        "store_node",
        route_after_store,
        {
            "coordinator_node": "coordinator_node",
            END: END,
        },
    )

    # Arista fija: coordinator_node → END
    workflow.add_edge("coordinator_node", END)

    return workflow


# --- Compilar el grafo (variable global lista para uso) ---
inventory_graph = _build_graph().compile()

logger.info("✅ Grafo de inventario LangGraph compilado exitosamente")
