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
            logger.warning("Mensaje de webhook no válido")
            return {"success": False, "error": "Invalid webhook data"}
        
        # Marcar como leído
        if parsed_message.get("message_id"):
            self.whatsapp.mark_as_read(parsed_message["message_id"])
        
        # Solo procesar mensajes de texto por ahora
        if parsed_message.get("type") != "text":
            logger.info(f"Tipo de mensaje no soportado: {parsed_message.get('type')}")
            return {"success": False, "error": "Unsupported message type"}
        
        # Enviar al Agente de Tienda
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
                if coordinator_response.get("success"):
                    response["text"] = self._format_success_message(coordinator_response)
                else:
                    response["text"] = f"❌ Error: {coordinator_response.get('error')}"
            
            # Enviar respuesta por WhatsApp
            if response.get("text"):
                send_result = self.whatsapp.send_message(
                    to=response.get("to"),
                    message=response.get("text")
                )
                
                return {
                    "success": send_result.get("success"),
                    "message_sent": True,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            return {"success": True, "message_sent": False}
        
        except Exception as e:
            logger.error(f"Error enrutando mensaje: {e}", exc_info=True)
            
            # Enviar mensaje de error al usuario
            self.whatsapp.send_message(
                to=parsed_message.get("from"),
                message="❌ Ocurrió un error al procesar tu mensaje. Por favor, intenta nuevamente."
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
        
        Args:
            product_sku: SKU del producto
            action: Acción a realizar
            quantity: Cantidad
            vendor_phone: Teléfono del vendedor
        
        Returns:
            Resultado de la operación
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
            f"✅ Operación completada\n\n"
            f"📦 {product.get('name')} ({product.get('sku')})\n"
            f"📊 Stock anterior: {product.get('previous_stock')}\n"
            f"📊 Stock nuevo: {product.get('new_stock')}\n"
            f"📊 Stock total: {product.get('stock_total')}"
        )


# Instancia global del router
message_router = MessageRouter()
