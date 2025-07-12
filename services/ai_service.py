import openai
from config import Config
from models import db, SystemLog

class AIService:
    def __init__(self):
        openai.api_key = Config.OPENAI_API_KEY
        
    def summarize_article(self, title, content, language='en'):
        try:
            language_prompts = {
                'en': 'English',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'pt': 'Portuguese'
            }
            
            lang_name = language_prompts.get(language, 'English')
            
            prompt = f"""
            Please summarize the following news article in {lang_name}. 
            Make it concise and engaging, suitable for a daily news podcast.
            Keep it under 150 words and focus on the key points.
            
            Title: {title}
            Content: {content}
            
            Summary:
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional news summarizer. Create concise, engaging summaries suitable for audio delivery."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content.strip()
            
            self._log_system('info', f"Successfully summarized article: {title[:50]}...")
            
            return summary
            
        except openai.error.OpenAIError as e:
            self._log_system('error', f"OpenAI API error: {str(e)}")
            return None
        except Exception as e:
            self._log_system('error', f"Error summarizing article: {str(e)}")
            return None
    
    def create_daily_summary(self, articles, language='en'):
        try:
            if not articles:
                return None
            
            language_prompts = {
                'en': 'English',
                'es': 'Spanish',
                'fr': 'French',
                'de': 'German',
                'pt': 'Portuguese'
            }
            
            lang_name = language_prompts.get(language, 'English')
            
            articles_text = ""
            for i, article in enumerate(articles[:5], 1):
                articles_text += f"{i}. {article.title}\n"
                if article.summary:
                    articles_text += f"   {article.summary}\n\n"
                else:
                    articles_text += f"   {article.content[:200]}...\n\n"
            
            prompt = f"""
            Create a daily news summary in {lang_name} for a podcast format.
            Combine the following top stories into a cohesive 2-3 minute summary.
            Make it engaging and conversational, as if you're speaking to listeners.
            
            Stories:
            {articles_text}
            
            Daily Summary:
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional news anchor creating a daily news podcast. Make the summary engaging and conversational."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content.strip()
            
            self._log_system('info', f"Created daily summary for {len(articles)} articles in {language}")
            
            return summary
            
        except openai.error.OpenAIError as e:
            self._log_system('error', f"OpenAI API error in daily summary: {str(e)}")
            return None
        except Exception as e:
            self._log_system('error', f"Error creating daily summary: {str(e)}")
            return None
    
    def _log_system(self, level, message):
        log = SystemLog(level=level, message=message)
        db.session.add(log)
        db.session.commit() 