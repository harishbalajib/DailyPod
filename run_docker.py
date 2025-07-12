#!/usr/bin/env python3

import os
import sys
from app import app

def main():
    print("Starting DailyPod with Docker setup")
    print("=" * 50)
    
    required_vars = [
        'OPENAI_API_KEY',
        'WHATSAPP_TOKEN', 
        'WHATSAPP_PHONE_ID',
        'NEWS_API_KEY',
        'GOOGLE_CLOUD_CREDENTIALS'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file.")
        sys.exit(1)
    
    print("Environment variables configured")
    print("Database initialized")
    print("Docker services should be running separately")
    print("\nStarting web server...")
    print(f"   Main site: http://localhost:8001")
    print(f"   Admin panel: http://localhost:8001/admin/login")
    print("\nDailyPod is ready!")
    print("=" * 50)
    
    try:
        app.run(
            host=app.config['HOST'],
            port=app.config['PORT'],
            debug=app.config['DEBUG']
        )
    except KeyboardInterrupt:
        print("\nShutting down DailyPod...")
        print("DailyPod stopped successfully")
    except Exception as e:
        print(f"Error starting DailyPod: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 