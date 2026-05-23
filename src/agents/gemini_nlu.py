"""
NLU Processor con Gemini AI
Procesa lenguaje natural para comandos de inventario
"""
import json
import re
from typing import Dict, Any, Optional
from dataclasses import dataclass
import google.generativeai as genai

from src.config import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Configurar Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)


@dataclass
class ParsedCommand:
    """Comando parseado del usuario"""
    action: str  # sell, add, update, remove, query
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    quantity: Optional[int] = None
    size: Optional[str] = None
    color: Optional[str] = None
    price: Optional[float] = None
    confidence: float = 0.0
    raw_text: str = ""


class GeminiNLUProcessor:
    """Procesador de lenguaje natural usando Gemini"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.logger = logger
        
        # Prompt del sistema
        self.system_prompt = """
Eres un asistente de inventario para una tienda de ropa. Tu trabajo es extraer información de mensajes de vendedores.

ACCIONES VÁLIDAS:
- "sell" (vender): cuando dicen "vendí", "salieron", "se fueron", "despachamos"
- "add" (agregar): cuando dicen "llegaron", "agregué", "recibimos", "entraron"
- "update" (actualizar): cuando dicen "actualizar", "cambiar", "modificar"
- "query" (consultar): cuando preguntan "cuánto", "stock", "hay", "quedan"
- "remove" (eliminar): cuando dicen "eliminar", "quitar", "borrar"

PRODUCTOS DISPONIBLES (SKU base - las tallas son variantes):
- Polo Blanco (SKU: POLO-BLANCO) - Tallas: S, M, L, XL, 2XL
- Polo Negro (SKU: POLO-NEGRO) - Tallas: S, M, L, XL, 2XL
- Polo Azul (SKU: POLO-AZUL) - Tallas: S, M, L, XL, 2XL
- Jean Azul (SKU: JEAN-AZUL) - Tallas: 28, 30, 32, 34, 36
- Pantalón Negro (SKU: PANTALON-NEGRO) - Tallas: 28, 30, 32, 34, 36
- Pantalón Beige (SKU: PANTALON-BEIGE) - Tallas: 28, 30, 32, 34
- Camisa Blanca (SKU: CAMISA-BLANCA) - Tallas: S, M, L, XL, 2XL
- Camisa Celeste (SKU: CAMISA-CELESTE) - Tallas: S, M, L, XL
- Gorra Negra (SKU: GORRA-NEGRA) - Talla única
- Correa Marrón (SKU: CORREA-MARRON) - Talla: 95

IMPORTANTE: 
- Usa SOLO el SKU base (sin la talla)
- La talla va en el campo "size" separado
- Reconoce variaciones como "polo rojo" → "POLO-NEGRO", "jeans" → "JEAN-AZUL", etc.

RESPONDE SOLO CON JSON en este formato exacto:
{
  "action": "sell|add|update|query|remove",
  "product_name": "nombre del producto",
  "product_sku": "SKU-BASE",
  "quantity": número,
  "size": "talla si aplica",
  "color": "color si aplica",
  "confidence": 0.0-1.0
}

EJEMPLOS:
Mensaje: "Vendí 3 polos rojos talla M"
Respuesta: {"action": "sell", "product_name": "Polo Negro", "product_sku": "POLO-NEGRO", "quantity": 3, "size": "M", "color": "negro", "confidence": 0.95}

Mensaje: "Cuánto stock hay de POLO-R-M"
Respuesta: {"action": "query", "product_name": "Polo Negro", "product_sku": "POLO-NEGRO", "quantity": null, "size": "M", "color": "negro", "confidence": 0.9}

Mensaje: "Llegaron 10 camisas celestes L"
Respuesta: {"action": "add", "product_name": "Camisa Celeste", "product_sku": "CAMISA-CELESTE", "quantity": 10, "size": "L", "color": "celeste", "confidence": 0.92}

Mensaje: "Vendi 3 polos rojos talla M"
Respuesta: {"action": "sell", "product_name": "Polo Negro", "product_sku": "POLO-NEGRO", "quantity": 3, "size": "M", "color": "negro", "confidence": 0.95}

Si no entiendes el mensaje, devuelve: {"action": "unknown", "confidence": 0.0}
"""
    
    def parse(self, text: str) -> ParsedCommand:
        """
        Parsea un mensaje de texto usando Gemini
        
        Args:
            text: Mensaje del usuario
            
        Returns:
            ParsedCommand con la información extraída
        """
        try:
            # Generar respuesta con Gemini
            prompt = f"{self.system_prompt}\n\nMensaje del usuario: \"{text}\"\n\nRespuesta JSON:"
            
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                self.logger.warning(f"No se encontró JSON en respuesta de Gemini: {response_text}")
                return self._fallback_parse(text)
            
            # Parsear JSON
            data = json.loads(json_match.group())
            
            return ParsedCommand(
                action=data.get("action", "unknown"),
                product_name=data.get("product_name"),
                product_sku=data.get("product_sku"),
                quantity=data.get("quantity"),
                size=data.get("size"),
                color=data.get("color"),
                confidence=data.get("confidence", 0.0),
                raw_text=text
            )
            
        except Exception as e:
            self.logger.error(f"Error en Gemini NLU: {e}", exc_info=True)
            return self._fallback_parse(text)
    
    def _fallback_parse(self, text: str) -> ParsedCommand:
        """Fallback usando regex simple si Gemini falla"""
        text_lower = text.lower()
        
        # Detectar acción
        action = "unknown"
        
        def matches(keywords, text):
            pattern = r'\b(' + '|'.join(map(re.escape, keywords)) + r')\b'
            return re.search(pattern, text, re.IGNORECASE) is not None

        # Detectar saludos PRIMERO
        if matches(["hola", "buenos días", "buenos dias", "buenas tardes", "buenas noches", 
                    "hey", "qué tal", "que tal", "saludos", "hi", "hello"], text):
            action = "greeting"
        # Detectar solicitud de inventario completo
        elif matches(["ver inventario", "mostrar inventario", "todo el inventario", 
                      "lista de productos", "qué productos", "que productos",
                      "todos los productos", "listar todo", "ver todo", "inventario completo"], text):
            action = "inventory"
        elif matches(["vendí", "vendi", "salieron", "despachamos", "venta", "vendido"], text):
            action = "sell"
        elif matches(["llegaron", "agregué", "agrege", "recibimos", "ingreso", "compra", "agregado", "agregar", "añadir", "agrega"], text):
            action = "add"
        elif matches(["cuánto", "cuanto", "stock", "hay", "quedan", "precio"], text):
            action = "query"
        elif matches(["actualizar", "cambiar", "modificar"], text):
            action = "update"
        
        # Extraer cantidad
        quantity_match = re.search(r'\b(\d+)\b', text)
        quantity = int(quantity_match.group(1)) if quantity_match else 1 if action in ["sell", "add"] else None
        
        # Extraer atributos (Emergency NLU)
        product_name = None
        color = None
        size = None
        product_sku = None
        
        # Mapa de productos conocidos para demo (Singular y Plural)
        products_map = {
            "polo blanco": "Polo Blanco", "polos blancos": "Polo Blanco",
            "polo negro": "Polo Negro", "polos negros": "Polo Negro",
            "polo azul": "Polo Azul", "polos azules": "Polo Azul",
            "camisa blanca": "Camisa Blanca", "camisas blancas": "Camisa Blanca",
            "camisa celeste": "Camisa Celeste", "camisas celestes": "Camisa Celeste",
            "pantalon negro": "Pantalón Negro", "pantalones negros": "Pantalón Negro",
            "pantalón negro": "Pantalón Negro",
            "pantalon beige": "Pantalón Beige", "pantalones beige": "Pantalón Beige",
            "pantalón beige": "Pantalón Beige",
            "jean azul": "Jean Azul", "jeans azules": "Jean Azul", "jeans": "Jean Azul", "jean": "Jean Azul",
            "correa marron": "Correa Marrón", "correas marrones": "Correa Marrón",
            "correa marrón": "Correa Marrón"
        }
        
        for key, val in products_map.items():
            if key in text_lower:
                product_name = val
                if "blanco" in key: color = "Blanco"
                elif "negro" in key: color = "Negro"
                elif "azul" in key: color = "Azul"
                elif "celeste" in key: color = "Celeste"
                elif "beige" in key: color = "Beige"
                elif "marron" in key or "marrón" in key: color = "Marrón"
                break
                
        # Extraer talla (Corrección de regex)
        size_match = re.search(r'\b(?:talla|talle)?\s*(xs|s|m|l|xl|2xl|28|30|32|34)\b', text_lower)
        if size_match:
            candidate = size_match.group(1).upper()
            size = candidate
        
        return ParsedCommand(
            action=action,
            product_name=product_name,
            product_sku=product_sku,
            quantity=quantity,
            size=size,
            color=color,
            confidence=0.85 if action != "unknown" else 0.0,
            raw_text=text
        )
    
    def is_valid_command(self, parsed: ParsedCommand, threshold: float = 0.7) -> bool:
        """Verifica si un comando es válido según el umbral de confianza"""
        return parsed.confidence >= threshold and parsed.action != "unknown"


# Instancia global
gemini_nlu = GeminiNLUProcessor()
