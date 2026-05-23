"""Script de prueba para Gemini NLU"""
from src.agents.gemini_nlu import gemini_nlu

def test_nlu():
    print("\n" + "="*80)
    print("PRUEBA DE GEMINI NLU")
    print("="*80 + "\n")
    
    test_messages = [
        "Vendí 3 polos blancos M",
        "Cuánto stock hay de jean azul 32",
        "Llegaron 10 camisas celestes L",
        "Se fueron 2 pantalones negros 34",
        "Hola",
        "Resumen del día"
    ]
    
    for msg in test_messages:
        print(f"📨 Mensaje: '{msg}'")
        parsed = gemini_nlu.parse(msg)
        print(f"   ✅ Acción: {parsed.action}")
        print(f"   📦 Producto: {parsed.product_name or 'N/A'}")
        print(f"   🔢 Cantidad: {parsed.quantity or 'N/A'}")
        print(f"   📊 Confianza: {parsed.confidence:.2f}")
        print(f"   ✓ Válido: {gemini_nlu.is_valid_command(parsed)}")
        print()

if __name__ == "__main__":
    test_nlu()
