import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
    WHATSAPP_PHONE_ID = os.getenv('WHATSAPP_PHONE_ID')
    NEWS_API_KEY = os.getenv('NEWS_API_KEY')
    GOOGLE_CLOUD_CREDENTIALS = os.getenv('GOOGLE_CLOUD_CREDENTIALS')
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8001))
    
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./dailypod.db')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    SUPPORTED_LANGUAGES = os.getenv('SUPPORTED_LANGUAGES', 'en,es,fr,de,pt').split(',')
    
    NEWS_COUNTRIES = ['us']
    NEWS_CATEGORIES = ['general', 'business', 'technology', 'sports', 'entertainment']
    
    DAILY_DELIVERY_TIME = '07:30'
    
    AUDIO_FOLDER = 'static/audio'
    UPLOADS_FOLDER = 'static/uploads' 