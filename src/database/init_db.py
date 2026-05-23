"""
Script de inicialización de base de datos
Crea las tablas y datos de ejemplo
"""
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.models import Base, Product, Transaction, TransactionType
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
    """Inserta datos de ejemplo"""
    logger.info("Insertando datos de ejemplo...")
    
    sample_products = [
        {
            "sku": "POLO-R-M",
            "name": "Polo Rojo",
            "description": "Polo de algodón color rojo",
            "price": 25.00,
            "stock_physical": 15,
            "stock_virtual": 10,
            "stock_total": 25,
            "category": "Polos",
            "size": "M",
            "color": "Rojo"
        },
        {
            "sku": "JEAN-A-32",
            "name": "Jean Azul",
            "description": "Jean clásico azul",
            "price": 80.00,
            "stock_physical": 8,
            "stock_virtual": 5,
            "stock_total": 13,
            "category": "Pantalones",
            "size": "32",
            "color": "Azul"
        },
        {
            "sku": "CAM-B-L",
            "name": "Camisa Blanca",
            "description": "Camisa formal blanca",
            "price": 45.00,
            "stock_physical": 12,
            "stock_virtual": 8,
            "stock_total": 20,
            "category": "Camisas",
            "size": "L",
            "color": "Blanco"
        },
        {
            "sku": "POLO-N-S",
            "name": "Polo Negro",
            "description": "Polo básico negro",
            "price": 22.00,
            "stock_physical": 20,
            "stock_virtual": 15,
            "stock_total": 35,
            "category": "Polos",
            "size": "S",
            "color": "Negro"
        },
        {
            "sku": "SHORT-G-M",
            "name": "Short Gris",
            "description": "Short deportivo gris",
            "price": 35.00,
            "stock_physical": 10,
            "stock_virtual": 5,
            "stock_total": 15,
            "category": "Shorts",
            "size": "M",
            "color": "Gris"
        }
    ]
    
    try:
        with get_db() as db:
            # Verificar si ya hay productos
            existing_count = db.query(Product).count()
            if existing_count > 0:
                logger.warning(f"⚠️  Ya existen {existing_count} productos en la base de datos")
                response = input("¿Deseas eliminar los datos existentes? (s/n): ")
                if response.lower() == 's':
                    db.query(Transaction).delete()
                    db.query(Product).delete()
                    db.commit()
                    logger.info("Datos existentes eliminados")
                else:
                    logger.info("Manteniendo datos existentes")
                    return
            
            # Insertar productos
            for product_data in sample_products:
                product = Product(**product_data)
                db.add(product)
            
            db.commit()
            logger.info(f"✅ {len(sample_products)} productos de ejemplo insertados")
            
    except Exception as e:
        logger.error(f"❌ Error al insertar datos de ejemplo: {e}")
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
