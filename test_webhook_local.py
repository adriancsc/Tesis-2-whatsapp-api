import requests
import json

def test_webhook():
    url = "http://localhost:8000/api/whatsapp/webhook"
    
    # Payload simulando un mensaje de WhatsApp "Hola"
    payload = {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "123456789",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {
                        "display_phone_number": "123456789",
                        "phone_number_id": "987654321"
                    },
                    "contacts": [{
                        "profile": {"name": "Test User"},
                        "wa_id": "51999999999"
                    }],
                    "messages": [{
                        "from": "51999999999",
                        "id": "wamid.HBgMNTE5OTk5OTk5OTkVAgASGBQ3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3AA==",
                        "timestamp": "1702190000",
                        "text": {"body": "Hola"},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }
    
    try:
        print(f"📤 Enviando webhook a {url}...")
        response = requests.post(url, json=payload)
        print(f"📥 Respuesta: {response.status_code}")
        print(f"📄 Cuerpo: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_webhook()
