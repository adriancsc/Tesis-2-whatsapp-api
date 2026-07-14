"""
Suscribir la App al WhatsApp Business Account para recibir webhooks reales.
"""
import requests

TOKEN = "EAAVv0cnP3EkBRzNuNDCex6WTkRchNa9fdXd8fZCMNHXLR5JnvMmATfNrUHpjLNdByM5FTDgAL2Wz9ZC475s2fkYiliF5maRYcxDju0WSruf5a5RlnZCBIcS7onhZCc1jkwwZCcstLiRLWP7po2KHmWfA9nCMN4jDXBhhwzYSJHFHqHKx7IXfgBu01zgqDZBwZDZD"
WABA_ID = "1769761744223678"

headers = {"Authorization": f"Bearer {TOKEN}"}

# Step 1: Suscribir la app al WABA
print(f"Suscribiendo app al WABA {WABA_ID}...")
url = f"https://graph.facebook.com/v25.0/{WABA_ID}/subscribed_apps"
response = requests.post(url, headers=headers)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Step 2: Verificar la suscripcion
print(f"\nVerificando suscripciones activas...")
response2 = requests.get(url, headers=headers)
print(f"Status: {response2.status_code}")
print(f"Suscripciones: {response2.json()}")

# Step 3: Probar enviar un mensaje simple para verificar el token
print(f"\nProbando envio de mensaje...")
PHONE_ID = "1112076461997080"
url3 = f"https://graph.facebook.com/v25.0/{PHONE_ID}/messages"
payload = {
    "messaging_product": "whatsapp",
    "to": "51990129187",
    "type": "text",
    "text": {"body": "🤖 Test de conexion exitoso!"}
}
response3 = requests.post(url3, headers=headers, json=payload)
print(f"Status: {response3.status_code}")
print(f"Response: {response3.json()}")
