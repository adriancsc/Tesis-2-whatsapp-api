from src.config import settings
from src.agents.gemini_nlu import gemini_nlu
import google.generativeai as genai
import traceback

# Configurar Gemini
genai.configure(api_key=settings.GEMINI_API_KEY)

with open("gemini_results.txt", "w", encoding="utf-8") as f:
    f.write(f"📦 Google Generative AI Version: {genai.__version__}\n")
    f.write(f"🔑 Gemini API Key configured: {'Yes' if settings.GEMINI_API_KEY else 'No'}\n")
    f.write(f"🤖 Gemini Model: {settings.GEMINI_MODEL}\n\n")

    test_phrases = [
        "Hola",
        "quiero ver saber el inventario de productos",
        "Vendí 3 polos blancos talla M"
    ]

    f.write("🧪 Testing Gemini NLU...\n")
    for text in test_phrases:
        f.write(f"\n📝 Input: '{text}'\n")
        
        # Test NLU wrapper (will use fallback if API fails)
        try:
            result = gemini_nlu.parse(text)
            f.write(f"✅ Result: Action={result.action}, Confidence={result.confidence}\n")
            f.write(f"   Details: {result}\n")
        except Exception as e:
            f.write(f"❌ Error in NLU Parse: {e}\n")
        
        f.write("-" * 20 + "\n")
