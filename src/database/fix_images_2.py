"""
Script para copiar las NUEVAS imágenes y actualizar base de datos
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

# Configuración
ARTIFACTS_DIR = r"C:/Users/adria/.gemini/antigravity/brain/fd834f8e-b673-4c76-af55-9ffe54c1256f"
DEST_DIR = r"C:\Prototipo Tesis 1\frontend\images"
PUBLIC_URL_PREFIX = "/static/images/"

# Mapeo: SKU -> (Archivo Origen, Nuevo Nombre de Archivo)
# Solo incluimos los NUEVOS archivos generados o los que faltaban
PRODUCT_IMAGES_CONFIG = {
    # Nuevos generados
    "JEAN-AZUL": (f"{ARTIFACTS_DIR}/jean_azul_producto_1765352078268.png", "jean_azul.png"),
    "PANTALON-NEGRO": (f"{ARTIFACTS_DIR}/pantalon_negro_producto_1765352091468.png", "pantalon_negro.png"),
    "PANTALON-BEIGE": (f"{ARTIFACTS_DIR}/pantalon_beige_producto_1765352116992.png", "pantalon_beige.png"),
    
    # Fallaron / Pendientes (Seguir con Placeholder)
    # No es necesario actualizarlos si ya tienen placeholder, pero lo confirmamos
    "POLO-AZUL": (None, "https://via.placeholder.com/400x500/4169E1/FFFFFF?text=Polo+Azul"),
    "CAMISA-BLANCA": (None, "https://via.placeholder.com/400x500/FFFFFF/000000?text=Camisa+Blanca"),
    "CAMISA-CELESTE": (None, "https://via.placeholder.com/400x500/87CEEB/000000?text=Camisa+Celeste"),
    "GORRA-NEGRA": (None, "https://via.placeholder.com/400x400/000000/FFFFFF?text=Gorra+Negra"),
}

def fix_images_and_db_phase2():
    logger.info("🔧 INICIANDO FASE 2 DE IMÁGENES")
    
    # Asegurar que directorio destino existe
    os.makedirs(DEST_DIR, exist_ok=True)
    
    with get_db() as db:
        for sku, config in PRODUCT_IMAGES_CONFIG.items():
            source_path, filename_or_url = config
            
            final_url = ""
            
            if source_path:
                # Es una imagen local que hay que copiar
                dest_path = os.path.join(DEST_DIR, filename_or_url)
                try:
                    shutil.copy2(source_path, dest_path)
                    logger.info(f"✅ Copiado: {filename_or_url}")
                    final_url = f"{PUBLIC_URL_PREFIX}{filename_or_url}"
                except FileNotFoundError:
                    logger.warning(f"⚠️  No se encontró archivo fuente: {source_path}")
                    continue
            else:
                # Es una URL externa
                final_url = filename_or_url
            
            # Actualizar base de datos
            product = db.query(Product).filter(Product.sku == sku).first()
            if product:
                product.image_url = final_url
                logger.info(f"🔄 DB Actualizada: {sku} -> {final_url}")
            else:
                logger.warning(f"⚠️  Producto no encontrado en DB: {sku}")
                
        db.commit()
        logger.info("💾 Base de datos guardada")

if __name__ == "__main__":
    fix_images_and_db_phase2()
