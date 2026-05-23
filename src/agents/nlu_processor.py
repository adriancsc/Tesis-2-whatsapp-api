"""
Procesador de Lenguaje Natural (NLU) para comandos de inventario
Extrae intención, cantidad, producto y atributos de mensajes en lenguaje natural
"""
import re
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import spacy
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class ParsedCommand:
    """Resultado del parsing de un comando"""
    action: str  # sell, add, update, remove, query
    quantity: Optional[int] = None
    product_name: Optional[str] = None
    product_sku: Optional[str] = None
    attributes: Dict[str, str] = None
    confidence: float = 0.0
    raw_text: str = ""
    
    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


class NLUProcessor:
    """Procesador de lenguaje natural para comandos de inventario"""
    
    # Patrones de acción
    ACTION_PATTERNS = {
        "sell": [
            r"vend[ií]",
            r"se vendi[oó]",
            r"comprar[oó]n",
            r"salida",
            r"egreso"
        ],
        "add": [
            r"agreg[aué]",
            r"a[ñn]ad[ií]",
            r"ingres[oé]",
            r"lleg[oó]",
            r"recib[ií]",
            r"entrada"
        ],
        "update": [
            r"actualiz[aá]",
            r"modific[aá]",
            r"cambi[aá]",
            r"establec[eé]",
            r"poner?\s+(?:el\s+)?stock"
        ],
        "remove": [
            r"elimin[aá]",
            r"quit[aá]",
            r"borr[aá]",
            r"descart[aá]",
            r"da[ñn]ad[oa]s?"
        ],
        "query": [
            r"cu[aá]nto[s]?",
            r"qu[eé]\s+(?:hay|tengo|queda)",
            r"consulta",
            r"ver\s+(?:el\s+)?stock",
            r"inventario",
            r"resumen"
        ]
    }
    
    # Patrones de cantidad
    QUANTITY_PATTERNS = [
        r"(\d+)\s+(?:unidades?|piezas?|items?)?",
        r"(?:cantidad|cant\.?)\s*[:=]?\s*(\d+)",
    ]
    
    # Patrones de SKU
    SKU_PATTERNS = [
        r"\b([A-Z]{3,}-[A-Z0-9]{1,}-[A-Z0-9]{1,})\b",  # POLO-R-M
        r"\bSKU\s*[:=]?\s*([A-Z0-9-]+)\b",
    ]
    
    # Atributos comunes
    COLORS = [
        "rojo", "azul", "verde", "amarillo", "negro", "blanco", "gris",
        "rosa", "morado", "naranja", "café", "beige", "celeste"
    ]
    
    SIZES = [
        "xs", "s", "m", "l", "xl", "xxl", "xxxl",
        "28", "30", "32", "34", "36", "38", "40", "42"
    ]
    
    def __init__(self, use_spacy: bool = True):
        """
        Inicializa el procesador NLU
        
        Args:
            use_spacy: Si True, intenta cargar spaCy para análisis avanzado
        """
        self.nlp = None
        if use_spacy:
            try:
                self.nlp = spacy.load("es_core_news_sm")
                logger.info("✅ Modelo spaCy cargado exitosamente")
            except OSError:
                logger.warning(
                    "⚠️  Modelo spaCy no encontrado. "
                    "Ejecuta: python -m spacy download es_core_news_sm"
                )
                logger.info("Usando solo patrones regex")
    
    def parse(self, text: str) -> ParsedCommand:
        """
        Parsea un mensaje en lenguaje natural
        
        Args:
            text: Texto del mensaje
        
        Returns:
            ParsedCommand con la información extraída
        """
        text_lower = text.lower().strip()
        
        # Extraer acción
        action = self._extract_action(text_lower)
        
        # Extraer cantidad
        quantity = self._extract_quantity(text_lower)
        
        # Extraer SKU
        sku = self._extract_sku(text)
        
        # Extraer nombre de producto
        product_name = self._extract_product_name(text_lower, sku)
        
        # Extraer atributos (color, talla)
        attributes = self._extract_attributes(text_lower)
        
        # Calcular confianza
        confidence = self._calculate_confidence(
            action, quantity, product_name, sku, attributes
        )
        
        return ParsedCommand(
            action=action,
            quantity=quantity,
            product_name=product_name,
            product_sku=sku,
            attributes=attributes,
            confidence=confidence,
            raw_text=text
        )
    
    def _extract_action(self, text: str) -> str:
        """Extrae la acción del texto"""
        for action, patterns in self.ACTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return action
        return "unknown"
    
    def _extract_quantity(self, text: str) -> Optional[int]:
        """Extrae la cantidad del texto"""
        for pattern in self.QUANTITY_PATTERNS:
            match = re.search(pattern, text)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_sku(self, text: str) -> Optional[str]:
        """Extrae el SKU del texto"""
        for pattern in self.SKU_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None
    
    def _extract_product_name(self, text: str, sku: Optional[str]) -> Optional[str]:
        """Extrae el nombre del producto"""
        # Si hay SKU, no necesitamos el nombre
        if sku:
            return None
        
        # Buscar sustantivos comunes de productos
        product_keywords = [
            "polo", "polera", "camisa", "blusa", "jean", "pantalón",
            "short", "bermuda", "falda", "vestido", "chompa", "casaca",
            "zapatilla", "zapato", "sandalia", "gorro", "sombrero"
        ]
        
        for keyword in product_keywords:
            if keyword in text:
                # Intentar extraer contexto alrededor
                pattern = rf"(\w+\s+)?{keyword}(\s+\w+)?"
                match = re.search(pattern, text)
                if match:
                    return match.group(0).strip()
        
        return None
    
    def _extract_attributes(self, text: str) -> Dict[str, str]:
        """Extrae atributos como color y talla"""
        attributes = {}
        
        # Buscar color
        for color in self.COLORS:
            if color in text:
                attributes["color"] = color.capitalize()
                break
        
        # Buscar talla
        for size in self.SIZES:
            # Buscar talla como palabra completa
            pattern = rf"\b{size}\b"
            if re.search(pattern, text, re.IGNORECASE):
                attributes["size"] = size.upper()
                break
        
        # Buscar "talla X"
        talla_match = re.search(r"talla\s+([a-z0-9]+)", text, re.IGNORECASE)
        if talla_match and "size" not in attributes:
            attributes["size"] = talla_match.group(1).upper()
        
        return attributes
    
    def _calculate_confidence(
        self,
        action: str,
        quantity: Optional[int],
        product_name: Optional[str],
        sku: Optional[str],
        attributes: Dict[str, str]
    ) -> float:
        """Calcula el nivel de confianza del parsing"""
        confidence = 0.0
        
        # Acción identificada
        if action != "unknown":
            confidence += 0.4
        
        # Cantidad presente (para acciones que la requieren)
        if quantity is not None and action in ["sell", "add", "remove"]:
            confidence += 0.3
        
        # Producto identificado (SKU o nombre)
        if sku or product_name:
            confidence += 0.2
        
        # Atributos adicionales
        if attributes:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def is_valid_command(self, parsed: ParsedCommand, threshold: float = 0.6) -> bool:
        """
        Verifica si un comando parseado es válido
        
        Args:
            parsed: Comando parseado
            threshold: Umbral mínimo de confianza
        
        Returns:
            True si el comando es válido
        """
        return parsed.confidence >= threshold and parsed.action != "unknown"


# Instancia global del procesador
nlu_processor = NLUProcessor()
