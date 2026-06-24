"""
Nodo del Agente de Alertas (Alert Agent) — LangGraph
======================================================
Agente autónomo responsable del monitoreo proactivo del inventario
y la emisión de alertas sin intervención del usuario.

Propiedades MAS (Wooldridge & Jennings, 1995):
    - Proactividad: Actúa SIN que el usuario lo solicite. Evalúa
                    condiciones post-transacción y emite alertas.
    - Autonomía:    Decide autónomamente si una situación amerita
                    una alerta basándose en umbrales y patrones.
    - Reactividad:  Percibe los cambios post-transacción del
                    CoordinatorAgent y reacciona en consecuencia.
    - Habilidad Social: Recibe mensajes inform del CoordinatorAgent
                    y crea mensajes alert para el StoreAgent.

Casos de Uso implementados:
    - CU-09: Alerta Proactiva de Stock Bajo (nuevo)
    - CU-10: Detección Autónoma de Anomalías en Mermas (nuevo)
"""
from typing import Dict, Any

from src.agents.state import MASState, create_message
from src.database.connection import get_db
from src.database.models import AgentLog, AgentType
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Nombre del agente (para mensajes inter-agente)
AGENT_NAME = "alert_agent"

# Umbrales configurables (podrían venir de settings en producción)
LOW_STOCK_THRESHOLD = 2     # Unidades para considerar stock bajo
CRITICAL_STOCK_THRESHOLD = 0  # Stock agotado


# =============================================================================
# Nodo Principal: alert_agent_node
# =============================================================================

def alert_agent_node(state: MASState) -> Dict[str, Any]:
    """
    Nodo del Agente de Alertas en el grafo LangGraph.

    Este agente se ejecuta DESPUÉS del CoordinatorAgent cuando
    éste activa la señal `requires_alert`. Evalúa las condiciones
    post-transacción y enriquece el response_text con alertas
    proactivas que se enviarán al vendedor por WhatsApp.

    Proactividad (Wooldridge): El agente toma la iniciativa de
    informar al vendedor sobre situaciones de riesgo sin que
    éste lo haya solicitado.

    Args:
        state: Estado actual del grafo MAS (MASState)

    Returns:
        Dict con actualizaciones parciales del estado, incluyendo
        texto de alerta anexado al response_text y mensajes alert.
    """
    logger.info("🚨 AlertAgent | Evaluando condiciones post-transacción")

    # --- Buscar el mensaje inform del CoordinatorAgent ---
    coordinator_inform = _find_coordinator_inform(state.get("messages", []))

    if not coordinator_inform:
        logger.info("🚨 AlertAgent | Sin datos del coordinador. No-op.")
        return {"requires_alert": False}

    content = coordinator_inform.get("content", {})
    alert_data = content.get("alert_data")
    action = content.get("action", "")

    if not alert_data:
        logger.info("🚨 AlertAgent | Sin datos de alerta. No-op.")
        return {"requires_alert": False}

    # --- Evaluar alertas ---
    alert_texts = []
    alert_messages = []

    # CU-09: Alerta de Stock Agotado
    if alert_data.get("type") == "stock_depleted":
        alert_text = (
            "\n🚨 *ALERTA CRÍTICA (Agente de Alertas):*\n"
            f"La variante *{alert_data.get('product_name', '')} "
            f"talla {alert_data.get('size', '')}* se ha agotado "
            f"completamente.\n"
            f"Registra un *Ingreso* (opción 2) lo antes posible.\n"
        )
        alert_texts.append(alert_text)
        alert_messages.append(
            create_message(
                performative="alert",
                sender=AGENT_NAME,
                receiver="store_agent",
                content={
                    "alert_type": "stock_depleted",
                    "variant_sku": alert_data.get("variant_sku"),
                    "product_name": alert_data.get("product_name"),
                    "size": alert_data.get("size"),
                    "severity": "critical",
                },
            )
        )
        logger.warning(
            f"🚨 AlertAgent ALERTA CRÍTICA: Stock agotado "
            f"{alert_data.get('variant_sku')}"
        )

    # CU-09: Alerta de Stock Bajo
    elif alert_data.get("type") == "low_stock":
        remaining = alert_data.get("remaining", 0)
        alert_text = (
            f"\n⚠️ *ALERTA (Agente de Alertas):*\n"
            f"Stock bajo en *{alert_data.get('product_name', '')} "
            f"talla {alert_data.get('size', '')}*.\n"
            f"Solo queda(n) {remaining} unidad(es).\n"
            f"Considera registrar un *Ingreso* pronto.\n"
        )
        alert_texts.append(alert_text)
        alert_messages.append(
            create_message(
                performative="alert",
                sender=AGENT_NAME,
                receiver="store_agent",
                content={
                    "alert_type": "low_stock",
                    "variant_sku": alert_data.get("variant_sku"),
                    "product_name": alert_data.get("product_name"),
                    "size": alert_data.get("size"),
                    "remaining": remaining,
                    "severity": "warning",
                },
            )
        )
        logger.warning(
            f"🚨 AlertAgent ALERTA: Stock bajo "
            f"{alert_data.get('variant_sku')} → {remaining} unidades"
        )

    # CU-10: Detección de Anomalías en Mermas
    merma_anomaly = alert_data.get("merma_anomaly")
    if merma_anomaly:
        alert_text = (
            f"\n⚠️ *ANOMALÍA DETECTADA (Agente de Alertas):*\n"
            f"{merma_anomaly.get('message', 'Patrón de mermas inusual detectado.')}\n"
            f"Revisa si hay un problema con la calidad del lote.\n"
        )
        alert_texts.append(alert_text)
        alert_messages.append(
            create_message(
                performative="alert",
                sender=AGENT_NAME,
                receiver="store_agent",
                content={
                    "alert_type": "merma_anomaly",
                    "removed_today": merma_anomaly.get("removed_today"),
                    "severity": "warning",
                },
            )
        )
        logger.warning(
            f"🚨 AlertAgent ANOMALÍA: Mermas diarias = "
            f"{merma_anomaly.get('removed_today')}"
        )

    # --- Enriquecer el response_text con las alertas ---
    current_response = state.get("response_text", "")
    full_response = current_response + "".join(alert_texts)

    # --- Registrar las alertas en el log de agentes ---
    _log_alerts(alert_texts, alert_data)

    logger.info(
        f"🚨 AlertAgent | {len(alert_texts)} alerta(s) generada(s)"
    )

    return {
        "response_text": full_response,
        "requires_alert": False,  # Ya procesada
        "messages": alert_messages,
    }


# =============================================================================
# Funciones Auxiliares
# =============================================================================

from typing import Optional

def _find_coordinator_inform(messages: list) -> Optional[dict]:
    """Encuentra el último mensaje inform del CoordinatorAgent"""
    for msg in reversed(messages):
        if (
            isinstance(msg, dict)
            and msg.get("performative") == "inform"
            and msg.get("sender") == "coordinator_agent"
        ):
            return msg
    return None


def _log_alerts(alert_texts: list, alert_data: dict):
    """Registra las alertas emitidas en la tabla AgentLog"""
    try:
        with get_db() as db:
            for i, text in enumerate(alert_texts):
                log = AgentLog(
                    agent_type=AgentType.STORE,  # Logged as store since it's for the vendor
                    action="proactive_alert",
                    message=text.strip(),
                    log_metadata=str(alert_data),
                    status="warning",
                )
                db.add(log)
            db.commit()
    except Exception as e:
        logger.error(f"Error registrando alertas en log: {e}")
