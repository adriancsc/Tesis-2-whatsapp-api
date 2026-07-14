import requests
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("WHATSAPP_API_TOKEN")
PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")

url = f"https://graph.facebook.com/v17.0/{PHONE_ID}/subscribed_apps"
headers = {"Authorization": f"Bearer {TOKEN}"}

print(f"Checking subscribed apps for phone ID: {PHONE_ID}")
response = requests.get(url, headers=headers)
print("Status:", response.status_code)
print("Response:", response.json())

# Also check WABA webhooks
url2 = f"https://graph.facebook.com/v17.0/{PHONE_ID}"
response2 = requests.get(url2, headers=headers)
if response2.status_code == 200:
    waba_id = response2.json().get("whatsapp_business_account_id")
    print(f"\nChecking webhooks for WABA ID: {waba_id}")
    url3 = f"https://graph.facebook.com/v17.0/{waba_id}/subscribed_apps"
    response3 = requests.get(url3, headers=headers)
    print("Response:", response3.json())
