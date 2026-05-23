"""
Script para corregir la imagen de Camisa Blanca
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

# Nueva URL para Camisa Blanca (probando una fuente más estable: Pexels o diferente Unsplash)
NEW_URL = "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?ixlib=rb-4.0.3&auto=format&fit=crop&w=500&q=80"

def fix_white_shirt_image():
    logger.info("🔧 CORRIGIENDO IMAGEN CAMISA BLANCA")
    
    with get_db() as db:
        sku = "CAMISA-BLANCA"
        product = db.query(Product).filter(Product.sku == sku).first()
        if product:
            product.image_url = NEW_URL
            logger.info(f"✅ {sku} -> Nueva URL actualizada: {NEW_URL}")
        else:
            logger.warning(f"⚠️ Producto no encontrado: {sku}")
                
        db.commit()
        logger.info("💾 Base de datos guardada")

if __name__ == "__main__":
    fix_white_shirt_image()
