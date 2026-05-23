"""
Validadores de negocio para operaciones de inventario
"""
from typing import Optional, Dict, Any
from datetime import datetime


class InventoryValidator:
    """Validador de operaciones de inventario"""
    
    @staticmethod
    def validate_stock_operation(
        product_sku: str,
        quantity: int,
        operation: str,
        current_stock: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Valida una operación de stock
        
        Args:
            product_sku: SKU del producto
            quantity: Cantidad a operar
            operation: Tipo de operación (sell, add, update, remove)
            current_stock: Stock actual (para validar ventas)
        
        Returns:
            Dict con resultado de validación
        """
        errors = []
        
        # Validar SKU
        if not product_sku or len(product_sku.strip()) == 0:
            errors.append("SKU de producto no puede estar vacío")
        
        # Validar cantidad
        if quantity < 0:
            errors.append("La cantidad no puede ser negativa")
        
        if quantity == 0 and operation != "update":
            errors.append("La cantidad debe ser mayor a 0")
        
        # Validar operación
        valid_operations = ["sell", "add", "update", "remove"]
        if operation not in valid_operations:
            errors.append(f"Operación inválida. Debe ser una de: {', '.join(valid_operations)}")
        
        # Validar stock suficiente para ventas
        if operation == "sell" and current_stock is not None:
            if quantity > current_stock:
                errors.append(
                    f"Stock insuficiente. Disponible: {current_stock}, "
                    f"Solicitado: {quantity}"
                )
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    def validate_product_data(
        sku: str,
        name: str,
        price: float,
        stock: int
    ) -> Dict[str, Any]:
        """
        Valida datos de un producto
        
        Args:
            sku: SKU del producto
            name: Nombre del producto
            price: Precio del producto
            stock: Stock inicial
        
        Returns:
            Dict con resultado de validación
        """
        errors = []
        
        if not sku or len(sku.strip()) == 0:
            errors.append("SKU no puede estar vacío")
        
        if not name or len(name.strip()) == 0:
            errors.append("Nombre no puede estar vacío")
        
        if price < 0:
            errors.append("Precio no puede ser negativo")
        
        if stock < 0:
            errors.append("Stock no puede ser negativo")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "timestamp": datetime.now().isoformat()
        }
