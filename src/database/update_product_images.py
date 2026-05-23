"""
Script para actualizar las URLs de imágenes de los productos
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.connection import get_db
from src.database.models import Product
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mapeo de productos a sus imágenes
PRODUCT_IMAGES = {
    "POLO-BLANCO": "C:/Users/adria/.gemini/antigravity/brain/fd834f8e-b673-4c76-af55-9ffe54c1256f/polo_blanco_producto_1765351760190.png",
    "POLO-NEGRO": "C:/Users/adria/.gemini/antigravity/brain/fd834f8e-b673-4c76-af55-9ffe54c1256f/polo_negro_producto_1765351774881.png",
    "POLO-AZUL": "https://via.placeholder.com/400x500/4169E1/FFFFFF?text=Polo+Azul",
    "JEAN-AZUL": "https://via.placeholder.com/400x500/1E3A8A/FFFFFF?text=Jean+Azul",
    "PANTALON-NEGRO": "https://via.placeholder.com/400x500/000000/FFFFFF?text=Pantalon+Negro",
    "PANTALON-BEIGE": "https://via.placeholder.com/400x500/F5F5DC/000000?text=Pantalon+Beige",
    "CAMISA-BLANCA": "https://via.placeholder.com/400x500/FFFFFF/000000?text=Camisa+Blanca",
    "CAMISA-CELESTE": "https://via.placeholder.com/400x500/87CEEB/000000?text=Camisa+Celeste",
    "GORRA-NEGRA": "https://via.placeholder.com/400x400/000000/FFFFFF?text=Gorra+Negra",
    "CORREA-MARRON": "C:/Users/adria/.gemini/antigravity/brain/fd834f8e-b673-4c76-af55-9ffe54c1256f/correa_marron_producto_1765351791897.png",
}

def update_product_images():
    """Actualizar las URLs de imágenes de los productos"""
    
    logger.info("=" * 60)
    logger.info("ACTUALIZANDO IMÁGENES DE PRODUCTOS")
    logger.info("=" * 60)
    
    try:
        with get_db() as db:
            updated_count = 0
            
            for sku, image_url in PRODUCT_IMAGES.items():
                product = db.query(Product).filter(Product.sku == sku).first()
                
                if product:
                    product.image_url = image_url
                    updated_count += 1
                    logger.info(f"✅ {product.name} ({sku})")
                    logger.info(f"   Imagen: {image_url[:80]}...")
                else:
                    logger.warning(f"⚠️  Producto no encontrado: {sku}")
            
            db.commit()
            
            logger.info("\n" + "=" * 60)
            logger.info(f"✅ ACTUALIZACIÓN COMPLETADA")
            logger.info(f"   Productos actualizados: {updated_count}/{len(PRODUCT_IMAGES)}")
            logger.info("=" * 60)
            
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        raise

if __name__ == "__main__":
    update_product_images()
