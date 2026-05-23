"""
Agente de Tienda (Store Agent) - Refactorizado con DTOs
Responsable de interactuar con el vendedor vía WhatsApp y procesar comandos
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.agents.base_agent import BaseAgent, AgentStatus
from src.agents.nlu_processor import nlu_processor, ParsedCommand
from src.agents.dtos import VariantDTO, ProductDTO, StockUpdateResult
from src.database.repository import product_repository
from src.config import settings


class StoreAgent(BaseAgent):
    """
    Agente de Tienda - Interfaz con el vendedor
    
    Responsabilidades:
    - Recibir mensajes de WhatsApp del vendedor
    - Procesar lenguaje natural con NLU
    - Ejecutar operaciones de inventario
    - Responder al vendedor con confirmaciones
    """
    
    def __init__(self, agent_id: str = "store_agent_01"):
        super().__init__(agent_id, "store")
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un mensaje del vendedor
        
        Args:
            message: {"from": "phone_number", "text": "mensaje", "timestamp": "..."}
        
        Returns:
            Respuesta para enviar al vendedor
        """
        self.update_status(AgentStatus.PROCESSING)
        
        try:
            vendor_phone = message.get("from")
            text = message.get("text", "").strip()
            
            if not text:
                return self._create_response(vendor_phone, "No recibí ningún mensaje.")
            
            self.log_activity("message_received", {
                "vendor": vendor_phone,
                "text_length": len(text)
            })
            
            # Parsear comando con NLU local
            parsed = nlu_processor.parse(text)
            
            self.logger.info(
                f"📝 Comando parseado: {parsed.action} | "
                f"Confianza: {parsed.confidence:.2f}"
            )
            
            # Procesar según la acción detectada
            if parsed.action == "greeting":
                return self._handle_greeting(vendor_phone)
            
            elif parsed.action == "inventory":
                return self._handle_inventory(vendor_phone)
            
            elif parsed.action == "sell":
                return self._handle_sell(parsed, vendor_phone)
            
            elif parsed.action == "add":
                return self._handle_add(parsed, vendor_phone)
            
            elif parsed.action == "query":
                return self._handle_query(parsed, vendor_phone)
            
            else:
                # Comando no reconocido - mostrar ayuda
                return self._handle_help(vendor_phone)
                
        except Exception as e:
            self.logger.error(f"❌ Error en store (process_message): {e}", exc_info=True)
            return self._create_response(
                message.get("from"),
                "❌ Ocurrió un error al procesar tu mensaje. Intenta nuevamente."
            )
        finally:
            self.update_status(AgentStatus.IDLE)
    
    def _handle_greeting(self, vendor_phone: str) -> Dict[str, Any]:
        """Responde a saludos con menú de opciones"""
        
        greeting = (
            "¡Hola! 👋 Soy tu asistente de inventario.\n\n"
            "Puedo ayudarte con:\n\n"
            "📦 *VENTAS*\n"
            "   • Vendí 3 polos blancos talla M\n"
            "   • Salieron 2 jeans azules talla 32\n\n"
            "➕ *AGREGAR STOCK*\n"
            "   • Agregar 5 camisas blancas talla L\n"
            "   • Llegaron 10 gorras negras\n\n"
            "🔍 *CONSULTAR PRODUCTO*\n"
            "   • ¿Cuánto stock hay de polo blanco?\n"
            "   • Stock de POLO-BLANCO-M\n\n"
            "📋 *VER TODO EL INVENTARIO*\n"
            "   • Ver inventario\n"
            "   • Mostrar todos los productos\n\n"
            "¿En qué puedo ayudarte hoy?"
        )
        
        return self._create_response(vendor_phone, greeting)
    
    def _handle_inventory(self, vendor_phone: str) -> Dict[str, Any]:
        """Muestra el inventario completo"""
        
        products = product_repository.list_all_products()
        
        if not products:
            return self._create_response(
                vendor_phone, 
                "📭 No hay productos registrados en el inventario."
            )
        
        msg = "📋 *INVENTARIO ACTUAL*\n"
        msg += "═" * 20 + "\n\n"
        
        for product in products:
            msg += f"📦 *{product.name}*\n"
            msg += f"   💰 Precio: S/ {product.base_price:.2f}\n"
            msg += f"   📊 Stock total: {product.total_stock} unidades\n"
            
            # Mostrar stock por talla
            if product.variants:
                for v in product.variants:
                    emoji = "✅" if v.stock_total > 5 else ("⚠️" if v.stock_total > 0 else "❌")
                    msg += f"      {emoji} Talla {v.size}: {v.stock_total}\n"
            
            msg += "\n"
        
        msg += "─" * 20 + "\n"
        msg += "💡 Para más detalles escribe:\n"
        msg += "   'Stock de [producto]'"
        
        return self._create_response(vendor_phone, msg)
    
    def _handle_sell(self, parsed: ParsedCommand, vendor_phone: str) -> Dict[str, Any]:
        """Procesa una venta y actualiza el stock REAL"""
        
        # Buscar el producto
        variant = product_repository.find_variant(
            product_name=parsed.product_name,
            color=parsed.color,
            size=parsed.size,
            sku=parsed.product_sku
        )
        
        if not variant:
            return self._create_response(
                vendor_phone,
                f"❌ No encontré el producto: {parsed.product_name or parsed.product_sku}\n\n"
                "Verifica:\n"
                "• Nombre del producto\n"
                "• Talla correcta\n"
                "• Que esté registrado en el sistema"
            )
        
        quantity = parsed.quantity or 1
        
        # Actualizar stock REAL en base de datos
        result = product_repository.update_stock(
            variant_id=variant.id,
            quantity_change=quantity,
            operation="sell"
        )
        
        if result.success:
            response = (
                f"✅ *VENTA REGISTRADA*\n\n"
                f"📦 Producto: {result.product_name}\n"
                f"📏 Talla: {result.size}\n"
                f"🏷️ SKU: {result.variant_sku}\n"
                f"🔢 Cantidad vendida: {result.quantity_changed}\n"
                f"📊 Stock restante: {result.new_stock}\n\n"
                f"✨ El stock se actualizó en la web automáticamente."
            )
            
            self.log_activity("sale_completed", {
                "variant_sku": result.variant_sku,
                "quantity": result.quantity_changed,
                "new_stock": result.new_stock
            })
        else:
            response = (
                f"⚠️ *NO SE PUDO COMPLETAR LA VENTA*\n\n"
                f"📦 Producto: {variant.product_name}\n"
                f"📏 Talla: {variant.size}\n"
                f"❌ Motivo: {result.message}\n\n"
                f"Stock actual: {variant.stock_total}"
            )
        
        return self._create_response(vendor_phone, response)
    
    def _handle_add(self, parsed: ParsedCommand, vendor_phone: str) -> Dict[str, Any]:
        """Agrega stock a un producto"""
        
        variant = product_repository.find_variant(
            product_name=parsed.product_name,
            color=parsed.color,
            size=parsed.size,
            sku=parsed.product_sku
        )
        
        if not variant:
            return self._create_response(
                vendor_phone,
                f"❌ No encontré el producto: {parsed.product_name or parsed.product_sku}\n\n"
                "Verifica el nombre y la talla."
            )
        
        quantity = parsed.quantity or 1
        
        result = product_repository.update_stock(
            variant_id=variant.id,
            quantity_change=quantity,
            operation="add"
        )
        
        if result.success:
            response = (
                f"✅ *STOCK AGREGADO*\n\n"
                f"📦 Producto: {result.product_name}\n"
                f"📏 Talla: {result.size}\n"
                f"➕ Cantidad agregada: {result.quantity_changed}\n"
                f"📊 Nuevo stock: {result.new_stock}\n\n"
                f"✨ El stock se actualizó en la web automáticamente."
            )
            
            self.log_activity("stock_added", {
                "variant_sku": result.variant_sku,
                "quantity": result.quantity_changed,
                "new_stock": result.new_stock
            })
        else:
            response = f"❌ Error: {result.message}"
        
        return self._create_response(vendor_phone, response)
    
    def _handle_query(self, parsed: ParsedCommand, vendor_phone: str) -> Dict[str, Any]:
        """Consulta stock de un producto específico"""
        
        # Si no hay producto específico, mostrar inventario general
        if not parsed.product_name and not parsed.product_sku:
            return self._handle_inventory(vendor_phone)
        
        variant = product_repository.find_variant(
            product_name=parsed.product_name,
            color=parsed.color,
            size=parsed.size,
            sku=parsed.product_sku
        )
        
        if not variant:
            return self._create_response(
                vendor_phone,
                f"❌ No encontré el producto: {parsed.product_name or parsed.product_sku}"
            )
        
        # Si se consultó una talla específica
        if parsed.size or parsed.product_sku:
            response = (
                f"📦 *{variant.product_name}*\n\n"
                f"📏 Talla: {variant.size}\n"
                f"🏷️ SKU: {variant.sku}\n"
                f"💰 Precio: S/ {variant.product_price:.2f}\n"
                f"📊 Stock disponible: {variant.stock_total}\n"
                f"   • Físico: {variant.stock_physical}\n"
                f"   • Virtual: {variant.stock_virtual}"
            )
        else:
            # Mostrar todas las tallas del producto
            products = product_repository.list_all_products()
            product = next((p for p in products if p.id == variant.product_id), None)
            
            if product:
                response = f"📦 *{product.name}*\n"
                response += f"💰 Precio: S/ {product.base_price:.2f}\n\n"
                response += "📏 *Stock por talla:*\n"
                
                for v in product.variants:
                    emoji = "✅" if v.stock_total > 5 else ("⚠️" if v.stock_total > 0 else "❌")
                    response += f"   {emoji} Talla {v.size}: {v.stock_total} unidades\n"
                
                response += f"\n📊 *Total:* {product.total_stock} unidades"
            else:
                response = f"📊 Stock de {variant.product_name} talla {variant.size}: {variant.stock_total}"
        
        return self._create_response(vendor_phone, response)
    
    def _handle_help(self, vendor_phone: str) -> Dict[str, Any]:
        """Muestra ayuda cuando no se entiende el comando"""
        
        help_text = (
            "❓ No entendí bien tu mensaje.\n\n"
            "Intenta con frases como:\n\n"
            "• Vendí 3 polos blancos talla M\n"
            "• Agregar 5 jeans azules talla 32\n"
            "• ¿Cuánto stock hay de polo blanco?\n"
            "• Ver inventario\n\n"
            "O escribe *hola* para ver todas las opciones."
        )
        
        return self._create_response(vendor_phone, help_text)
    
    def _create_response(self, to: str, text: str) -> Dict[str, Any]:
        """Crea una respuesta formateada"""
        return {
            "to": to,
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id
        }


# Instancia singleton
store_agent = StoreAgent()
