"""
Gateway de WhatsApp usando Meta Cloud API
Maneja la comunicación bidireccional con WhatsApp Business
"""
import requests
from typing import Dict, Any, Optional
from datetime import datetime

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class WhatsAppGateway:
    """Gateway para WhatsApp Business Cloud API"""
    
    def __init__(self):
        self.api_url = settings.whatsapp_graph_api_url
        self.phone_number_id = settings.WHATSAPP_PHONE_NUMBER_ID
        self.access_token = settings.WHATSAPP_API_TOKEN
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """
        Envía un mensaje de texto a un número de WhatsApp
        
        Args:
            to: Número de teléfono (formato: 51999999999)
            message: Texto del mensaje
        
        Returns:
            Respuesta de la API
        """
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message
            }
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Mensaje enviado a {to}")
            
            return {
                "success": True,
                "message_id": result.get("messages", [{}])[0].get("id"),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error enviando mensaje: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "es"
    ) -> Dict[str, Any]:
        """
        Envía un mensaje de plantilla (template)
        
        Args:
            to: Número de teléfono
            template_name: Nombre de la plantilla aprobada
            language_code: Código de idioma
        
        Returns:
            Respuesta de la API
        """
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ Template enviado a {to}: {template_name}")
            
            return {
                "success": True,
                "message_id": result.get("messages", [{}])[0].get("id"),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error enviando template: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def mark_as_read(self, message_id: str) -> bool:
        """
        Marca un mensaje como leído
        
        Args:
            message_id: ID del mensaje
        
        Returns:
            True si fue exitoso
        """
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id
        }
        
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.debug(f"Mensaje marcado como leído: {message_id}")
            return True
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error marcando mensaje como leído: {e}")
            return False
    
    def parse_webhook_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parsea un mensaje recibido del webhook de WhatsApp
        
        Args:
            webhook_data: Datos del webhook
        
        Returns:
            Mensaje parseado o None
        """
        try:
            # Estructura de webhook de WhatsApp Cloud API
            entry = webhook_data.get("entry", [])[0]
            changes = entry.get("changes", [])[0]
            value = changes.get("value", {})
            
            # Verificar si hay mensajes
            messages = value.get("messages", [])
            if not messages:
                return None
            
            message = messages[0]
            
            # Extraer información del contacto
            contacts = value.get("contacts", [])
            contact_name = contacts[0].get("profile", {}).get("name", "") if contacts else ""
            
            # Parsear mensaje
            parsed = {
                "message_id": message.get("id"),
                "from": message.get("from"),
                "contact_name": contact_name,
                "timestamp": message.get("timestamp"),
                "type": message.get("type"),
            }
            
            # Extraer contenido según el tipo
            if message.get("type") == "text":
                parsed["text"] = message.get("text", {}).get("body", "")
            elif message.get("type") == "image":
                parsed["image"] = message.get("image", {})
            elif message.get("type") == "document":
                parsed["document"] = message.get("document", {})
            
            logger.info(f"📩 Mensaje recibido de {parsed['from']}: {parsed.get('text', '[media]')}")
            
            return parsed
        
        except (KeyError, IndexError) as e:
            logger.error(f"Error parseando webhook: {e}")
            return None
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verifica el webhook de WhatsApp
        
        Args:
            mode: Modo de verificación
            token: Token de verificación
            challenge: Challenge de WhatsApp
        
        Returns:
            Challenge si la verificación es exitosa
        """
        if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
            logger.info("✅ Webhook verificado exitosamente")
            return challenge
        else:
            logger.warning("❌ Verificación de webhook fallida")
            return None


# Instancia global del gateway
whatsapp_gateway = WhatsAppGateway()
