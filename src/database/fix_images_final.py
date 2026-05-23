"""
Script final para actualizar imágenes de productos con URLs de Unsplash de alta calidad
"""
import sys
import os
import shutil
from pathlib import Path

# Agregar directorio raíz al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database.connection import get_db
from src.database.models import Product
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# URLs de Unsplash para productos faltantes
# Estas son imágenes reales de stock que se ven profesionales
UNSPLASH_IMAGES = {
    # Polo Azul -> Polo navy en fondo claro
    "POLO-AZUL": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80",
    
    # Camisa Blanca -> Camisa blanca colgada o doblada
    "CAMISA-BLANCA": "https://images.unsplash.com/photo-1620799140408-ed5341cd2431?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80",
    
    # Camisa Celeste -> Camisa azul claro
    "CAMISA-CELESTE": "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80",
    
    # Gorra Negra -> Gorra negra simple
    "GORRA-NEGRA": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80",
}

def update_remaining_images():
    logger.info("🔧 ACTUALIZANDO IMÁGENES RESTANTES CON STOCK PHOTOS")
    
    with get_db() as db:
        for sku, url in UNSPLASH_IMAGES.items():
            product = db.query(Product).filter(Product.sku == sku).first()
            if product:
                # Solo actualizar si no tiene ya una imagen local (empezando con /static/)
                # O si queremos forzar el reemplazo de los placeholders anteriores
                if "via.placeholder" in product.image_url or not product.image_url:
                    product.image_url = url
                    logger.info(f"✅ {sku} -> URL Stock actualizada")
                else:
                    logger.info(f"ℹ️ {sku} ya tiene imagen personalizada. Omitiendo.")
            else:
                logger.warning(f"⚠️ Producto no encontrado: {sku}")
                
        db.commit()
        logger.info("💾 Base de datos guardada con nuevas imágenes")

if __name__ == "__main__":
    update_remaining_images()
