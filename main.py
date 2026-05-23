"""
Punto de entrada principal del sistema MAS-CIS
"""
import sys
import uvicorn
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import settings
from src.utils.logger import system_logger


def main():
    """Función principal para iniciar el servidor"""
    system_logger.info("=" * 70)
    system_logger.info("🚀 Iniciando Sistema MAS-CIS")
    system_logger.info("   Sistema Multiagente de Sincronización de Inventario")
    system_logger.info("=" * 70)
    system_logger.info(f"📍 Host: {settings.APP_HOST}:{settings.APP_PORT}")
    system_logger.info(f"🔧 Modo Debug: {settings.DEBUG_MODE}")
    system_logger.info(f"📊 Base de Datos: {settings.DB_SERVER}/{settings.DB_NAME}")
    system_logger.info("=" * 70)
    
    try:
        uvicorn.run(
            "src.api.main:app",
            host=settings.APP_HOST,
            port=settings.APP_PORT,
            reload=settings.DEBUG_MODE,
            log_level=settings.LOG_LEVEL.lower()
        )
    except KeyboardInterrupt:
        system_logger.info("\n👋 Sistema detenido por el usuario")
    except Exception as e:
        system_logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
