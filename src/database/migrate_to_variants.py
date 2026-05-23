"""
Script de migración: Convertir productos existentes a sistema de variantes
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.connection import get_db, engine
from src.database.models import Base, Product, ProductVariant
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Distribución de stock por talla para cada producto
STOCK_DISTRIBUTION = {
    "POLO-BLANCO-M": {
        "base_sku": "POLO-BLANCO",
        "base_name": "Polo Blanco",
        "variants": {
            "S": 7,
            "M": 10,
            "L": 10,
            "XL": 6,
            "2XL": 2
        }
    },
    "POLO-NEGRO-L": {
        "base_sku": "POLO-NEGRO",
        "base_name": "Polo Negro",
        "variants": {
            "S": 6,
            "M": 8,
            "L": 10,
            "XL": 4,
            "2XL": 2
        }
    },
    "POLO-AZUL-S": {
        "base_sku": "POLO-AZUL",
        "base_name": "Polo Azul",
        "variants": {
            "S": 5,
            "M": 7,
            "L": 8,
            "XL": 4,
            "2XL": 1
        }
    },
    "JEAN-AZUL-32": {
        "base_sku": "JEAN-AZUL",
        "base_name": "Jean Azul",
        "variants": {
            "28": 3,
            "30": 4,
            "32": 6,
            "34": 5,
            "36": 2
        }
    },
    "PANTALON-NEGRO-34": {
        "base_sku": "PANTALON-NEGRO",
        "base_name": "Pantalón Negro",
        "variants": {
            "28": 2,
            "30": 3,
            "32": 4,
            "34": 5,
            "36": 3
        }
    },
    "PANTALON-BEIGE-30": {
        "base_sku": "PANTALON-BEIGE",
        "base_name": "Pantalón Beige",
        "variants": {
            "28": 4,
            "30": 7,
            "32": 7,
            "34": 5
        }
    },
    "CAMISA-BLANCA-M": {
        "base_sku": "CAMISA-BLANCA",
        "base_name": "Camisa Blanca",
        "variants": {
            "S": 5,
            "M": 8,
            "L": 8,
            "XL": 5,
            "2XL": 1
        }
    },
    "CAMISA-CELESTE-L": {
        "base_sku": "CAMISA-CELESTE",
        "base_name": "Camisa Celeste",
        "variants": {
            "S": 4,
            "M": 6,
            "L": 7,
            "XL": 4
        }
    },
    "GORRA-NEGRA": {
        "base_sku": "GORRA-NEGRA",
        "base_name": "Gorra Negra",
        "variants": {
            "UNICA": 43  # Talla única
        }
    },
    "CORREA-MARRON-95": {
        "base_sku": "CORREA-MARRON",
        "base_name": "Correa Marrón 95cm",
        "variants": {
            "95": 34  # Talla única (95cm)
        }
    }
}


def migrate_to_variants():
    """Migrar productos existentes al sistema de variantes"""
    
    logger.info("=" * 60)
    logger.info("INICIANDO MIGRACIÓN A SISTEMA DE VARIANTES")
    logger.info("=" * 60)
    
    try:
        # Crear tablas nuevas
        logger.info("\n1. Creando tabla product_variants...")
        Base.metadata.create_all(engine)
        logger.info("✅ Tabla product_variants creada")
        
        with get_db() as db:
            # Obtener productos existentes
            existing_products = db.query(Product).all()
            logger.info(f"\n2. Productos existentes encontrados: {len(existing_products)}")
            
            migrated_count = 0
            
            for old_product in existing_products:
                logger.info(f"\n   Procesando: {old_product.sku} - {old_product.name}")
                
                # Verificar si este producto debe ser migrado
                if old_product.sku not in STOCK_DISTRIBUTION:
                    logger.warning(f"   ⚠️  Producto {old_product.sku} no está en la configuración de migración")
                    continue
                
                config = STOCK_DISTRIBUTION[old_product.sku]
                
                # Verificar si ya existe el producto padre
                parent_product = db.query(Product).filter(
                    Product.sku == config["base_sku"]
                ).first()
                
                if not parent_product:
                    # Crear producto padre
                    parent_product = Product(
                        sku=config["base_sku"],
                        name=config["base_name"],
                        description=old_product.description,
                        base_price=old_product.price,
                        category=old_product.category,
                        color=old_product.color,
                        image_url=old_product.image_url
                    )
                    db.add(parent_product)
                    db.flush()  # Para obtener el ID
                    logger.info(f"   ✅ Producto padre creado: {parent_product.sku}")
                else:
                    logger.info(f"   ℹ️  Producto padre ya existe: {parent_product.sku}")
                
                # Crear variantes
                for size, stock in config["variants"].items():
                    variant_sku = f"{config['base_sku']}-{size}"
                    
                    # Verificar si la variante ya existe
                    existing_variant = db.query(ProductVariant).filter(
                        ProductVariant.sku == variant_sku
                    ).first()
                    
                    if existing_variant:
                        logger.info(f"      ⚠️  Variante ya existe: {variant_sku}")
                        continue
                    
                    # Distribuir stock entre físico y virtual (60% físico, 40% virtual)
                    stock_physical = int(stock * 0.6)
                    stock_virtual = stock - stock_physical
                    
                    variant = ProductVariant(
                        product_id=parent_product.id,
                        sku=variant_sku,
                        size=size,
                        stock_physical=stock_physical,
                        stock_virtual=stock_virtual,
                        stock_total=stock,
                        price_adjustment=0.0
                    )
                    db.add(variant)
                    logger.info(f"      ✅ Variante creada: {variant_sku} (Talla {size}, Stock: {stock})")
                
                migrated_count += 1
            
            # Commit de todos los cambios
            db.commit()
            
            logger.info("\n" + "=" * 60)
            logger.info(f"✅ MIGRACIÓN COMPLETADA")
            logger.info(f"   Productos migrados: {migrated_count}")
            
            # Mostrar resumen
            total_products = db.query(Product).count()
            total_variants = db.query(ProductVariant).count()
            
            logger.info(f"\n📊 RESUMEN:")
            logger.info(f"   Total productos padre: {total_products}")
            logger.info(f"   Total variantes: {total_variants}")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error(f"\n❌ ERROR EN MIGRACIÓN: {e}")
        raise


def verify_migration():
    """Verificar que la migración fue exitosa"""
    logger.info("\n" + "=" * 60)
    logger.info("VERIFICANDO MIGRACIÓN")
    logger.info("=" * 60)
    
    with get_db() as db:
        products = db.query(Product).all()
        
        for product in products:
            logger.info(f"\n📦 {product.name} ({product.sku})")
            logger.info(f"   Precio base: S/ {product.base_price:.2f}")
            logger.info(f"   Variantes:")
            
            total_stock = 0
            for variant in product.variants:
                total_stock += variant.stock_total
                logger.info(f"      - Talla {variant.size}: {variant.stock_total} unidades (SKU: {variant.sku})")
            
            logger.info(f"   Stock total: {total_stock} unidades")


if __name__ == "__main__":
    logger.info("🚀 Iniciando migración a sistema de variantes...")
    
    response = input("\n⚠️  Esta operación creará nuevas tablas y datos. ¿Continuar? (s/n): ")
    
    if response.lower() == 's':
        migrate_to_variants()
        verify_migration()
        logger.info("\n✅ Proceso completado exitosamente!")
    else:
        logger.info("\n❌ Migración cancelada por el usuario")
