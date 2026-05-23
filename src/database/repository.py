"""
Repositorio de Productos - Acceso a datos con DTOs
Evita problemas de DetachedInstanceError devolviendo objetos simples
"""
from typing import Optional, List
from sqlalchemy.orm import joinedload

from src.database.connection import get_db
from src.database.models import Product, ProductVariant
from src.agents.dtos import VariantDTO, ProductDTO, StockUpdateResult
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ProductRepository:
    """Repositorio para acceder a productos y variantes"""
    
    @staticmethod
    def find_variant(
        product_name: Optional[str] = None,
        color: Optional[str] = None,
        size: Optional[str] = None,
        sku: Optional[str] = None
    ) -> Optional[VariantDTO]:
        """
        Busca una variante de producto y retorna un DTO
        
        Args:
            product_name: Nombre del producto (ej: "Polo Blanco")
            color: Color del producto
            size: Talla (ej: "M", "32")
            sku: SKU directo de la variante
        
        Returns:
            VariantDTO o None si no se encuentra
        """
        try:
            with get_db() as db:
                # Búsqueda por SKU directo
                if sku:
                    variant = db.query(ProductVariant).options(
                        joinedload(ProductVariant.product)
                    ).filter(ProductVariant.sku == sku).first()
                    
                    if variant:
                        return ProductRepository._variant_to_dto(variant)
                
                # Búsqueda por nombre/color/talla
                if product_name:
                    query = db.query(Product).options(
                        joinedload(Product.variants)
                    ).filter(Product.name.ilike(f"%{product_name}%"))
                    
                    if color:
                        query = query.filter(Product.color.ilike(f"%{color}%"))
                    
                    product = query.first()
                    
                    if product:
                        # Si se especificó talla, buscar variante específica
                        if size:
                            for v in product.variants:
                                if v.size.upper() == size.upper():
                                    return ProductRepository._variant_to_dto(v, product)
                        else:
                            # Retornar primera variante disponible
                            if product.variants:
                                return ProductRepository._variant_to_dto(
                                    product.variants[0], product
                                )
                
                return None
                
        except Exception as e:
            logger.error(f"Error buscando variante: {e}")
            return None
    
    @staticmethod
    def update_stock(
        variant_id: int, 
        quantity_change: int,
        operation: str = "sell"
    ) -> StockUpdateResult:
        """
        Actualiza el stock de una variante
        
        Args:
            variant_id: ID de la variante
            quantity_change: Cantidad a cambiar (positivo para agregar, negativo para vender)
            operation: Tipo de operación ("sell", "add")
        
        Returns:
            StockUpdateResult con el resultado
        """
        try:
            with get_db() as db:
                variant = db.query(ProductVariant).options(
                    joinedload(ProductVariant.product)
                ).filter(ProductVariant.id == variant_id).first()
                
                if not variant:
                    return StockUpdateResult(
                        success=False,
                        variant_sku="",
                        product_name="",
                        size="",
                        quantity_changed=0,
                        new_stock=0,
                        message="Variante no encontrada"
                    )
                
                # Calcular nuevo stock
                if operation == "sell":
                    # Para ventas, restamos
                    new_stock = variant.stock_total - abs(quantity_change)
                    if new_stock < 0:
                        return StockUpdateResult(
                            success=False,
                            variant_sku=variant.sku,
                            product_name=variant.product.name,
                            size=variant.size,
                            quantity_changed=0,
                            new_stock=variant.stock_total,
                            message=f"Stock insuficiente. Disponible: {variant.stock_total}"
                        )
                    variant.stock_total = new_stock
                    variant.stock_physical = max(0, variant.stock_physical - abs(quantity_change))
                else:
                    # Para agregar, sumamos
                    variant.stock_total += abs(quantity_change)
                    variant.stock_physical += abs(quantity_change)
                    new_stock = variant.stock_total
                
                db.commit()
                
                logger.info(f"Stock actualizado: {variant.sku} -> {new_stock}")
                
                return StockUpdateResult(
                    success=True,
                    variant_sku=variant.sku,
                    product_name=variant.product.name,
                    size=variant.size,
                    quantity_changed=abs(quantity_change),
                    new_stock=new_stock,
                    message="Stock actualizado correctamente"
                )
                
        except Exception as e:
            logger.error(f"Error actualizando stock: {e}")
            return StockUpdateResult(
                success=False,
                variant_sku="",
                product_name="",
                size="",
                quantity_changed=0,
                new_stock=0,
                message=f"Error: {str(e)}"
            )
    
    @staticmethod
    def list_all_products() -> List[ProductDTO]:
        """
        Lista todos los productos con sus variantes
        
        Returns:
            Lista de ProductDTO
        """
        try:
            with get_db() as db:
                products = db.query(Product).options(
                    joinedload(Product.variants)
                ).all()
                
                result = []
                for p in products:
                    variants = [
                        VariantDTO(
                            id=v.id,
                            sku=v.sku,
                            size=v.size,
                            stock_physical=v.stock_physical,
                            stock_virtual=v.stock_virtual,
                            stock_total=v.stock_total,
                            product_id=p.id,
                            product_name=p.name,
                            product_price=p.base_price,
                            product_color=p.color
                        )
                        for v in p.variants
                    ]
                    
                    result.append(ProductDTO(
                        id=p.id,
                        sku=p.sku,
                        name=p.name,
                        description=p.description,
                        base_price=p.base_price,
                        category=p.category,
                        color=p.color,
                        image_url=p.image_url,
                        variants=variants
                    ))
                
                return result
                
        except Exception as e:
            logger.error(f"Error listando productos: {e}")
            return []
    
    @staticmethod
    def _variant_to_dto(variant: ProductVariant, product: Product = None) -> VariantDTO:
        """Convierte un ORM ProductVariant a VariantDTO"""
        if product is None:
            product = variant.product
            
        return VariantDTO(
            id=variant.id,
            sku=variant.sku,
            size=variant.size,
            stock_physical=variant.stock_physical,
            stock_virtual=variant.stock_virtual,
            stock_total=variant.stock_total,
            product_id=product.id,
            product_name=product.name,
            product_price=product.base_price,
            product_color=product.color
        )


# Singleton para uso global
product_repository = ProductRepository()
