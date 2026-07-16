"""
Script de inicialización de base de datos
Crea las tablas y datos de ejemplo
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.models import Base, Product, ProductVariant, Transaction, TransactionType
from src.database.connection import engine, get_db
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_tables():
    """Crea todas las tablas en la base de datos"""
    try:
        logger.info("Creando tablas en la base de datos...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tablas creadas exitosamente")
    except Exception as e:
        logger.error(f"❌ Error al crear tablas: {e}")
        raise


def seed_sample_data():
    """Inserta datos de ejemplo adaptados al nuevo esquema con Variantes"""
    logger.info("Insertando datos de ejemplo...")
    
    sample_data = [
        {
            "product": {
                "sku": "POLO-BLANCO",
                "name": "Polo Blanco",
                "description": "Polo de algodón pima color blanco",
                "base_price": 35.00,
                "category": "Polos",
                "color": "Blanco",
                "image_url": "/images/polo-blanco.png"
            },
            "variants": [
                {"sku": "POLO-BLANCO-S", "size": "S", "stock_physical": 10, "stock_virtual": 0, "stock_total": 10},
                {"sku": "POLO-BLANCO-M", "size": "M", "stock_physical": 15, "stock_virtual": 0, "stock_total": 15},
                {"sku": "POLO-BLANCO-L", "size": "L", "stock_physical": 12, "stock_virtual": 0, "stock_total": 12},
                {"sku": "POLO-BLANCO-XL", "size": "XL", "stock_physical": 8, "stock_virtual": 0, "stock_total": 8},
            ]
        },
        {
            "product": {
                "sku": "POLO-NEGRO",
                "name": "Polo Negro",
                "description": "Polo de algodón pima color negro",
                "base_price": 35.00,
                "category": "Polos",
                "color": "Negro",
                "image_url": "/images/polo-negro.png"
            },
            "variants": [
                {"sku": "POLO-NEGRO-S", "size": "S", "stock_physical": 8, "stock_virtual": 0, "stock_total": 8},
                {"sku": "POLO-NEGRO-M", "size": "M", "stock_physical": 12, "stock_virtual": 0, "stock_total": 12},
                {"sku": "POLO-NEGRO-L", "size": "L", "stock_physical": 10, "stock_virtual": 0, "stock_total": 10},
                {"sku": "POLO-NEGRO-XL", "size": "XL", "stock_physical": 6, "stock_virtual": 0, "stock_total": 6},
            ]
        },
        {
            "product": {
                "sku": "POLO-AZUL",
                "name": "Polo Azul",
                "description": "Polo de algodón pima color azul marino",
                "base_price": 35.00,
                "category": "Polos",
                "color": "Azul",
                "image_url": "/images/polo-azul.png"
            },
            "variants": [
                {"sku": "POLO-AZUL-S", "size": "S", "stock_physical": 7, "stock_virtual": 0, "stock_total": 7},
                {"sku": "POLO-AZUL-M", "size": "M", "stock_physical": 14, "stock_virtual": 0, "stock_total": 14},
                {"sku": "POLO-AZUL-L", "size": "L", "stock_physical": 9, "stock_virtual": 0, "stock_total": 9},
                {"sku": "POLO-AZUL-XL", "size": "XL", "stock_physical": 5, "stock_virtual": 0, "stock_total": 5},
            ]
        }
    ]
    
    try:
        with get_db() as db:
            existing_count = db.query(Product).count()
            if existing_count > 0:
                logger.warning(f"⚠️  Ya existen {existing_count} productos. Limpiando...")
                db.query(Transaction).delete()
                db.query(ProductVariant).delete()
                db.query(Product).delete()
                db.commit()
                logger.info("Datos existentes eliminados")
            
            for item in sample_data:
                product = Product(**item["product"])
                db.add(product)
                db.flush() # Para obtener el ID del producto
                
                for var_data in item["variants"]:
                    variant = ProductVariant(product_id=product.id, **var_data)
                    db.add(variant)
            
            db.commit()
            logger.info(f"✅ {len(sample_data)} productos con sus variantes insertados")
            
    except Exception as e:
        logger.error(f"❌ Error al insertar datos de ejemplo: {e}")
        db.rollback()
        raise


def main():
    """Función principal"""
    logger.info("=" * 60)
    logger.info("Inicialización de Base de Datos - Sistema MAS-CIS")
    logger.info("=" * 60)
    
    try:
        # Crear tablas
        create_tables()
        
        # Insertar datos de ejemplo
        seed_sample_data()
        
        logger.info("=" * 60)
        logger.info("✅ Inicialización completada exitosamente")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error en la inicialización: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
