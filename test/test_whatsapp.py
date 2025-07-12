import os
import sys
import requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from services.whatsapp_service import WhatsAppService
from app import app

def check_env():
    print("Checking environment configuration for WhatsApp API keys...")
    token = Config.WHATSAPP_TOKEN
    phone_id = Config.WHATSAPP_PHONE_ID
    if not token or not phone_id:
        print("FAILED: WhatsApp API keys are not properly configured in the environment.")
        return False
    print("SUCCESS: WhatsApp API keys are present in the environment.")
    return True

def check_token_validity():
    print("Checking WhatsApp API token validity...")
    token = Config.WHATSAPP_TOKEN
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get("https://graph.facebook.com/v17.0/me", headers=headers, timeout=10)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS: Token is valid.")
            return True
        else:
            print("FAILED: Token is invalid or expired.")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"ERROR: Exception occurred while checking token: {e}")
        return False

def check_send_message():
    print("Checking WhatsApp message sending...")
    with app.app_context():
        whatsapp = WhatsAppService()
        test_phone = "+13475525608"
        test_message = "Hello, this is a test message from DailyPod to verify WhatsApp integration."
        try:
            result = whatsapp.send_text_message(test_phone, test_message)
            if result and 'messages' in result:
                print("SUCCESS: Message sent successfully.")
                print(f"Response: {result}")
                return True
            else:
                print("FAILED: Message sending failed.")
                print(f"Response: {result}")
                return False
        except Exception as e:
            print(f"ERROR: Exception occurred while sending message: {e}")
            return False

def main():
    env_ok = check_env()
    token_ok = check_token_validity() if env_ok else False
    send_ok = check_send_message() if token_ok else False
    print("\nSummary:")
    print(f"Environment configured: {env_ok}")
    print(f"Token valid: {token_ok}")
    print(f"Can send message: {send_ok}")
    if env_ok and token_ok and send_ok:
        print("Test result: WhatsApp integration is working.")
    else:
        print("Test result: WhatsApp integration is NOT working.")

if __name__ == "__main__":
    main() 