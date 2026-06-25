"""
Grafo del Sistema Multiagente MAS-CIS — LangGraph StateGraph
============================================================
Ensambla y compila el StateGraph con los 4 nodos (agentes) y
aristas condicionales del sistema MAS.

Topología:
    START → route_by_source → (store_agent | sync_agent)
    
    store_agent → route_after_store → (coordinator_agent | END)
    sync_agent → coordinator_agent
    
    coordinator_agent → route_after_coordinator → (sync_agent | alert_agent | END)
    
    alert_agent → END
"""
from typing import Dict, Any, Literal
from datetime import datetime
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig

from src.agents.state import MASState
from src.agents.store_agent_node import store_agent_node
from src.agents.coordinator_agent_node import coordinator_agent_node
from src.agents.sync_agent_node import sync_agent_node
from src.agents.alert_agent_node import alert_agent_node
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# =============================================================================
# Funciones de Enrutamiento Condicional
# =============================================================================

def route_by_source(state: MASState) -> Literal["store_agent", "sync_agent"]:
    """
    Enruta el flujo inicial dependiendo del canal de origen.
    """
    source = state.get("source", "whatsapp")
    if source == "ecommerce":
        logger.info("🔀 Enrutando START → sync_agent (E-Commerce)")
        return "sync_agent"
    
    logger.info("🔀 Enrutando START → store_agent (WhatsApp)")
    return "store_agent"


def route_after_store(state: MASState) -> Literal["coordinator_agent", "__end__"]:
    """
    Determina si el StoreAgent requiere delegar una transacción
    al CoordinatorAgent o si el flujo termina aquí.
    """
    if state.get("requires_coordinator", False):
        logger.info("🔀 Enrutando store_agent → coordinator_agent (Transacción pendiente)")
        return "coordinator_agent"

    logger.info("🔀 Finalizando grafo desde store_agent (Sin transacción)")
    return END


def route_after_coordinator(state: MASState) -> Literal["sync_agent", "alert_agent", "__end__"]:
    """
    Determina la acción post-transacción del CoordinatorAgent.
    Prioridad: 
      1. AlertAgent (si hay alertas que emitir)
      2. SyncAgent (si hay stock que sincronizar con la web)
      3. END (flujo completo)
    """
    if state.get("requires_alert", False):
        logger.info("🔀 Enrutando coordinator_agent → alert_agent (Alerta requerida)")
        return "alert_agent"
        
    if state.get("requires_sync", False) or state.get("conflict_detected", False):
        logger.info("🔀 Enrutando coordinator_agent → sync_agent (Sincronización o Conflicto)")
        return "sync_agent"

    logger.info("🔀 Finalizando grafo desde coordinator_agent")
    return END


def route_after_sync(state: MASState) -> Literal["coordinator_agent", "__end__"]:
    """
    Determina la acción después del SyncAgent.
    Si fue una orden web entrante, va al CoordinatorAgent.
    Si fue un push post-venta, termina.
    """
    if state.get("requires_coordinator", False):
        logger.info("🔀 Enrutando sync_agent → coordinator_agent (Ejecutar Orden Web)")
        return "coordinator_agent"
    
    logger.info("🔀 Finalizando grafo desde sync_agent (Post-Venta / Cancelación)")
    return END


# =============================================================================
# Funciones de Info para la API del Dashboard
# =============================================================================

def get_store_agent_info() -> Dict[str, Any]:
    return {
        "agent_id": "store_agent_mas",
        "agent_type": "store",
        "status": "idle",
        "created_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat(),
    }

def get_coordinator_agent_info() -> Dict[str, Any]:
    return {
        "agent_id": "coordinator_agent_mas",
        "agent_type": "coordinator",
        "status": "idle",
        "created_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat(),
    }

def get_sync_agent_info() -> Dict[str, Any]:
    return {
        "agent_id": "sync_agent_mas",
        "agent_type": "sync",
        "status": "idle",
        "created_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat(),
    }

def get_alert_agent_info() -> Dict[str, Any]:
    return {
        "agent_id": "alert_agent_mas",
        "agent_type": "alert",
        "status": "idle",
        "created_at": datetime.utcnow().isoformat(),
        "last_activity": datetime.utcnow().isoformat(),
    }


# =============================================================================
# Helper para invocaciones desde la API REST
# =============================================================================

def process_api_stock_update(
    action: str, variant_sku: str, quantity: int, vendor_phone: str = "API"
) -> Dict[str, Any]:
    """
    Procesa una actualización de stock desde la API REST.
    """
    from src.agents.state import create_message
    
    # Crear mensaje request falso para el coordinador
    msg = create_message(
        performative="request",
        sender="api",
        receiver="coordinator_agent",
        content={
            "action": action,
            "variant_sku": variant_sku,
            "quantity": quantity,
            "channel": "api"
        }
    )
    
    initial_state: MASState = {
        "source": "api",
        "vendor_phone": vendor_phone,
        "raw_text": str(quantity),
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
        "requires_sync": False,
        "requires_alert": False,
        "conflict_detected": False,
        "operation_success": False,
        "size_options": None,
        "messages": [msg],
        "ecommerce_order_id": None,
        "ecommerce_action": None,
    }

    config: RunnableConfig = {"configurable": {"thread_id": vendor_phone}}
    # Llamamos al coordinador directamente o dejamos que siga el flujo natural
    # En este caso vamos al store_agent que enrutará porque requires_coordinator = True
    result = mas_app.invoke(initial_state, config)

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
    Construye el StateGraph de LangGraph con los 4 nodos (agentes).
    """
    workflow = StateGraph(MASState)

    # 1. Registrar nodos
    workflow.add_node("store_agent", store_agent_node)
    workflow.add_node("coordinator_agent", coordinator_agent_node)
    workflow.add_node("sync_agent", sync_agent_node)
    workflow.add_node("alert_agent", alert_agent_node)

    # 2. Punto de entrada condicional
    workflow.add_conditional_edges(
        START,
        route_by_source,
        {
            "store_agent": "store_agent",
            "sync_agent": "sync_agent",
        },
    )

    # 3. Flujo del StoreAgent
    workflow.add_conditional_edges(
        "store_agent",
        route_after_store,
        {
            "coordinator_agent": "coordinator_agent",
            END: END,
        },
    )
    
    # 4. Flujo del SyncAgent -> CoordinatorAgent o END
    workflow.add_conditional_edges(
        "sync_agent",
        route_after_sync,
        {
            "coordinator_agent": "coordinator_agent",
            END: END,
        },
    )

    # 5. Flujo Post-Transacción (CoordinatorAgent)
    workflow.add_conditional_edges(
        "coordinator_agent",
        route_after_coordinator,
        {
            "alert_agent": "alert_agent",
            "sync_agent": "sync_agent",
            END: END,
        },
    )
    
    # 6. Fin de las ramas hijas
    workflow.add_edge("alert_agent", END)

    return workflow


# --- Compilar el grafo (variable global lista para uso) ---
memory_saver = MemorySaver()
mas_app = _build_graph().compile(checkpointer=memory_saver)

logger.info("✅ Grafo Multiagente LangGraph compilado exitosamente")
