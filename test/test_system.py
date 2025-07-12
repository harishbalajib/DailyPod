#!/usr/bin/env python3

import os
import sys
import requests
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models import db, User, NewsArticle, SystemLog
from services.news_service import NewsService
from services.ai_service import AIService
from services.tts_service import TTSService
from services.whatsapp_service import WhatsAppService

def test_config():
    print("Testing configuration...")
    
    required_configs = [
        'OPENAI_API_KEY',
        'WHATSAPP_TOKEN',
        'WHATSAPP_PHONE_ID', 
        'NEWS_API_KEY',
        'GOOGLE_CLOUD_CREDENTIALS'
    ]
    
    for config_name in required_configs:
        value = getattr(Config, config_name, None)
        if value:
            print(f"   {config_name}: Configured")
        else:
            print(f"   {config_name}: Missing")
            return False
    
    print("   Configuration test passed")
    return True

def test_database():
    print("\nTesting database...")
    
    try:
        db.session.execute('SELECT 1')
        print("   Database connection: OK")
        
        db.create_all()
        print("   Database tables: Created")
        
        test_user = User(
            phone_number='1234567890',
            language='en'
        )
        db.session.add(test_user)
        db.session.commit()
        print("   Database write: OK")
        
        db.session.delete(test_user)
        db.session.commit()
        print("   Database cleanup: OK")
        
        return True
    except Exception as e:
        print(f"   Database test failed: {e}")
        return False

def test_news_api():
    print("\nTesting NewsAPI...")
    
    try:
        news_service = NewsService()
        
        articles = news_service.fetch_news(category='general', language='en', count=1)
        
        if articles:
            print(f"   NewsAPI: Connected (fetched {len(articles)} articles)")
            return True
        else:
            print("   NewsAPI: Connected but no articles returned")
            return True
    except Exception as e:
        print(f"   NewsAPI test failed: {e}")
        return False

def test_openai():
    print("\nTesting OpenAI API...")
    
    try:
        ai_service = AIService()
        
        test_text = "This is a test article about technology."
        summary = ai_service.summarize_article("Test Article", test_text, "en")
        
        if summary:
            print(f"   OpenAI API: Connected (summary length: {len(summary)} chars)")
            return True
        else:
            print("   OpenAI API: No summary generated")
            return False
    except Exception as e:
        print(f"   OpenAI API test failed: {e}")
        return False

def test_tts():
    print("\nTesting Google Cloud TTS...")
    
    try:
        tts_service = TTSService()
        
        test_text = "This is a test of the text to speech system."
        filename = tts_service.text_to_speech(test_text, "en", "test_audio.mp3")
        
        if filename:
            print(f"   Google Cloud TTS: Connected (file: {filename})")
            
            try:
                os.remove(os.path.join(Config.AUDIO_FOLDER, filename))
                print("   Test audio file: Cleaned up")
            except:
                pass
            
            return True
        else:
            print("   Google Cloud TTS: No audio file generated")
            return False
    except Exception as e:
        print(f"   Google Cloud TTS test failed: {e}")
        return False

def test_whatsapp():
    print("\nTesting WhatsApp API...")
    
    try:
        whatsapp_service = WhatsAppService()
        
        print("   WhatsApp API: Service initialized")
        print("   Note: Actual message sending requires valid phone numbers")
        return True
    except Exception as e:
        print(f"   WhatsApp API test failed: {e}")
        return False

def test_scheduler():
    print("\nTesting scheduler...")
    
    try:
        from scheduler import NewsScheduler
        scheduler = NewsScheduler()
        print("   Scheduler: Initialized")
        
        scheduler.start()
        print("   Scheduler: Started")
        
        scheduler.stop()
        print("   Scheduler: Stopped")
        
        return True
    except Exception as e:
        print(f"   Scheduler test failed: {e}")
        return False

def main():
    print("DailyPod System Test")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        test_config,
        test_database,
        test_news_api,
        test_openai,
        test_tts,
        test_whatsapp,
        test_scheduler
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"   Test failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed! DailyPod is ready to run.")
        return 0
    else:
        print("Some tests failed. Please check the configuration and try again.")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 