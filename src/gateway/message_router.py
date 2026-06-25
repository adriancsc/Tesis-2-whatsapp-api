"""
Enrutador de mensajes entre Gateway y LangGraph
Coordina la comunicación entre WhatsApp y el grafo de inventario
"""
from typing import Dict, Any
from datetime import datetime
from langchain_core.runnables import RunnableConfig

from src.gateway.whatsapp_gateway import whatsapp_gateway
from src.agents import mas_app, conversation_manager
from src.agents.state import MASState
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class MessageRouter:
    """Enrutador de mensajes del sistema MAS-CIS (LangGraph)"""
    
    def __init__(self):
        self.whatsapp = whatsapp_gateway
    
    async def route_whatsapp_message(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enruta un mensaje de WhatsApp al grafo de LangGraph
        """
        # Parsear mensaje
        parsed_message = self.whatsapp.parse_webhook_message(webhook_data)
        
        if not parsed_message:
            logger.warning("Mensaje de webhook no válido o no soportado")
            return {"success": False, "error": "Invalid webhook data"}
        
        # Marcar como leído
        if parsed_message.get("message_id"):
            self.whatsapp.mark_as_read(parsed_message["message_id"])
        
        # Obtener input y emisor
        vendor_phone = parsed_message.get("from")
        msg_type = parsed_message.get("type")
        
        # En el nuevo modelo numérico, solo aceptamos "text" o el body de list_reply
        raw_text = ""
        if msg_type == "text":
            raw_text = parsed_message.get("text", "")
        elif msg_type == "interactive":
            interactive_type = parsed_message.get("interactive_type")
            if interactive_type in ["list_reply", "button_reply"]:
                # Por si alguien toca un botón antiguo, tomamos el id como texto
                raw_text = parsed_message.get("interactive_id", "")
        else:
            logger.info(f"Tipo de mensaje no procesado: {msg_type}")
            return {"success": False, "error": "Unsupported message type"}
            
        logger.info(f"📨 Enrutando mensaje de {vendor_phone} al Grafo LangGraph")
        
        try:
            # 1. Recuperar contexto de memoria
            context = conversation_manager.get_context(vendor_phone)
            
            # 2. Construir el estado inicial para LangGraph
            initial_state: MASState = {
                "source": "whatsapp",
                "vendor_phone": vendor_phone,
                "raw_text": raw_text,
                "current_step": context.current_step,
                "action": context.action,
                "product_sku": context.product_sku,
                "product_name": context.product_name,
                "variant_id": context.variant_id,
                "variant_sku": context.variant_sku,
                "size": context.size,
                "quantity": context.quantity,
                "response_text": "",
                "requires_coordinator": False,
                "requires_sync": False,
                "requires_alert": False,
                "conflict_detected": False,
                "operation_success": False,
                "size_options": context.size_options,
                "messages": [],
                "ecommerce_order_id": None,
                "ecommerce_action": None,
            }
            
            # 3. Invocar el grafo (asíncrono, no bloquea el event loop de FastAPI)
            config: RunnableConfig = {"configurable": {"thread_id": vendor_phone}}
            final_state = await mas_app.ainvoke(initial_state, config)
            
            # 4. Actualizar el contexto en memoria
            context.update_from_state(final_state)
            
            # 5. Enviar la respuesta por WhatsApp
            response_text = final_state.get("response_text", "")
            if response_text:
                send_result = self.whatsapp.send_message(
                    to=vendor_phone,
                    message=response_text
                )
            else:
                send_result = {"success": True}
                
            return {
                "success": send_result.get("success", False),
                "message_sent": bool(response_text),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error enrutando mensaje al grafo: {e}", exc_info=True)
            
            # Resetear contexto en caso de error grave
            conversation_manager.reset_context(vendor_phone)
            
            # Enviar mensaje de error
            self.whatsapp.send_message(
                to=vendor_phone,
                message="❌ Ocurrió un error interno al procesar tu petición. La conversación ha sido reiniciada. Escribe 'menu' para empezar."
            )
            
            return {"success": False, "error": str(e)}


# Instancia global del router
message_router = MessageRouter()
