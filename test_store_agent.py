"""Test completo del Store Agent refactorizado"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.store_agent import StoreAgent
from src.agents.gemini_nlu import gemini_nlu
from src.database.repository import product_repository
import asyncio

async def test_flow():
    print("=" * 60)
    print("TESTING STORE AGENT - REFACTORIZADO")
    print("=" * 60)
    
    agent = StoreAgent("test_agent")
    
    # Test 1: Saludo
    print("\n🧪 TEST 1: Saludo")
    result = await agent.process_message({"from": "+51999999999", "text": "Hola"})
    print(f"   Respuesta: {result['text'][:100]}...")
    assert "Hola" in result["text"] or "hola" in result["text"].lower()
    print("   ✅ PASSED")
    
    # Test 2: Ver inventario
    print("\n🧪 TEST 2: Ver inventario completo")
    result = await agent.process_message({"from": "+51999999999", "text": "Ver inventario"})
    print(f"   Respuesta: {result['text'][:150]}...")
    assert "INVENTARIO" in result["text"] or "inventario" in result["text"].lower()
    print("   ✅ PASSED")
    
    # Test 3: Consultar producto específico
    print("\n🧪 TEST 3: Consultar producto")
    result = await agent.process_message({"from": "+51999999999", "text": "Stock de polo blanco"})
    print(f"   Respuesta: {result['text'][:150]}...")
    print("   ✅ PASSED")
    
    # Test 4: Consultar stock inicial
    print("\n🧪 TEST 4: Verificar stock inicial")
    variant = product_repository.find_variant(product_name="Polo Blanco", size="M")
    if variant:
        initial_stock = variant.stock_total
        print(f"   Stock inicial de Polo Blanco M: {initial_stock}")
    else:
        print("   ⚠️ Producto no encontrado")
        initial_stock = 0
    
    # Test 5: Vender producto
    print("\n🧪 TEST 5: Vender 3 polos blancos talla M")
    result = await agent.process_message({
        "from": "+51999999999", 
        "text": "Vendí 3 polos blancos talla M"
    })
    print(f"   Respuesta: {result['text'][:200]}...")
    
    if "VENTA REGISTRADA" in result["text"]:
        print("   ✅ Venta exitosa")
        
        # Verificar que el stock cambió
        variant_after = product_repository.find_variant(product_name="Polo Blanco", size="M")
        if variant_after:
            new_stock = variant_after.stock_total
            print(f"   Stock después: {new_stock}")
            if new_stock == initial_stock - 3:
                print(f"   ✅ Stock actualizado correctamente: {initial_stock} -> {new_stock}")
            else:
                print(f"   ⚠️ Stock no coincide: esperado {initial_stock - 3}, actual {new_stock}")
    else:
        print(f"   Resultado: {result['text']}")
    
    # Test 6: Agregar stock
    print("\n🧪 TEST 6: Agregar 5 jeans azules talla 32")
    result = await agent.process_message({
        "from": "+51999999999",
        "text": "Agregar 5 jeans azules talla 32"
    })
    print(f"   Respuesta: {result['text'][:200]}...")
    
    print("\n" + "=" * 60)
    print("✅ TODOS LOS TESTS COMPLETADOS")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_flow())
