"""
Agente Coordinador (Coordinator Agent)
Responsable de sincronizar el inventario y validar operaciones
"""
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

from src.agents.base_agent import BaseAgent, AgentStatus
from src.database import (
    get_db, Product, Transaction, TransactionType,
    AgentLog, AgentType, SyncHistory
)
from src.utils.validators import InventoryValidator
from src.config import settings


class CoordinatorAgent(BaseAgent):
    """
    Agente Coordinador - Gestión central de inventario
    
    Responsabilidades:
    - Recibir solicitudes del Agente de Tienda
    - Validar operaciones de stock
    - Actualizar base de datos central
    - Detectar y resolver conflictos
    - Aplicar reglas de negocio
    - Sincronizar con plataforma de e-commerce
    """
    
    def __init__(self, agent_id: str = "coordinator_agent_01"):
        super().__init__(agent_id, "coordinator")
        self.validator = InventoryValidator()
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una solicitud de operación de inventario
        
        Args:
            message: {
                "action": "sell|add|update|remove",
                "product_sku": "SKU del producto",
                "quantity": cantidad,
                "vendor_phone": "teléfono del vendedor",
                "timestamp": "ISO timestamp"
            }
        
        Returns:
            Resultado de la operación
        """
        self.update_status(AgentStatus.PROCESSING)
        
        try:
            action = message.get("action")
            product_sku = message.get("product_sku")
            quantity = message.get("quantity")
            vendor_phone = message.get("vendor_phone")
            
            self.log_activity("operation_request", {
                "action": action,
                "sku": product_sku,
                "quantity": quantity
            })
            
            # Ejecutar operación según el tipo
            if action == "sell":
                result = await self._process_sale(product_sku, quantity, vendor_phone)
            elif action == "add":
                result = await self._process_addition(product_sku, quantity, vendor_phone)
            elif action == "update":
                result = await self._process_update(product_sku, quantity, vendor_phone)
            elif action == "remove":
                result = await self._process_removal(product_sku, quantity, vendor_phone)
            else:
                result = {
                    "success": False,
                    "error": f"Acción no reconocida: {action}"
                }
            
            # Registrar en logs
            self._log_operation(action, product_sku, result)
            
            return result
        
        except Exception as e:
            self.handle_error(e, "process_message")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            self.update_status(AgentStatus.IDLE)
    
    async def _process_sale(
        self,
        product_sku: str,
        quantity: int,
        vendor_phone: str
    ) -> Dict[str, Any]:
        """Procesa una venta (reduce stock)"""
        
        try:
            with get_db() as db:
                # Obtener producto
                product = db.query(Product).filter(
                    Product.sku == product_sku
                ).first()
                
                if not product:
                    return {
                        "success": False,
                        "error": f"Producto no encontrado: {product_sku}"
                    }
                
                # Validar operación
                validation = self.validator.validate_stock_operation(
                    product_sku=product_sku,
                    quantity=quantity,
                    operation="sell",
                    current_stock=product.stock_physical
                )
                
                if not validation["valid"]:
                    return {
                        "success": False,
                        "error": ", ".join(validation["errors"])
                    }
                
                # Actualizar stock
                previous_stock = product.stock_physical
                product.stock_physical -= quantity
                product.stock_total = product.stock_physical + product.stock_virtual
                product.updated_at = datetime.utcnow()
                
                # Registrar transacción
                transaction = Transaction(
                    product_id=product.id,
                    transaction_type=TransactionType.SELL,
                    quantity=quantity,
                    previous_stock=previous_stock,
                    new_stock=product.stock_physical,
                    vendor_phone=vendor_phone,
                    notes=f"Venta registrada por {vendor_phone}"
                )
                db.add(transaction)
                
                db.commit()
                
                self.logger.info(
                    f"✅ Venta procesada: {product.name} | "
                    f"Cantidad: {quantity} | "
                    f"Stock: {previous_stock} -> {product.stock_physical}"
                )
                
                return {
                    "success": True,
                    "product": {
                        "sku": product.sku,
                        "name": product.name,
                        "previous_stock": previous_stock,
                        "new_stock": product.stock_physical,
                        "stock_total": product.stock_total
                    },
                    "transaction_id": transaction.id,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error de base de datos en venta: {e}")
            return {
                "success": False,
                "error": "Error al actualizar la base de datos"
            }
    
    async def _process_addition(
        self,
        product_sku: str,
        quantity: int,
        vendor_phone: str
    ) -> Dict[str, Any]:
        """Procesa una adición de stock"""
        
        try:
            with get_db() as db:
                product = db.query(Product).filter(
                    Product.sku == product_sku
                ).first()
                
                if not product:
                    return {
                        "success": False,
                        "error": f"Producto no encontrado: {product_sku}"
                    }
                
                # Validar
                validation = self.validator.validate_stock_operation(
                    product_sku=product_sku,
                    quantity=quantity,
                    operation="add"
                )
                
                if not validation["valid"]:
                    return {
                        "success": False,
                        "error": ", ".join(validation["errors"])
                    }
                
                # Actualizar stock
                previous_stock = product.stock_physical
                product.stock_physical += quantity
                product.stock_total = product.stock_physical + product.stock_virtual
                product.updated_at = datetime.utcnow()
                
                # Registrar transacción
                transaction = Transaction(
                    product_id=product.id,
                    transaction_type=TransactionType.ADD,
                    quantity=quantity,
                    previous_stock=previous_stock,
                    new_stock=product.stock_physical,
                    vendor_phone=vendor_phone,
                    notes=f"Stock agregado por {vendor_phone}"
                )
                db.add(transaction)
                
                db.commit()
                
                self.logger.info(
                    f"✅ Stock agregado: {product.name} | "
                    f"Cantidad: +{quantity} | "
                    f"Stock: {previous_stock} -> {product.stock_physical}"
                )
                
                return {
                    "success": True,
                    "product": {
                        "sku": product.sku,
                        "name": product.name,
                        "previous_stock": previous_stock,
                        "new_stock": product.stock_physical,
                        "stock_total": product.stock_total
                    },
                    "transaction_id": transaction.id,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error de base de datos en adición: {e}")
            return {
                "success": False,
                "error": "Error al actualizar la base de datos"
            }
    
    async def _process_update(
        self,
        product_sku: str,
        quantity: int,
        vendor_phone: str
    ) -> Dict[str, Any]:
        """Procesa una actualización de stock (establece valor absoluto)"""
        
        try:
            with get_db() as db:
                product = db.query(Product).filter(
                    Product.sku == product_sku
                ).first()
                
                if not product:
                    return {
                        "success": False,
                        "error": f"Producto no encontrado: {product_sku}"
                    }
                
                # Actualizar stock
                previous_stock = product.stock_physical
                product.stock_physical = quantity
                product.stock_total = product.stock_physical + product.stock_virtual
                product.updated_at = datetime.utcnow()
                
                # Registrar transacción
                transaction = Transaction(
                    product_id=product.id,
                    transaction_type=TransactionType.UPDATE,
                    quantity=quantity,
                    previous_stock=previous_stock,
                    new_stock=product.stock_physical,
                    vendor_phone=vendor_phone,
                    notes=f"Stock actualizado por {vendor_phone}"
                )
                db.add(transaction)
                
                db.commit()
                
                self.logger.info(
                    f"✅ Stock actualizado: {product.name} | "
                    f"Stock: {previous_stock} -> {product.stock_physical}"
                )
                
                return {
                    "success": True,
                    "product": {
                        "sku": product.sku,
                        "name": product.name,
                        "previous_stock": previous_stock,
                        "new_stock": product.stock_physical,
                        "stock_total": product.stock_total
                    },
                    "transaction_id": transaction.id,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error de base de datos en actualización: {e}")
            return {
                "success": False,
                "error": "Error al actualizar la base de datos"
            }
    
    async def _process_removal(
        self,
        product_sku: str,
        quantity: int,
        vendor_phone: str
    ) -> Dict[str, Any]:
        """Procesa una eliminación de stock (productos dañados, etc.)"""
        
        try:
            with get_db() as db:
                product = db.query(Product).filter(
                    Product.sku == product_sku
                ).first()
                
                if not product:
                    return {
                        "success": False,
                        "error": f"Producto no encontrado: {product_sku}"
                    }
                
                # Validar
                validation = self.validator.validate_stock_operation(
                    product_sku=product_sku,
                    quantity=quantity,
                    operation="remove",
                    current_stock=product.stock_physical
                )
                
                if not validation["valid"]:
                    return {
                        "success": False,
                        "error": ", ".join(validation["errors"])
                    }
                
                # Actualizar stock
                previous_stock = product.stock_physical
                product.stock_physical -= quantity
                product.stock_total = product.stock_physical + product.stock_virtual
                product.updated_at = datetime.utcnow()
                
                # Registrar transacción
                transaction = Transaction(
                    product_id=product.id,
                    transaction_type=TransactionType.REMOVE,
                    quantity=quantity,
                    previous_stock=previous_stock,
                    new_stock=product.stock_physical,
                    vendor_phone=vendor_phone,
                    notes=f"Stock eliminado por {vendor_phone}"
                )
                db.add(transaction)
                
                db.commit()
                
                self.logger.info(
                    f"✅ Stock eliminado: {product.name} | "
                    f"Cantidad: -{quantity} | "
                    f"Stock: {previous_stock} -> {product.stock_physical}"
                )
                
                return {
                    "success": True,
                    "product": {
                        "sku": product.sku,
                        "name": product.name,
                        "previous_stock": previous_stock,
                        "new_stock": product.stock_physical,
                        "stock_total": product.stock_total
                    },
                    "transaction_id": transaction.id,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        except SQLAlchemyError as e:
            self.logger.error(f"Error de base de datos en eliminación: {e}")
            return {
                "success": False,
                "error": "Error al actualizar la base de datos"
            }
    
    def _log_operation(
        self,
        action: str,
        product_sku: str,
        result: Dict[str, Any]
    ):
        """Registra la operación en los logs de agente"""
        
        try:
            with get_db() as db:
                log = AgentLog(
                    agent_type=AgentType.COORDINATOR,
                    action=f"inventory_{action}",
                    message=f"Operación {action} en producto {product_sku}",
                    metadata=str(result),
                    status="success" if result.get("success") else "error"
                )
                db.add(log)
                db.commit()
        except Exception as e:
            self.logger.error(f"Error al registrar log: {e}")


# Instancia global del agente coordinador
coordinator_agent = CoordinatorAgent()
