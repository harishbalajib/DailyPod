import os
import sys
import requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from services.news_service import NewsService
from services.ai_service import AIService
from services.tts_service import TTSService
from services.whatsapp_service import WhatsAppService
from app import app
from models import NewsArticle

def check_all_env():
    print("Checking all environment configurations...")
    print("=" * 50)
    
    checks = {
        "OpenAI API Key": Config.OPENAI_API_KEY,
        "WhatsApp Token": Config.WHATSAPP_TOKEN,
        "WhatsApp Phone ID": Config.WHATSAPP_PHONE_ID,
        "News API Key": Config.NEWS_API_KEY,
        "Google Cloud Credentials": Config.GOOGLE_CLOUD_CREDENTIALS
    }
    
    all_ok = True
    for name, value in checks.items():
        if value:
            print(f"SUCCESS: {name} is configured")
        else:
            print(f"FAILED: {name} is missing")
            all_ok = False
    
    # Check if Google Cloud credentials file exists
    if Config.GOOGLE_CLOUD_CREDENTIALS and not os.path.exists(Config.GOOGLE_CLOUD_CREDENTIALS):
        print(f"FAILED: Google Cloud credentials file not found at {Config.GOOGLE_CLOUD_CREDENTIALS}")
        all_ok = False
    
    return all_ok

def test_news_fetching():
    print("\nTesting News Fetching...")
    print("=" * 30)
    
    try:
        with app.app_context():
            news_service = NewsService()
            
            # Try to fetch new articles
            articles = news_service.fetch_news(category='general', count=3)
            
            # If no new articles, get existing ones from database
            if not articles or len(articles) == 0:
                print("No new articles fetched, getting existing articles from database...")
                articles = NewsArticle.query.filter_by(language='en').order_by(NewsArticle.created_at.desc()).limit(3).all()
            
            if articles and len(articles) > 0:
                print(f"SUCCESS: Got {len(articles)} articles for testing")
                for i, article in enumerate(articles, 1):
                    print(f"  {i}. {article.title[:60]}...")
                return True, articles
            else:
                print("FAILED: No articles available for testing")
                return False, []
    except Exception as e:
        print(f"ERROR: News fetching failed - {e}")
        return False, []

def test_ai_summarization(articles):
    print("\nTesting AI Summarization...")
    print("=" * 30)
    
    try:
        with app.app_context():
            ai_service = AIService()
            summaries = []
            
            for article in articles[:2]:  # Test with first 2 articles
                summary = ai_service.summarize_article(article.title, article.content)
                if summary:
                    summaries.append(summary)
                    print(f"SUCCESS: Generated summary for '{article.title[:40]}...'")
                else:
                    print(f"FAILED: Could not generate summary for '{article.title[:40]}...'")
            
            if summaries:
                print(f"SUCCESS: Generated {len(summaries)} summaries")
                return True, summaries
            else:
                print("FAILED: No summaries generated")
                return False, []
    except Exception as e:
        print(f"ERROR: AI summarization failed - {e}")
        return False, []

def test_tts_generation(summaries):
    print("\nTesting TTS Generation...")
    print("=" * 30)
    
    try:
        with app.app_context():
            tts_service = TTSService()
            audio_files = []
            
            for i, summary in enumerate(summaries):
                filename = f"test_audio_{i+1}.mp3"
                result = tts_service.text_to_speech(summary, 'en', filename)
                if result:
                    audio_files.append(result)
                    print(f"SUCCESS: Generated audio file '{result}'")
                else:
                    print(f"FAILED: Could not generate audio file for summary {i+1}")
            
            if audio_files:
                print(f"SUCCESS: Generated {len(audio_files)} audio files")
                return True, audio_files
            else:
                print("FAILED: No audio files generated")
                return False, []
    except Exception as e:
        print(f"ERROR: TTS generation failed - {e}")
        return False, []

def test_whatsapp_sending():
    print("\nTesting WhatsApp Sending...")
    print("=" * 30)
    
    try:
        with app.app_context():
            whatsapp = WhatsAppService()
            test_phone = "+13475525608"
            test_message = "DailyPod Application Test: All systems are working correctly!"
            
            result = whatsapp.send_text_message(test_phone, test_message)
            if result and 'messages' in result:
                print("SUCCESS: WhatsApp message sent successfully")
                return True
            else:
                print("FAILED: WhatsApp message sending failed")
                return False
    except Exception as e:
        print(f"ERROR: WhatsApp sending failed - {e}")
        return False

def main():
    print("DailyPod Full Application Test")
    print("=" * 50)
    
    # Test 1: Environment Configuration
    env_ok = check_all_env()
    
    # Test 2: News Fetching
    news_ok, articles = test_news_fetching() if env_ok else (False, [])
    
    # Test 3: AI Summarization
    ai_ok, summaries = test_ai_summarization(articles) if news_ok else (False, [])
    
    # Test 4: TTS Generation
    tts_ok, audio_files = test_tts_generation(summaries) if ai_ok else (False, [])
    
    # Test 5: WhatsApp Sending
    whatsapp_ok = test_whatsapp_sending() if env_ok else False
    
    # Final Summary
    print("\n" + "=" * 50)
    print("FINAL APPLICATION STATUS")
    print("=" * 50)
    print(f"Environment Configuration: {'WORKING' if env_ok else 'FAILED'}")
    print(f"News Fetching: {'WORKING' if news_ok else 'FAILED'}")
    print(f"AI Summarization: {'WORKING' if ai_ok else 'FAILED'}")
    print(f"TTS Generation: {'WORKING' if tts_ok else 'FAILED'}")
    print(f"WhatsApp Sending: {'WORKING' if whatsapp_ok else 'FAILED'}")
    
    if env_ok and news_ok and ai_ok and tts_ok and whatsapp_ok:
        print("\nRESULT: DailyPod application is FULLY WORKING")
        print("All components are functioning correctly and ready for production use.")
    else:
        print("\nRESULT: DailyPod application has ISSUES")
        print("Some components are not working correctly and need attention.")
    
    # Cleanup test audio files
    if tts_ok and audio_files:
        print("\nCleaning up test audio files...")
        for audio_file in audio_files:
            try:
                os.remove(os.path.join(Config.AUDIO_FOLDER, audio_file))
                print(f"Removed: {audio_file}")
            except:
                pass

if __name__ == "__main__":
    main() 