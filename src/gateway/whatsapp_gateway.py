"""
Gateway de WhatsApp usando Meta Cloud API
Maneja la comunicación bidireccional con WhatsApp Business
Soporta mensajes de texto, botones interactivos y listas
"""
import requests
from typing import Dict, Any, Optional, List
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
    
    # ============= Envío de Mensajes =============
    
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
        
        return self._send_request(url, payload, f"Mensaje de texto a {to}")
    
    def send_interactive_buttons(
        self,
        to: str,
        body_text: str,
        buttons: List[Dict[str, str]],
        header: Optional[str] = None,
        footer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envía un mensaje con botones de respuesta rápida (máximo 3)
        
        Args:
            to: Número de teléfono
            body_text: Texto principal del mensaje
            buttons: Lista de botones [{"id": "btn_1", "title": "Opción 1"}, ...]
            header: Texto del encabezado (opcional)
            footer: Texto del pie (opcional)
        
        Returns:
            Respuesta de la API
        """
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        
        interactive = {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {"id": btn["id"], "title": btn["title"]}
                    }
                    for btn in buttons[:3]  # Máximo 3 botones
                ]
            }
        }
        
        if header:
            interactive["header"] = {"type": "text", "text": header}
        if footer:
            interactive["footer"] = {"text": footer}
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive
        }
        
        return self._send_request(url, payload, f"Botones interactivos a {to}")
    
    def send_interactive_list(
        self,
        to: str,
        body_text: str,
        button_label: str,
        sections: List[Dict[str, Any]],
        header: Optional[str] = None,
        footer: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envía un mensaje con lista desplegable de opciones
        
        Args:
            to: Número de teléfono
            body_text: Texto principal del mensaje
            button_label: Texto del botón que abre la lista
            sections: Secciones con opciones
                [{"title": "Sección", "rows": [{"id": "opt_1", "title": "Opción", "description": "..."}]}]
            header: Texto del encabezado (opcional)
            footer: Texto del pie (opcional)
        
        Returns:
            Respuesta de la API
        """
        url = f"{self.api_url}/{self.phone_number_id}/messages"
        
        interactive = {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_label,
                "sections": sections
            }
        }
        
        if header:
            interactive["header"] = {"type": "text", "text": header}
        if footer:
            interactive["footer"] = {"text": footer}
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive
        }
        
        return self._send_request(url, payload, f"Lista interactiva a {to}")
    
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
        
        return self._send_request(url, payload, f"Template '{template_name}' a {to}")
    
    # ============= Utilidades =============
    
    def _send_request(self, url: str, payload: Dict, description: str) -> Dict[str, Any]:
        """Método interno para enviar peticiones a la API de WhatsApp"""
        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"✅ {description}")
            
            return {
                "success": True,
                "message_id": result.get("messages", [{}])[0].get("id"),
                "timestamp": datetime.utcnow().isoformat()
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error en {description}: {e}")
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
    
    # ============= Parsing de Webhooks =============
    
    def parse_webhook_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parsea un mensaje recibido del webhook de WhatsApp
        Soporta mensajes de texto, respuestas de botón y selección de lista
        
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
            
            # Parsear mensaje base
            parsed = {
                "message_id": message.get("id"),
                "from": message.get("from"),
                "contact_name": contact_name,
                "timestamp": message.get("timestamp"),
                "type": message.get("type"),
            }
            
            # Extraer contenido según el tipo
            msg_type = message.get("type")
            
            if msg_type == "text":
                parsed["text"] = message.get("text", {}).get("body", "")
            
            elif msg_type == "interactive":
                interactive = message.get("interactive", {})
                interactive_type = interactive.get("type")
                
                if interactive_type == "button_reply":
                    button_reply = interactive.get("button_reply", {})
                    parsed["interactive_type"] = "button_reply"
                    parsed["interactive_id"] = button_reply.get("id", "")
                    parsed["interactive_title"] = button_reply.get("title", "")
                
                elif interactive_type == "list_reply":
                    list_reply = interactive.get("list_reply", {})
                    parsed["interactive_type"] = "list_reply"
                    parsed["interactive_id"] = list_reply.get("id", "")
                    parsed["interactive_title"] = list_reply.get("title", "")
            
            elif msg_type == "image":
                parsed["image"] = message.get("image", {})
            
            elif msg_type == "document":
                parsed["document"] = message.get("document", {})
            
            logger.info(
                f"📩 Mensaje recibido de {parsed['from']} "
                f"(tipo: {msg_type}): "
                f"{parsed.get('text') or parsed.get('interactive_title', '[media]')}"
            )
            
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
