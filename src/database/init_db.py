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
                "sku": "POLO-R",
                "name": "Polo Rojo",
                "description": "Polo de algodón color rojo",
                "base_price": 25.00,
                "category": "Polos",
                "color": "Rojo"
            },
            "variants": [
                {
                    "sku": "POLO-R-M",
                    "size": "M",
                    "stock_physical": 15,
                    "stock_virtual": 10,
                    "stock_total": 25
                },
                {
                    "sku": "POLO-R-L",
                    "size": "L",
                    "stock_physical": 5,
                    "stock_virtual": 0,
                    "stock_total": 5
                }
            ]
        },
        {
            "product": {
                "sku": "JEAN-A",
                "name": "Jean Azul",
                "description": "Jean clásico azul",
                "base_price": 80.00,
                "category": "Pantalones",
                "color": "Azul"
            },
            "variants": [
                {
                    "sku": "JEAN-A-32",
                    "size": "32",
                    "stock_physical": 8,
                    "stock_virtual": 5,
                    "stock_total": 13
                }
            ]
        },
        {
            "product": {
                "sku": "CAM-B",
                "name": "Camisa Blanca",
                "description": "Camisa formal blanca",
                "base_price": 45.00,
                "category": "Camisas",
                "color": "Blanco"
            },
            "variants": [
                {
                    "sku": "CAM-B-L",
                    "size": "L",
                    "stock_physical": 12,
                    "stock_virtual": 8,
                    "stock_total": 20
                }
            ]
        }
    ]
    
    try:
        with get_db() as db:
            existing_count = db.query(Product).count()
            if existing_count > 0:
                logger.warning(f"⚠️  Ya existen {existing_count} productos en la base de datos")
                response = input("¿Deseas eliminar los datos existentes? (s/n): ")
                if response.lower() == 's':
                    db.query(Transaction).delete()
                    db.query(ProductVariant).delete()
                    db.query(Product).delete()
                    db.commit()
                    logger.info("Datos existentes eliminados")
                else:
                    logger.info("Manteniendo datos existentes")
                    return
            
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
