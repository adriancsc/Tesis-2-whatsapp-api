"""
Enrutador de mensajes entre Gateway y Agentes
Coordina la comunicación entre WhatsApp y los agentes del sistema
"""
from typing import Dict, Any
from datetime import datetime

from src.gateway.whatsapp_gateway import whatsapp_gateway
from src.agents import store_agent, coordinator_agent
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class MessageRouter:
    """Enrutador de mensajes del sistema MAS-CIS"""
    
    def __init__(self):
        self.whatsapp = whatsapp_gateway
        self.store_agent = store_agent
        self.coordinator = coordinator_agent
    
    async def route_whatsapp_message(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enruta un mensaje de WhatsApp al agente correspondiente
        
        Args:
            webhook_data: Datos del webhook de WhatsApp
        
        Returns:
            Resultado del procesamiento
        """
        # Parsear mensaje
        parsed_message = self.whatsapp.parse_webhook_message(webhook_data)
        
        if not parsed_message:
            logger.warning("Mensaje de webhook no válido o no soportado")
            return {"success": False, "error": "Invalid webhook data"}
        
        # Marcar como leído
        if parsed_message.get("message_id"):
            self.whatsapp.mark_as_read(parsed_message["message_id"])
        
        # Procesar mensajes soportados (texto e interactivos)
        msg_type = parsed_message.get("type")
        if msg_type not in ["text", "interactive"]:
            logger.info(f"Tipo de mensaje no procesado por el store_agent: {msg_type}")
            return {"success": False, "error": "Unsupported message type"}
        
        logger.info(f"📨 Enrutando mensaje al Store Agent")
        
        try:
            # Procesar con Store Agent
            response = await self.store_agent.process_message(parsed_message)
            
            # Si el Store Agent necesita al Coordinador
            if response.get("requires_coordinator"):
                logger.info("🔄 Enrutando al Coordinator Agent")
                coordinator_response = await self.coordinator.process_message(
                    response.get("coordinator_request", {})
                )
                
                # Actualizar respuesta con resultado del coordinador
                response["response_type"] = "text"
                if coordinator_response.get("success"):
                    response["text"] = self._format_success_message(coordinator_response)
                else:
                    response["text"] = f"❌ Error: {coordinator_response.get('error', 'Ocurrió un error al procesar el stock.')}"
            
            # Enviar respuesta por WhatsApp según su tipo
            to = response.get("to")
            resp_type = response.get("response_type", "text")
            
            if resp_type == "text" and response.get("text"):
                send_result = self.whatsapp.send_message(
                    to=to,
                    message=response.get("text")
                )
            
            elif resp_type == "interactive_buttons" and response.get("buttons"):
                send_result = self.whatsapp.send_interactive_buttons(
                    to=to,
                    body_text=response.get("body", "Elige una opción:"),
                    buttons=response.get("buttons")
                )
            
            elif resp_type == "interactive_list" and response.get("sections"):
                send_result = self.whatsapp.send_interactive_list(
                    to=to,
                    body_text=response.get("body", "Abre la lista:"),
                    button_label=response.get("button_label", "Opciones"),
                    sections=response.get("sections")
                )
            else:
                return {"success": True, "message_sent": False, "reason": "No valid response to send"}
                
            return {
                "success": send_result.get("success"),
                "message_sent": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error enrutando mensaje: {e}", exc_info=True)
            
            # Enviar mensaje de error al usuario
            self.whatsapp.send_message(
                to=parsed_message.get("from"),
                message="❌ Ocurrió un error al procesar tu petición. Por favor, intenta nuevamente escribiendo 'menu'."
            )
            
            return {"success": False, "error": str(e)}
    
    async def send_inventory_update(
        self,
        product_sku: str,
        action: str,
        quantity: int,
        vendor_phone: str
    ) -> Dict[str, Any]:
        """
        Envía una actualización de inventario directamente al Coordinador
        """
        request = {
            "action": action,
            "product_sku": product_sku,
            "quantity": quantity,
            "vendor_phone": vendor_phone,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self.coordinator.process_message(request)
        
        # Notificar al vendedor
        if vendor_phone and result.get("success"):
            message = self._format_success_message(result)
            self.whatsapp.send_message(to=vendor_phone, message=message)
        
        return result
    
    def _format_success_message(self, coordinator_response: Dict[str, Any]) -> str:
        """Formatea un mensaje de éxito del coordinador"""
        
        if not coordinator_response.get("success"):
            return f"❌ Error: {coordinator_response.get('error')}"
        
        product = coordinator_response.get("product", {})
        
        return (
            f"✅ Operación completada con éxito\n\n"
            f"📦 {product.get('name')} ({product.get('sku')})\n"
            f"📊 Stock anterior: {product.get('previous_stock')}\n"
            f"📊 Stock nuevo: {product.get('new_stock')}\n"
            f"📊 Stock total: {product.get('stock_total')}\n\n"
            f"✨ El sistema web ha sido actualizado."
        )


# Instancia global del router
message_router = MessageRouter()
