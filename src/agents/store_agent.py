"""
Agente de Tienda (Store Agent) - Interfaz de WhatsApp
Responsable de guiar al vendedor mediante un menú interactivo paso a paso
"""
from typing import Dict, Any
from datetime import datetime

from src.agents.base_agent import BaseAgent, AgentStatus
from src.agents.conversation_state import conversation_manager, ConversationStep
from src.database.repository import product_repository


class StoreAgent(BaseAgent):
    """
    Agente de Tienda - Maneja el menú interactivo con el vendedor
    """
    
    def __init__(self, agent_id: str = "store_agent_01"):
        super().__init__(agent_id, "store")
        self.conversations = conversation_manager
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un mensaje de WhatsApp (texto o interactivo)"""
        self.update_status(AgentStatus.PROCESSING)
        
        try:
            phone = message.get("from")
            msg_type = message.get("type")
            context = self.conversations.get_context(phone)
            
            # Limpiar estado si expira o manda algo que no encaja, o si pide salir
            if msg_type == "text":
                text = message.get("text", "").strip().lower()
                if text in ["salir", "cancelar", "menu", "menú", "hola"]:
                    context.reset()
                    return self._send_main_menu(phone)
            
            # Manejar estados de la máquina de estados
            if context.step == ConversationStep.IDLE:
                if msg_type == "interactive" and message.get("interactive_type") == "list_reply":
                    return self._handle_main_menu_selection(phone, message.get("interactive_id"), context)
                return self._send_main_menu(phone)
                
            elif context.step == ConversationStep.AWAITING_PRODUCT:
                if msg_type == "interactive" and message.get("interactive_type") == "list_reply":
                    return self._handle_product_selection(phone, message.get("interactive_id"), context)
                # Si mandó otra cosa, recordarle que elija
                return self._send_product_list(phone, context)
                
            elif context.step == ConversationStep.AWAITING_SIZE:
                if msg_type == "interactive" and message.get("interactive_type") == "list_reply":
                    return self._handle_size_selection(phone, message.get("interactive_id"), context)
                return self._send_size_list(phone, context)
                
            elif context.step == ConversationStep.AWAITING_QUANTITY:
                if msg_type == "text":
                    return self._handle_quantity_input(phone, message.get("text", ""), context)
                return self._send_quantity_prompt(phone, context)
                
            elif context.step == ConversationStep.AWAITING_CONFIRM:
                if msg_type == "interactive" and message.get("interactive_type") == "button_reply":
                    return self._handle_confirmation(phone, message.get("interactive_id"), context)
                return self._send_confirmation(phone, context)
            
            # Por si cae en un estado no manejado
            context.reset()
            return self._send_main_menu(phone)
                
        except Exception as e:
            self.logger.error(f"❌ Error en store_agent: {e}", exc_info=True)
            if 'phone' in locals():
                self.conversations.reset_context(phone)
            return {
                "to": message.get("from"),
                "response_type": "text",
                "text": "❌ Ocurrió un error inesperado. Volviendo al menú principal.\nEscribe 'menu' para intentar de nuevo.",
                "agent_id": self.agent_id
            }
        finally:
            self.update_status(AgentStatus.IDLE)

    # ============= PASO 1: Menú Principal =============

    def _send_main_menu(self, to: str) -> Dict[str, Any]:
        """Envía el menú principal con lista interactiva"""
        body = (
            "🤖 *MAS-CIS - Menú Principal*\n\n"
            "Selecciona una opción para gestionar tu inventario:"
        )
        sections = [
            {
                "title": "Opciones",
                "rows": [
                    {
                        "id": "menu_sell",
                        "title": "📦 Registrar Venta",
                        "description": "Registra salida de polos vendidos"
                    },
                    {
                        "id": "menu_add",
                        "title": "➕ Registrar Ingreso",
                        "description": "Ingreso de lote del taller"
                    },
                    {
                        "id": "menu_remove",
                        "title": "⚠️ Registrar Merma",
                        "description": "Reporta prendas dañadas o falla"
                    },
                    {
                        "id": "menu_inventory",
                        "title": "📋 Ver Inventario",
                        "description": "Consulta el stock actual"
                    }
                ]
            }
        ]
        
        return {
            "to": to,
            "response_type": "interactive_list",
            "body": body,
            "button_label": "📋 Ver Opciones",
            "sections": sections,
            "agent_id": self.agent_id
        }

    def _handle_main_menu_selection(self, to: str, selection_id: str, context: Any) -> Dict[str, Any]:
        """Maneja la selección del menú principal"""
        if selection_id == "menu_inventory":
            return self._handle_inventory(to)
            
        elif selection_id == "menu_sell":
            context.action = "sell"
            context.step = ConversationStep.AWAITING_PRODUCT
            context.touch()
            return self._send_product_list(to, context)
            
        elif selection_id == "menu_add":
            context.action = "add"
            context.step = ConversationStep.AWAITING_PRODUCT
            context.touch()
            return self._send_product_list(to, context)
            
        elif selection_id == "menu_remove":
            context.action = "remove"
            context.step = ConversationStep.AWAITING_PRODUCT
            context.touch()
            return self._send_product_list(to, context)
            
        else:
            return self._send_main_menu(to)

    # ============= PASO 2: Selección de Producto =============

    def _send_product_list(self, to: str, context: Any) -> Dict[str, Any]:
        """Envía lista de productos (solo polos)"""
        action_names = {
            "sell": "vendiste",
            "add": "ingresó del taller",
            "remove": "presenta falla"
        }
        action_name = action_names.get(context.action, "seleccionas")
        
        body = f"📦 ¿Qué polo {action_name}?"
        
        sections = [
            {
                "title": "Polos",
                "rows": [
                    {"id": "prod_POLO-BLANCO", "title": "Polo Blanco"},
                    {"id": "prod_POLO-NEGRO", "title": "Polo Negro"},
                    {"id": "prod_POLO-AZUL", "title": "Polo Azul"}
                ]
            }
        ]
        
        return {
            "to": to,
            "response_type": "interactive_list",
            "body": body,
            "button_label": "👕 Seleccionar Polo",
            "sections": sections,
            "agent_id": self.agent_id
        }

    def _handle_product_selection(self, to: str, selection_id: str, context: Any) -> Dict[str, Any]:
        """Maneja el producto elegido"""
        if not selection_id.startswith("prod_"):
            return self._send_product_list(to, context)
            
        sku = selection_id.replace("prod_", "")
        
        # Validar si existe el producto
        variant_dto = product_repository.find_variant(product_name=sku)
        if not variant_dto:
            variant_dto = product_repository.find_variant(sku=sku)
            
        # Si no lo encuentra por exact match, intentar por nombre
        if not variant_dto:
            name_map = {
                "POLO-BLANCO": "Polo Blanco",
                "POLO-NEGRO": "Polo Negro",
                "POLO-AZUL": "Polo Azul"
            }
            context.product_name = name_map.get(sku, sku)
        else:
            context.product_name = variant_dto.product_name
            
        context.product_sku = sku
        context.step = ConversationStep.AWAITING_SIZE
        context.touch()
        
        return self._send_size_list(to, context)

    # ============= PASO 3: Selección de Talla =============

    def _send_size_list(self, to: str, context: Any) -> Dict[str, Any]:
        """Envía las tallas disponibles y su stock"""
        # Obtener todas las variantes de este producto
        products = product_repository.list_all_products()
        product = next((p for p in products if p.sku == context.product_sku or p.name.lower() == context.product_name.lower()), None)
        
        if not product or not product.variants:
            context.reset()
            return {
                "to": to,
                "response_type": "text",
                "text": f"❌ Error: No se encontraron tallas para {context.product_name}.\nVuelve al menú escribiendo 'menu'.",
                "agent_id": self.agent_id
            }

        body = f"📏 Selecciona la talla\nProducto: {context.product_name}"
        rows = []
        
        for v in product.variants:
            stock = v.stock_total
            if stock > 5:
                emoji = "✅"
            elif stock > 0:
                emoji = "⚠️"
            else:
                emoji = "❌"
                
            rows.append({
                "id": f"size_{v.id}",
                "title": f"Talla {v.size}",
                "description": f"Stock: {stock} {emoji}"
            })
            
        sections = [
            {
                "title": "Tallas Disponibles",
                "rows": rows[:10]  # Max 10 por list message
            }
        ]
        
        return {
            "to": to,
            "response_type": "interactive_list",
            "body": body,
            "button_label": "📏 Elegir Talla",
            "sections": sections,
            "agent_id": self.agent_id
        }

    def _handle_size_selection(self, to: str, selection_id: str, context: Any) -> Dict[str, Any]:
        """Maneja la talla elegida"""
        if not selection_id.startswith("size_"):
            return self._send_size_list(to, context)
            
        variant_id = int(selection_id.replace("size_", ""))
        
        # Buscar el nombre de la talla y stock actual
        products = product_repository.list_all_products()
        variant = None
        for p in products:
            for v in p.variants:
                if v.id == variant_id:
                    variant = v
                    break
        
        if not variant:
            context.reset()
            return {
                "to": to,
                "response_type": "text",
                "text": "❌ Variante no encontrada. Reiniciando...",
                "agent_id": self.agent_id
            }
            
        context.variant_id = variant_id
        context.variant_sku = variant.sku
        context.size = variant.size
        context.step = ConversationStep.AWAITING_QUANTITY
        context.touch()
        
        return self._send_quantity_prompt(to, context)

    # ============= PASO 4: Cantidad =============

    def _send_quantity_prompt(self, to: str, context: Any) -> Dict[str, Any]:
        """Solicita la cantidad por texto"""
        action_names = {
            "sell": "vendiste",
            "add": "ingresó",
            "remove": "presenta falla"
        }
        action_name = action_names.get(context.action, "seleccionaste")
        
        # Obtener stock actual para contexto
        variant = product_repository.find_variant(sku=context.variant_sku)
        stock_msg = f"\nStock disponible: {variant.stock_total}" if variant else ""
        
        body = (
            f"🔢 ¿Cuántas unidades {action_name}?\n\n"
            f"Producto: {context.product_name} - Talla {context.size}{stock_msg}\n\n"
            f"👉 Escribe la cantidad (ejemplo: 2):"
        )
        
        return {
            "to": to,
            "response_type": "text",
            "text": body,
            "agent_id": self.agent_id
        }

    def _handle_quantity_input(self, to: str, text: str, context: Any) -> Dict[str, Any]:
        """Procesa y valida la cantidad ingresada"""
        try:
            quantity = int(text.strip())
            if quantity <= 0:
                raise ValueError("Cantidad no válida")
        except ValueError:
            return {
                "to": to,
                "response_type": "text",
                "text": "❌ Ingresa un número válido mayor a 0.\n👉 Escribe la cantidad:",
                "agent_id": self.agent_id
            }
            
        # Validación extra: Merma sobre stock 0 o Ventas mayores al stock
        variant = product_repository.find_variant(sku=context.variant_sku)
        stock_total = variant.stock_total if variant else 0
        
        if context.action in ["sell", "remove"] and quantity > stock_total:
            context.reset()
            return {
                "to": to,
                "response_type": "interactive_buttons",
                "body": (
                    f"❌ *STOCK INSUFICIENTE*\n\n"
                    f"Producto: {context.product_name} - Talla {context.size}\n"
                    f"Stock disponible: {stock_total}\n"
                    f"Cantidad solicitada: {quantity}\n\n"
                    f"No se puede procesar la operación."
                ),
                "buttons": [
                    {"id": "menu_sell" if context.action=="sell" else "menu_remove", "title": "🔄 Intentar de nuevo"},
                    {"id": "menu_main", "title": "🏠 Menú Principal"}
                ],
                "agent_id": self.agent_id
            }
            
        context.quantity = quantity
        context.step = ConversationStep.AWAITING_CONFIRM
        context.touch()
        
        return self._send_confirmation(to, context)

    # ============= PASO 5: Confirmación =============

    def _send_confirmation(self, to: str, context: Any) -> Dict[str, Any]:
        """Envía el resumen y botones de confirmar/cancelar"""
        action_names = {
            "sell": "VENTA",
            "add": "INGRESO",
            "remove": "MERMA"
        }
        op_name = action_names.get(context.action, "OPERACIÓN")
        
        body = (
            f"📋 *Confirma la operación:*\n\n"
            f"Operación: {op_name}\n"
            f"Producto: {context.product_name}\n"
            f"Talla: {context.size}\n"
            f"Cantidad: {context.quantity} unidades\n\n"
            f"¿Es correcto?"
        )
        
        buttons = [
            {"id": "confirm_yes", "title": "✅ Confirmar"},
            {"id": "confirm_no", "title": "❌ Cancelar"}
        ]
        
        return {
            "to": to,
            "response_type": "interactive_buttons",
            "body": body,
            "buttons": buttons,
            "agent_id": self.agent_id
        }

    def _handle_confirmation(self, to: str, selection_id: str, context: Any) -> Dict[str, Any]:
        """Maneja la confirmación o cancelación"""
        if selection_id == "confirm_no":
            context.reset()
            return {
                "to": to,
                "response_type": "text",
                "text": "❌ Operación cancelada.\nEscribe 'menu' para volver al inicio.",
                "agent_id": self.agent_id
            }
            
        if selection_id == "confirm_yes":
            # Ejecutar al coordinador!
            # El message_router se encarga de enviarlo al coordinator_agent si lo devolvemos aquí
            # O podemos actualizar la lógica del coordinator request
            request = {
                "action": context.action,
                "product_sku": context.variant_sku,
                "quantity": context.quantity,
                "vendor_phone": to
            }
            
            # Limpiar contexto antes de retornar
            context.reset()
            
            return {
                "requires_coordinator": True,
                "coordinator_request": request,
                "to": to,
                "agent_id": self.agent_id
            }
            
        return self._send_confirmation(to, context)

    # ============= Opciones directas =============

    def _handle_inventory(self, to: str) -> Dict[str, Any]:
        """Ver Inventario desde el menú"""
        products = product_repository.list_all_products()
        
        if not products:
            return {
                "to": to,
                "response_type": "text",
                "text": "📭 No hay productos registrados en el inventario.",
                "agent_id": self.agent_id
            }
        
        msg = "📋 *INVENTARIO ACTUAL*\n"
        msg += "═" * 20 + "\n\n"
        
        for product in products:
            msg += f"📦 *{product.name}*\n"
            msg += f"   📊 Stock total: {product.total_stock} unidades\n"
            
            if product.variants:
                for v in product.variants:
                    emoji = "✅" if v.stock_total > 5 else ("⚠️" if v.stock_total > 0 else "❌")
                    msg += f"      {emoji} Talla {v.size}: {v.stock_total}\n"
            
            msg += "\n"
        
        msg += "─" * 20 + "\n"
        msg += "💡 Escribe 'menu' para volver."
        
        return {
            "to": to,
            "response_type": "text",
            "text": msg,
            "agent_id": self.agent_id
        }


# Instancia singleton
store_agent = StoreAgent()
