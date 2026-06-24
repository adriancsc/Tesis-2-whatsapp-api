"""
Estado del Sistema Multiagente MAS-CIS — LangGraph
====================================================
Define la estructura de datos que viaja a través de todos
los nodos del StateGraph, incluyendo el protocolo de
comunicación inter-agente (FIPA ACL simplificado).

Referencia Académica:
    - Wooldridge & Jennings (1995): Propiedades de agentes autónomos
    - Maldonado et al. (2024): Componentes de un MAS (IEEE Access)

Protocolo de Mensajes Inter-Agente:
    Cada agente puede enviar mensajes estructurados a otros agentes
    usando performatives inspirados en FIPA ACL:
        - request:  Solicitud de acción (Store → Coordinator)
        - inform:   Notificación de resultado exitoso
        - refuse:   Rechazo de solicitud con razón
        - alert:    Alerta proactiva sin solicitud previa
        - confirm:  Confirmación de recepción
"""
from typing import TypedDict, Optional, Annotated
from operator import add
from datetime import datetime


# =============================================================================
# Protocolo de Comunicación Inter-Agente
# =============================================================================

class AgentMessage(TypedDict):
    """
    Mensaje inter-agente inspirado en FIPA ACL simplificado.

    Permite comunicación formal y trazable entre los agentes del MAS.
    Cada mensaje queda registrado en la cola acumulativa del estado,
    formando un historial completo de la conversación inter-agente.

    Attributes:
        performative: Tipo de acto comunicativo (request/inform/refuse/alert/confirm)
        sender:       Nombre del agente emisor
        receiver:     Nombre del agente destinatario
        content:      Payload estructurado del mensaje
        timestamp:    Marca temporal ISO 8601
    """
    performative: str
    sender: str
    receiver: str
    content: dict
    timestamp: str


def create_message(
    performative: str,
    sender: str,
    receiver: str,
    content: dict,
) -> AgentMessage:
    """
    Factoría para crear mensajes inter-agente con timestamp automático.

    Args:
        performative: "request" | "inform" | "refuse" | "alert" | "confirm"
        sender: Nombre del agente emisor
        receiver: Nombre del agente destinatario
        content: Diccionario con el payload del mensaje

    Returns:
        AgentMessage listo para agregar a la cola de mensajes del estado
    """
    return AgentMessage(
        performative=performative,
        sender=sender,
        receiver=receiver,
        content=content,
        timestamp=datetime.utcnow().isoformat(),
    )


# =============================================================================
# Estado del Sistema Multiagente (MASState)
# =============================================================================

class MASState(TypedDict):
    """
    Estado inmutable del grafo LangGraph del Sistema Multiagente MAS-CIS.

    Este estado fluye a través de todos los nodos del StateGraph y contiene:
    1. Contexto de origen de la interacción
    2. Estado de la Máquina de Estados Finitos (FSM) del StoreAgent
    3. Cola acumulativa de mensajes inter-agente
    4. Señales de enrutamiento condicional para el grafo
    5. Contexto de e-commerce para el SyncAgent

    El campo `messages` usa el reductor `operator.add` de LangGraph,
    lo que permite que cada nodo ACUMULE mensajes en la cola sin
    sobrescribir los anteriores. Esto genera un historial completo
    de la comunicación inter-agente en cada invocación del grafo.
    """

    # --- Contexto de Origen ---
    source: str                         # "whatsapp" | "ecommerce" | "api" | "system"
    vendor_phone: Optional[str]         # Número del vendedor (identifica la sesión)
    raw_text: str                       # Texto/input recibido del usuario o webhook

    # --- Estado FSM del StoreAgent ---
    current_step: str                   # MAIN_MENU | SELECT_PRODUCT | SELECT_SIZE |
                                        # ENTER_QUANTITY | CONFIRM
    action: Optional[str]               # "sell" | "add" | "remove" | "query" |
                                        # "daily_summary" | "sell_web"
    product_sku: Optional[str]          # SKU base del producto (ej: "POLO-BLANCO")
    product_name: Optional[str]         # Nombre para mostrar (ej: "Polo Blanco")
    variant_id: Optional[int]           # ID de la variante seleccionada en BD
    variant_sku: Optional[str]          # SKU de la variante (ej: "POLO-BLANCO-M")
    size: Optional[str]                 # Talla seleccionada (ej: "M", "L")
    quantity: Optional[int]             # Cantidad ingresada por el vendedor
    size_options: Optional[dict]        # Mapa temporal: "1" → {id, sku, size, stock}

    # --- Comunicación Inter-Agente (FIPA ACL simplificado) ---
    messages: Annotated[list, add]      # Cola acumulativa de AgentMessage
                                        # Cada nodo AGREGA mensajes; nunca sobrescribe

    # --- Señales de Enrutamiento del Grafo ---
    response_text: str                  # Texto de respuesta final para el usuario
    operation_success: bool             # Resultado de la transacción del coordinador
    requires_coordinator: bool          # Flag: Store/Sync → Coordinator
    requires_sync: bool                 # Flag: Coordinator → SyncAgent
    requires_alert: bool                # Flag: Coordinator → AlertAgent
    conflict_detected: bool             # Señal de conflicto de concurrencia (CU-05/06)

    # --- Contexto de E-Commerce (SyncAgent) ---
    ecommerce_order_id: Optional[str]   # ID de la orden web (CU-04)
    ecommerce_action: Optional[str]     # "process_order" | "cancel_order" | "sync_stock"
