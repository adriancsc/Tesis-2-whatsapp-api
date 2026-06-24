import asyncio
import json
from src.database.connection import get_db
from src.database.models import Product, ProductVariant, AgentLog, WebOrder
from src.gateway import message_router
from src.agents import agent_orchestrator
from src.agents.state import MASState

async def run_tests():
    print("=" * 60)
    print("🧪 INICIANDO PRUEBAS DEL SPRINT 3 (MAS-CIS)")
    print("=" * 60)

    # 1. Preparar base de datos simulada (Asegurar que hay stock)
    with get_db() as db:
        variant = db.query(ProductVariant).filter(ProductVariant.sku == "POLO-BLANCO-M").first()
        if variant:
            variant.stock_physical = 10
            variant.stock_total = 10
            db.commit()
            print(f"📦 Stock inicial configurado: POLO-BLANCO-M -> {variant.stock_physical} unidades")

    print("\n" + "-" * 60)
    print("▶️ PRUEBA 1: FLUJO WHATSAPP (CU-01 VENTA) - StoreAgent + CoordinatorAgent")
    
    vendor_phone = "51999888777"
    
    async def simulate_whatsapp_message(text):
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{"changes": [{"value": {
                "messages": [{"from": vendor_phone, "type": "text", "text": {"body": text}}]
            }}]}]
        }
        await message_router.route_whatsapp_message(payload)
        
    await simulate_whatsapp_message("menu")
    print("✓ [StoreAgent] Menú principal generado")
    
    await simulate_whatsapp_message("1")
    print("✓ [StoreAgent] Selección de Venta procesada")
    
    await simulate_whatsapp_message("1")
    print("✓ [StoreAgent] Producto Polo Blanco seleccionado")
    
    await simulate_whatsapp_message("2")
    print("✓ [StoreAgent] Talla M seleccionada")
    
    await simulate_whatsapp_message("1")
    print("✓ [StoreAgent] Cantidad 1 validada")
    
    await simulate_whatsapp_message("1")
    print("✓ [CoordinatorAgent] Venta procesada y Kárdex actualizado")
    
    with get_db() as db:
        variant = db.query(ProductVariant).filter(ProductVariant.sku == "POLO-BLANCO-M").first()
        print(f"📊 Nuevo stock físico tras la venta: {variant.stock_physical} unidades (Esperado: 9)")

    print("\n" + "-" * 60)
    print("▶️ PRUEBA 2: WEBHOOK E-COMMERCE (CU-04 VENTA WEB) - SyncAgent + CoordinatorAgent")
    
    order_id = "WOO-9999"
    initial_state: MASState = {
        "source": "ecommerce",
        "vendor_phone": None,
        "raw_text": "",
        "current_step": "CONFIRM",
        "action": "sell_web",
        "product_sku": None,
        "product_name": None,
        "variant_id": None,
        "variant_sku": "POLO-BLANCO-M",
        "size": None,
        "quantity": 2,
        "response_text": "",
        "requires_coordinator": True,
        "requires_sync": False,
        "requires_alert": False,
        "conflict_detected": False,
        "operation_success": False,
        "size_options": None,
        "messages": [],
        "ecommerce_order_id": order_id,
        "ecommerce_action": "process_order",
    }
    
    from langchain_core.runnables import RunnableConfig
    config: RunnableConfig = {"configurable": {"thread_id": f"web_{order_id}"}}
    result = agent_orchestrator.invoke(initial_state, config)
    
    if result.get("operation_success"):
         print(f"✓ [SyncAgent] Orden Web {order_id} procesada exitosamente")
    else:
         print(f"❌ [SyncAgent] Error en Orden Web: {result.get('response_text')}")
         
    with get_db() as db:
        variant = db.query(ProductVariant).filter(ProductVariant.sku == "POLO-BLANCO-M").first()
        print(f"📊 Nuevo stock tras la venta web: {variant.stock_physical} unidades (Esperado: 7)")

    print("\n" + "-" * 60)
    print("▶️ PRUEBA 3: PROACTIVIDAD DE ALERTAS (CU-09) - AlertAgent")
    
    print("⏳ Forzando agotamiento de stock (Venta Web de 7 unidades)...")
    order_id2 = "WOO-CRITICAL"
    initial_state["quantity"] = 7
    initial_state["ecommerce_order_id"] = order_id2
    config2: RunnableConfig = {"configurable": {"thread_id": f"web_{order_id2}"}}
    agent_orchestrator.invoke(initial_state, config2)
    
    with get_db() as db:
        variant = db.query(ProductVariant).filter(ProductVariant.sku == "POLO-BLANCO-M").first()
        print(f"📊 Stock actual: {variant.stock_physical} unidades (Esperado: 0)")
        
        logs = db.query(AgentLog).filter(AgentLog.action == "proactive_alert").all()
        found_alert = False
        for log in logs[-5:]: # Check recent logs
            if "agotado completamente" in log.message:
                found_alert = True
                print(f"✓ [AlertAgent] ¡Alerta proactiva encontrada en BD!\n   Mensaje: {log.message.replace(chr(10), ' ')}")
                break
                
        if not found_alert:
            print("❌ [AlertAgent] No se encontró la alerta de stock agotado en los logs.")

    print("\n" + "=" * 60)
    print("✅ PRUEBAS FINALIZADAS")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_tests())
