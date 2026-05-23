"""
Script para recrear la base de datos con el nuevo esquema de variantes
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


# Productos con sus variantes
PRODUCTS_WITH_VARIANTS = [
    {
        "sku": "POLO-BLANCO",
        "name": "Polo Blanco",
        "description": "Polo básico de algodón color blanco",
        "base_price": 25.00,
        "category": "Polos",
        "color": "Blanco",
        "image_url": "https://via.placeholder.com/300x300/FFFFFF/000000?text=Polo+Blanco",
        "variants": [
            {"size": "S", "stock_physical": 4, "stock_virtual": 3},
            {"size": "M", "stock_physical": 6, "stock_virtual": 4},
            {"size": "L", "stock_physical": 6, "stock_virtual": 4},
            {"size": "XL", "stock_physical": 4, "stock_virtual": 2},
            {"size": "2XL", "stock_physical": 1, "stock_virtual": 1},
        ]
    },
    {
        "sku": "POLO-NEGRO",
        "name": "Polo Negro",
        "description": "Polo básico de algodón color negro",
        "base_price": 25.00,
        "category": "Polos",
        "color": "Negro",
        "image_url": "https://via.placeholder.com/300x300/000000/FFFFFF?text=Polo+Negro",
        "variants": [
            {"size": "S", "stock_physical": 4, "stock_virtual": 2},
            {"size": "M", "stock_physical": 5, "stock_virtual": 3},
            {"size": "L", "stock_physical": 6, "stock_virtual": 4},
            {"size": "XL", "stock_physical": 2, "stock_virtual": 2},
            {"size": "2XL", "stock_physical": 1, "stock_virtual": 1},
        ]
    },
    {
        "sku": "POLO-AZUL",
        "name": "Polo Azul",
        "description": "Polo básico de algodón color azul",
        "base_price": 25.00,
        "category": "Polos",
        "color": "Azul",
        "image_url": "https://via.placeholder.com/300x300/0000FF/FFFFFF?text=Polo+Azul",
        "variants": [
            {"size": "S", "stock_physical": 3, "stock_virtual": 2},
            {"size": "M", "stock_physical": 4, "stock_virtual": 3},
            {"size": "L", "stock_physical": 5, "stock_virtual": 3},
            {"size": "XL", "stock_physical": 2, "stock_virtual": 2},
            {"size": "2XL", "stock_physical": 1, "stock_virtual": 0},
        ]
    },
    {
        "sku": "JEAN-AZUL",
        "name": "Jean Azul",
        "description": "Jean clásico de mezclilla azul",
        "base_price": 85.00,
        "category": "Pantalones",
        "color": "Azul",
        "image_url": "https://via.placeholder.com/300x300/4169E1/FFFFFF?text=Jean+Azul",
        "variants": [
            {"size": "28", "stock_physical": 2, "stock_virtual": 1},
            {"size": "30", "stock_physical": 2, "stock_virtual": 2},
            {"size": "32", "stock_physical": 4, "stock_virtual": 2},
            {"size": "34", "stock_physical": 3, "stock_virtual": 2},
            {"size": "36", "stock_physical": 1, "stock_virtual": 1},
        ]
    },
    {
        "sku": "PANTALON-NEGRO",
        "name": "Pantalón Negro",
        "description": "Pantalón de vestir color negro",
        "base_price": 75.00,
        "category": "Pantalones",
        "color": "Negro",
        "image_url": "https://via.placeholder.com/300x300/000000/FFFFFF?text=Pantalon+Negro",
        "variants": [
            {"size": "28", "stock_physical": 1, "stock_virtual": 1},
            {"size": "30", "stock_physical": 2, "stock_virtual": 1},
            {"size": "32", "stock_physical": 2, "stock_virtual": 2},
            {"size": "34", "stock_physical": 3, "stock_virtual": 2},
            {"size": "36", "stock_physical": 2, "stock_virtual": 1},
        ]
    },
    {
        "sku": "PANTALON-BEIGE",
        "name": "Pantalón Beige",
        "description": "Pantalón casual color beige",
        "base_price": 70.00,
        "category": "Pantalones",
        "color": "Beige",
        "image_url": "https://via.placeholder.com/300x300/F5F5DC/000000?text=Pantalon+Beige",
        "variants": [
            {"size": "28", "stock_physical": 2, "stock_virtual": 2},
            {"size": "30", "stock_physical": 4, "stock_virtual": 3},
            {"size": "32", "stock_physical": 4, "stock_virtual": 3},
            {"size": "34", "stock_physical": 3, "stock_virtual": 2},
        ]
    },
    {
        "sku": "CAMISA-BLANCA",
        "name": "Camisa Blanca",
        "description": "Camisa de vestir color blanco",
        "base_price": 50.00,
        "category": "Camisas",
        "color": "Blanco",
        "image_url": "https://via.placeholder.com/300x300/FFFFFF/000000?text=Camisa+Blanca",
        "variants": [
            {"size": "S", "stock_physical": 3, "stock_virtual": 2},
            {"size": "M", "stock_physical": 5, "stock_virtual": 3},
            {"size": "L", "stock_physical": 5, "stock_virtual": 3},
            {"size": "XL", "stock_physical": 3, "stock_virtual": 2},
            {"size": "2XL", "stock_physical": 1, "stock_virtual": 0},
        ]
    },
    {
        "sku": "CAMISA-CELESTE",
        "name": "Camisa Celeste",
        "description": "Camisa de vestir color celeste",
        "base_price": 48.00,
        "category": "Camisas",
        "color": "Celeste",
        "image_url": "https://via.placeholder.com/300x300/87CEEB/000000?text=Camisa+Celeste",
        "variants": [
            {"size": "S", "stock_physical": 2, "stock_virtual": 2},
            {"size": "M", "stock_physical": 4, "stock_virtual": 2},
            {"size": "L", "stock_physical": 4, "stock_virtual": 3},
            {"size": "XL", "stock_physical": 2, "stock_virtual": 2},
        ]
    },
    {
        "sku": "GORRA-NEGRA",
        "name": "Gorra Negra",
        "description": "Gorra deportiva color negro",
        "base_price": 30.00,
        "category": "Accesorios",
        "color": "Negro",
        "image_url": "https://via.placeholder.com/300x300/000000/FFFFFF?text=Gorra+Negra",
        "variants": [
            {"size": "UNICA", "stock_physical": 26, "stock_virtual": 17},
        ]
    },
    {
        "sku": "CORREA-MARRON",
        "name": "Correa Marrón 95cm",
        "description": "Correa de cuero marrón 95cm",
        "base_price": 35.00,
        "category": "Accesorios",
        "color": "Marrón",
        "image_url": "https://via.placeholder.com/300x300/8B4513/FFFFFF?text=Correa+Marron",
        "variants": [
            {"size": "95", "stock_physical": 20, "stock_virtual": 14},
        ]
    },
]


def recreate_database():
    """Recrear la base de datos con el nuevo esquema"""
    
    logger.info("=" * 60)
    logger.info("RECREANDO BASE DE DATOS CON ESQUEMA DE VARIANTES")
    logger.info("=" * 60)
    
    try:
        # Eliminar todas las tablas existentes
        logger.info("\n1. Eliminando tablas existentes...")
        Base.metadata.drop_all(engine)
        logger.info("✅ Tablas eliminadas")
        
        # Crear todas las tablas con el nuevo esquema
        logger.info("\n2. Creando tablas con nuevo esquema...")
        Base.metadata.create_all(engine)
        logger.info("✅ Tablas creadas:")
        logger.info("   - products (productos padre)")
        logger.info("   - product_variants (variantes por talla)")
        logger.info("   - transactions (transacciones)")
        logger.info("   - chat_sessions")
        logger.info("   - agent_logs")
        logger.info("   - sync_history")
        
        # Poblar con productos y variantes
        logger.info("\n3. Poblando productos y variantes...")
        
        with get_db() as db:
            for product_data in PRODUCTS_WITH_VARIANTS:
                # Crear producto padre
                product = Product(
                    sku=product_data["sku"],
                    name=product_data["name"],
                    description=product_data["description"],
                    base_price=product_data["base_price"],
                    category=product_data["category"],
                    color=product_data["color"],
                    image_url=product_data["image_url"]
                )
                db.add(product)
                db.flush()  # Para obtener el ID
                
                logger.info(f"\n   📦 {product.name} ({product.sku})")
                logger.info(f"      Precio base: S/ {product.base_price:.2f}")
                
                # Crear variantes
                total_stock = 0
                for variant_data in product_data["variants"]:
                    stock_total = variant_data["stock_physical"] + variant_data["stock_virtual"]
                    total_stock += stock_total
                    
                    variant = ProductVariant(
                        product_id=product.id,
                        sku=f"{product.sku}-{variant_data['size']}",
                        size=variant_data["size"],
                        stock_physical=variant_data["stock_physical"],
                        stock_virtual=variant_data["stock_virtual"],
                        stock_total=stock_total,
                        price_adjustment=0.0
                    )
                    db.add(variant)
                    
                    logger.info(f"      - Talla {variant.size}: {stock_total} unidades ({variant.sku})")
                
                logger.info(f"      Total: {total_stock} unidades")
            
            db.commit()
            
            # Mostrar resumen final
            total_products = db.query(Product).count()
            total_variants = db.query(ProductVariant).count()
            
            logger.info("\n" + "=" * 60)
            logger.info("✅ BASE DE DATOS RECREADA EXITOSAMENTE")
            logger.info("=" * 60)
            logger.info(f"\n📊 RESUMEN:")
            logger.info(f"   Productos padre: {total_products}")
            logger.info(f"   Variantes totales: {total_variants}")
            logger.info(f"   Promedio variantes por producto: {total_variants / total_products:.1f}")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error(f"\n❌ ERROR AL RECREAR BASE DE DATOS: {e}")
        raise


if __name__ == "__main__":
    logger.info("🚀 Iniciando recreación de base de datos...")
    
    response = input("\n⚠️  ADVERTENCIA: Esto eliminará TODOS los datos existentes. ¿Continuar? (s/n): ")
    
    if response.lower() == 's':
        recreate_database()
        logger.info("\n✅ Proceso completado exitosamente!")
        logger.info("\n💡 Ahora puedes iniciar el servidor con: python main.py")
    else:
        logger.info("\n❌ Operación cancelada por el usuario")
