import requests
import json
from config import Config
from models import db, User, DeliveryLog, SystemLog

class WhatsAppService:
    def __init__(self):
        self.token = Config.WHATSAPP_TOKEN
        self.phone_id = Config.WHATSAPP_PHONE_ID
        self.base_url = f"https://graph.facebook.com/v17.0/{self.phone_id}"
        
    def send_text_message(self, phone_number, message):
        try:
            url = f"{self.base_url}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {"body": message}
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            self._log_system('info', f"Text message sent to {phone_number}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self._log_system('error', f"WhatsApp API request failed: {str(e)}")
            return None
        except Exception as e:
            self._log_system('error', f"Error sending text message: {str(e)}")
            return None
    
    def send_audio_message(self, phone_number, audio_url, caption=None):
        try:
            url = f"{self.base_url}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "audio",
                "audio": {
                    "link": audio_url
                }
            }
            
            if caption:
                data["audio"]["caption"] = caption
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            
            self._log_system('info', f"Audio message sent to {phone_number}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            self._log_system('error', f"WhatsApp API request failed: {str(e)}")
            return None
        except Exception as e:
            self._log_system('error', f"Error sending audio message: {str(e)}")
            return None
    
    def send_daily_news(self, user, audio_filename, summary_text):
        try:
            audio_url = f"https://your-domain.com/static/audio/{audio_filename}"
            
            caption = f"Daily News Summary\n\n{summary_text[:200]}..."
            
            result = self.send_audio_message(user.phone_number, audio_url, caption)
            
            if result:
                from datetime import datetime
                user.last_delivery = datetime.utcnow()
                db.session.commit()
                
                self._log_delivery(user.id, None, 'sent')
                
                return True
            else:
                self._log_delivery(user.id, None, 'failed', "WhatsApp API error")
                return False
                
        except Exception as e:
            self._log_system('error', f"Error sending daily news to {user.phone_number}: {str(e)}")
            self._log_delivery(user.id, None, 'failed', str(e))
            return False
    
    def send_welcome_message(self, phone_number, language='en'):
        welcome_messages = {
            'en': "Welcome to DailyPod! You'll receive your daily news summary every morning at 7:30 AM. Stay informed with our AI-powered news podcast!",
            'es': "¡Bienvenido a DailyPod! Recibirás tu resumen de noticias diario todas las mañanas a las 7:30 AM. ¡Mantente informado con nuestro podcast de noticias con IA!",
            'fr': "Bienvenue sur DailyPod ! Vous recevrez votre résumé d'actualités quotidien tous les matins à 7h30. Restez informé avec notre podcast d'actualités alimenté par l'IA !",
            'de': "Willkommen bei DailyPod! Sie erhalten jeden Morgen um 7:30 Uhr Ihre tägliche Nachrichtenzusammenfassung. Bleiben Sie mit unserem KI-gestützten Nachrichten-Podcast informiert!",
            'pt': "Bem-vindo ao DailyPod! Você receberá seu resumo de notícias diário todas as manhãs às 7:30. Mantenha-se informado com nosso podcast de notícias alimentado por IA!"
        }
        
        message = welcome_messages.get(language, welcome_messages['en'])
        return self.send_text_message(phone_number, message)
    
    def send_unsubscribe_message(self, phone_number, language='en'):
        unsubscribe_messages = {
            'en': "You have been successfully unsubscribed from DailyPod. We're sorry to see you go! You can resubscribe anytime by visiting our website.",
            'es': "Has sido dado de baja exitosamente de DailyPod. ¡Lamentamos verte partir! Puedes volver a suscribirte en cualquier momento visitando nuestro sitio web.",
            'fr': "Vous avez été désabonné avec succès de DailyPod. Nous sommes désolés de vous voir partir ! Vous pouvez vous réabonner à tout moment en visitant notre site web.",
            'de': "Sie wurden erfolgreich von DailyPod abgemeldet. Es tut uns leid, Sie gehen zu sehen! Sie können sich jederzeit wieder anmelden, indem Sie unsere Website besuchen.",
            'pt': "Você foi cancelado com sucesso do DailyPod. Sentimos muito vê-lo partir! Você pode se reinscrever a qualquer momento visitando nosso site."
        }
        
        message = unsubscribe_messages.get(language, unsubscribe_messages['en'])
        return self.send_text_message(phone_number, message)
    
    def send_error_message(self, phone_number, language='en'):
        error_messages = {
            'en': "Sorry, we encountered an issue delivering your daily news today. We'll try again tomorrow. Thank you for your patience!",
            'es': "Lo sentimos, encontramos un problema al entregar sus noticias diarias hoy. Intentaremos de nuevo mañana. ¡Gracias por su paciencia!",
            'fr': "Désolé, nous avons rencontré un problème lors de la livraison de vos actualités quotidiennes aujourd'hui. Nous réessayerons demain. Merci pour votre patience !",
            'de': "Entschuldigung, wir hatten heute ein Problem bei der Lieferung Ihrer täglichen Nachrichten. Wir versuchen es morgen erneut. Vielen Dank für Ihre Geduld!",
            'pt': "Desculpe, encontramos um problema ao entregar suas notícias diárias hoje. Tentaremos novamente amanhã. Obrigado pela sua paciência!"
        }
        
        message = error_messages.get(language, error_messages['en'])
        return self.send_text_message(phone_number, message)
    
    def _log_delivery(self, user_id, article_id, status, error_message=None):
        delivery = DeliveryLog(
            user_id=user_id,
            article_id=article_id,
            status=status,
            error_message=error_message
        )
        db.session.add(delivery)
        db.session.commit()
    
    def _log_system(self, level, message):
        log = SystemLog(level=level, message=message)
        db.session.add(log)
        db.session.commit() 