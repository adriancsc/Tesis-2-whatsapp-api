"""
Script de prueba para verificar el sistema MAS-CIS
Ejecuta pruebas básicas de los componentes principales
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import asyncio
from src.agents.nlu_processor import nlu_processor
from src.agents import store_agent, coordinator_agent
from src.utils.logger import setup_logger

logger = setup_logger("test_system")


def test_nlu_processor():
    """Prueba el procesador NLU"""
    logger.info("=" * 60)
    logger.info("🧪 Probando NLU Processor")
    logger.info("=" * 60)
    
    test_cases = [
        "Vendí 3 polos rojos talla M",
        "Agregar 10 jeans azules",
        "Actualizar stock de POLO-R-M a 15",
        "Eliminar 2 camisas dañadas",
        "¿Cuánto stock hay de JEAN-A-32?",
        "Resumen del día"
    ]
    
    for text in test_cases:
        parsed = nlu_processor.parse(text)
        logger.info(f"\n📝 Texto: {text}")
        logger.info(f"   Acción: {parsed.action}")
        logger.info(f"   Cantidad: {parsed.quantity}")
        logger.info(f"   Producto: {parsed.product_name or parsed.product_sku or 'N/A'}")
        logger.info(f"   Atributos: {parsed.attributes}")
        logger.info(f"   Confianza: {parsed.confidence:.2f}")
        logger.info(f"   Válido: {nlu_processor.is_valid_command(parsed)}")
    
    logger.info("\n✅ Prueba de NLU completada")


async def test_store_agent():
    """Prueba el Agente de Tienda"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 Probando Store Agent")
    logger.info("=" * 60)
    
    test_messages = [
        {
            "from": "51999999999",
            "text": "Vendí 2 polos rojos talla M",
            "timestamp": "2025-01-26T18:00:00Z"
        },
        {
            "from": "51999999999",
            "text": "¿Cuánto stock hay de POLO-R-M?",
            "timestamp": "2025-01-26T18:01:00Z"
        }
    ]
    
    for msg in test_messages:
        logger.info(f"\n📨 Mensaje: {msg['text']}")
        response = await store_agent.process_message(msg)
        logger.info(f"📤 Respuesta: {response.get('text', 'N/A')[:100]}...")
    
    logger.info("\n✅ Prueba de Store Agent completada")


async def test_coordinator_agent():
    """Prueba el Agente Coordinador"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 Probando Coordinator Agent")
    logger.info("=" * 60)
    
    # Nota: Esta prueba requiere base de datos configurada
    logger.info("\n⚠️  Esta prueba requiere base de datos configurada")
    logger.info("   Si la base de datos no está lista, esta prueba fallará")
    
    test_request = {
        "action": "sell",
        "product_sku": "POLO-R-M",
        "quantity": 1,
        "vendor_phone": "51999999999",
        "timestamp": "2025-01-26T18:00:00Z"
    }
    
    try:
        logger.info(f"\n🔄 Procesando: {test_request}")
        result = await coordinator_agent.process_message(test_request)
        
        if result.get("success"):
            logger.info("✅ Operación exitosa")
            logger.info(f"   Producto: {result.get('product', {}).get('name')}")
            logger.info(f"   Stock anterior: {result.get('product', {}).get('previous_stock')}")
            logger.info(f"   Stock nuevo: {result.get('product', {}).get('new_stock')}")
        else:
            logger.warning(f"⚠️  Operación falló: {result.get('error')}")
    
    except Exception as e:
        logger.error(f"❌ Error en prueba: {e}")
        logger.info("   Asegúrate de que la base de datos esté configurada")
    
    logger.info("\n✅ Prueba de Coordinator Agent completada")


def test_agent_info():
    """Prueba información de agentes"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 Probando Información de Agentes")
    logger.info("=" * 60)
    
    store_info = store_agent.get_info()
    coord_info = coordinator_agent.get_info()
    
    logger.info("\n🏪 Store Agent:")
    logger.info(f"   ID: {store_info['agent_id']}")
    logger.info(f"   Tipo: {store_info['agent_type']}")
    logger.info(f"   Estado: {store_info['status']}")
    
    logger.info("\n🔄 Coordinator Agent:")
    logger.info(f"   ID: {coord_info['agent_id']}")
    logger.info(f"   Tipo: {coord_info['agent_type']}")
    logger.info(f"   Estado: {coord_info['status']}")
    
    logger.info("\n✅ Prueba de información completada")


async def main():
    """Función principal de pruebas"""
    logger.info("\n" + "=" * 60)
    logger.info("🚀 INICIANDO PRUEBAS DEL SISTEMA MAS-CIS")
    logger.info("=" * 60)
    
    try:
        # Prueba 1: NLU Processor
        test_nlu_processor()
        
        # Prueba 2: Store Agent
        await test_store_agent()
        
        # Prueba 3: Coordinator Agent
        await test_coordinator_agent()
        
        # Prueba 4: Agent Info
        test_agent_info()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ TODAS LAS PRUEBAS COMPLETADAS")
        logger.info("=" * 60)
        logger.info("\n📝 Notas:")
        logger.info("   - Si alguna prueba falló, verifica la configuración")
        logger.info("   - Las pruebas de base de datos requieren SQL Server configurado")
        logger.info("   - Revisa los logs para más detalles")
        
    except Exception as e:
        logger.error(f"\n❌ Error en las pruebas: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
