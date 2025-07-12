import os
from google.cloud import texttospeech
from config import Config
from models import db, SystemLog
import uuid

class TTSService:
    def __init__(self):
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = Config.GOOGLE_CLOUD_CREDENTIALS
        self.client = texttospeech.TextToSpeechClient()
        
        self.language_codes = {
            'en': 'en-US',
            'es': 'es-ES',
            'fr': 'fr-FR',
            'de': 'de-DE',
            'pt': 'pt-BR'
        }
        
        self.voice_mapping = {
            'en': 'en-US-Neural2-F',
            'es': 'es-ES-Neural2-A',
            'fr': 'fr-FR-Neural2-A',
            'de': 'de-DE-Neural2-A',
            'pt': 'pt-BR-Neural2-A'
        }
        
        os.makedirs(Config.AUDIO_FOLDER, exist_ok=True)
    
    def text_to_speech(self, text, language='en', filename=None):
        try:
            if not text:
                return None
            
            language_code = self.language_codes.get(language, 'en-US')
            voice_name = self.voice_mapping.get(language, 'en-US-Neural2-F')
            
            synthesis_input = texttospeech.SynthesisInput(text=text)
            
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name
            )
            
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                speaking_rate=0.9,
                pitch=0.0,
                volume_gain_db=0.0
            )
            
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            if not filename:
                filename = f"{uuid.uuid4().hex}.mp3"
            
            file_path = os.path.join(Config.AUDIO_FOLDER, filename)
            
            with open(file_path, "wb") as out:
                out.write(response.audio_content)
            
            self._log_system('info', f"Successfully converted text to speech: {filename}")
            
            return filename
            
        except Exception as e:
            self._log_system('error', f"TTS conversion failed: {str(e)}")
            return None
    
    def create_daily_audio(self, summary_text, language='en'):
        try:
            if not summary_text:
                return None
            
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"daily_summary_{language}_{timestamp}.mp3"
            
            return self.text_to_speech(summary_text, language, filename)
            
        except Exception as e:
            self._log_system('error', f"Error creating daily audio: {str(e)}")
            return None
    
    def create_article_audio(self, article_title, summary_text, language='en'):
        try:
            if not summary_text:
                return None
            
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_title = "".join(c for c in article_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title[:30]
            filename = f"article_{safe_title}_{language}_{timestamp}.mp3"
            
            return self.text_to_speech(summary_text, language, filename)
            
        except Exception as e:
            self._log_system('error', f"Error creating article audio: {str(e)}")
            return None
    
    def get_audio_url(self, filename):
        if filename:
            return f"/static/audio/{filename}"
        return None
    
    def cleanup_old_audio(self, days=7):
        try:
            import glob
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            audio_pattern = os.path.join(Config.AUDIO_FOLDER, "*.mp3")
            
            deleted_count = 0
            for file_path in glob.glob(audio_pattern):
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
            
            if deleted_count > 0:
                self._log_system('info', f"Cleaned up {deleted_count} old audio files")
                
        except Exception as e:
            self._log_system('error', f"Error cleaning up audio files: {str(e)}")
    
    def _log_system(self, level, message):
        try:
            log = SystemLog(level=level, message=message)
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            # If we can't log to database, just print the message
            print(f"[{level.upper()}] {message}") 