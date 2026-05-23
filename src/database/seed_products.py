"""
Script para poblar la base de datos con los 10 productos del sistema MAS-CIS
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.models import Product
from src.database.connection import get_db
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def seed_products():
    """Inserta los 10 productos principales del sistema"""
    
    products = [
        {
            "sku": "POLO-BLANCO-M",
            "name": "Polo Blanco M",
            "description": "Polo básico de algodón color blanco, talla M",
            "price": 25.00,
            "stock_physical": 20,
            "stock_virtual": 15,
            "stock_total": 35,
            "category": "Polos",
            "size": "M",
            "color": "Blanco",
            "image_url": "/static/images/polo-blanco.jpg"
        },
        {
            "sku": "POLO-NEGRO-L",
            "name": "Polo Negro L",
            "description": "Polo básico de algodón color negro, talla L",
            "price": 25.00,
            "stock_physical": 18,
            "stock_virtual": 12,
            "stock_total": 30,
            "category": "Polos",
            "size": "L",
            "color": "Negro",
            "image_url": "/static/images/polo-negro.jpg"
        },
        {
            "sku": "POLO-AZUL-S",
            "name": "Polo Azul S",
            "description": "Polo básico de algodón color azul, talla S",
            "price": 25.00,
            "stock_physical": 15,
            "stock_virtual": 10,
            "stock_total": 25,
            "category": "Polos",
            "size": "S",
            "color": "Azul",
            "image_url": "/static/images/polo-azul.jpg"
        },
        {
            "sku": "JEAN-AZUL-32",
            "name": "Jean Azul 32",
            "description": "Jean clásico azul, talla 32",
            "price": 85.00,
            "stock_physical": 12,
            "stock_virtual": 8,
            "stock_total": 20,
            "category": "Pantalones",
            "size": "32",
            "color": "Azul",
            "image_url": "/static/images/jean-azul.jpg"
        },
        {
            "sku": "PANTALON-NEGRO-34",
            "name": "Pantalón Negro 34",
            "description": "Pantalón de vestir negro, talla 34",
            "price": 75.00,
            "stock_physical": 10,
            "stock_virtual": 7,
            "stock_total": 17,
            "category": "Pantalones",
            "size": "34",
            "color": "Negro",
            "image_url": "/static/images/pantalon-negro.jpg"
        },
        {
            "sku": "PANTALON-BEIGE-30",
            "name": "Pantalón Beige 30",
            "description": "Pantalón casual beige, talla 30",
            "price": 70.00,
            "stock_physical": 14,
            "stock_virtual": 9,
            "stock_total": 23,
            "category": "Pantalones",
            "size": "30",
            "color": "Beige",
            "image_url": "/static/images/pantalon-beige.jpg"
        },
        {
            "sku": "CAMISA-BLANCA-M",
            "name": "Camisa Blanca M",
            "description": "Camisa formal blanca, talla M",
            "price": 50.00,
            "stock_physical": 16,
            "stock_virtual": 11,
            "stock_total": 27,
            "category": "Camisas",
            "size": "M",
            "color": "Blanco",
            "image_url": "/static/images/camisa-blanca.jpg"
        },
        {
            "sku": "CAMISA-CELESTE-L",
            "name": "Camisa Celeste L",
            "description": "Camisa casual celeste, talla L",
            "price": 48.00,
            "stock_physical": 13,
            "stock_virtual": 8,
            "stock_total": 21,
            "category": "Camisas",
            "size": "L",
            "color": "Celeste",
            "image_url": "/static/images/camisa-celeste.jpg"
        },
        {
            "sku": "GORRA-NEGRA",
            "name": "Gorra Negra",
            "description": "Gorra deportiva color negro",
            "price": 30.00,
            "stock_physical": 25,
            "stock_virtual": 18,
            "stock_total": 43,
            "category": "Accesorios",
            "size": "Única",
            "color": "Negro",
            "image_url": "/static/images/gorra-negra.jpg"
        },
        {
            "sku": "CORREA-MARRON-95",
            "name": "Correa Marrón 95cm",
            "description": "Correa de cuero marrón, 95cm",
            "price": 35.00,
            "stock_physical": 20,
            "stock_virtual": 14,
            "stock_total": 34,
            "category": "Accesorios",
            "size": "95cm",
            "color": "Marrón",
            "image_url": "/static/images/correa-marron.jpg"
        }
    ]
    
    try:
        with get_db() as db:
            # Verificar si ya existen productos
            existing_count = db.query(Product).count()
            
            if existing_count > 0:
                logger.info(f"⚠️  Ya existen {existing_count} productos en la base de datos")
                logger.info("Agregando nuevos productos sin eliminar los existentes...")
            
            # Insertar productos (solo si no existen por SKU)
            added_count = 0
            updated_count = 0
            
            for product_data in products:
                existing_product = db.query(Product).filter(
                    Product.sku == product_data["sku"]
                ).first()
                
                if existing_product:
                    logger.info(f"Producto {product_data['sku']} ya existe, actualizando...")
                    for key, value in product_data.items():
                        setattr(existing_product, key, value)
                    updated_count += 1
                else:
                    product = Product(**product_data)
                    db.add(product)
                    added_count += 1
                    logger.info(f"✅ Agregado: {product_data['name']} ({product_data['sku']})")
            
            db.commit()
            
            logger.info("=" * 60)
            logger.info(f"✅ Productos agregados: {added_count}")
            logger.info(f"🔄 Productos actualizados: {updated_count}")
            logger.info(f"📊 Total de productos en BD: {db.query(Product).count()}")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error(f"❌ Error al insertar productos: {e}")
        raise


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("Poblando Base de Datos - Sistema MAS-CIS")
    logger.info("=" * 60)
    
    try:
        seed_products()
        logger.info("✅ Proceso completado exitosamente")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        sys.exit(1)
