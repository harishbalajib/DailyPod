import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from services.tts_service import TTSService

def check_env():
    print("Checking environment configuration for Google Cloud credentials...")
    credentials_path = Config.GOOGLE_CLOUD_CREDENTIALS
    if not credentials_path:
        print("FAILED: GOOGLE_CLOUD_CREDENTIALS is not configured in the environment.")
        return False
    if not os.path.exists(credentials_path):
        print(f"FAILED: Google Cloud credentials file not found at {credentials_path}")
        return False
    print("SUCCESS: Google Cloud credentials are present and file exists.")
    return True

def test_tts():
    print("Testing Text-to-Speech service...")
    with app.app_context():
        tts = TTSService()
        test_text = "Hello, this is a test of the DailyPod text-to-speech service. This audio was generated to verify the TTS integration is working correctly."
        test_filename = "test_tts_output.mp3"
        try:
            result = tts.text_to_speech(test_text, 'en', test_filename)
            if result and os.path.exists(os.path.join(Config.AUDIO_FOLDER, result)):
                print("SUCCESS: TTS audio generated successfully.")
                print(f"Audio file saved as: {result}")
                return True
            else:
                print("FAILED: TTS audio generation failed.")
                return False
        except Exception as e:
            print(f"ERROR: Exception occurred while generating TTS audio: {e}")
            return False

def main():
    env_ok = check_env()
    tts_ok = test_tts() if env_ok else False
    print("\nSummary:")
    print(f"Environment configured: {env_ok}")
    print(f"Can generate TTS audio: {tts_ok}")
    if env_ok and tts_ok:
        print("Test result: TTS integration is working.")
    else:
        print("Test result: TTS integration is NOT working.")

if __name__ == "__main__":
    from app import app
    main() 