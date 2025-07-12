from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

from config import Config
from models import db, User, NewsArticle, DeliveryLog, SystemLog
from services.news_service import NewsService
from services.ai_service import AIService
from services.tts_service import TTSService
from services.whatsapp_service import WhatsAppService
from tasks import fetch_news_task, daily_delivery_task, cleanup_audio_task, health_check_task
from scheduler import NewsScheduler

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'admin_login'

news_service = NewsService()
ai_service = AIService()
tts_service = TTSService()
whatsapp_service = WhatsAppService()

scheduler = NewsScheduler()

class AdminUser(UserMixin):
    def __init__(self):
        self.id = "admin"
        self.phone_number = "admin"
    def get_id(self):
        return "admin"

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return AdminUser()
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    os.makedirs(Config.AUDIO_FOLDER, exist_ok=True)
    os.makedirs(Config.UPLOADS_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subscribe', methods=['GET', 'POST'])
def subscribe():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        language = request.form.get('language', 'en')
        
        if not phone_number:
            flash('Phone number is required', 'error')
            return render_template('subscribe.html')
        
        phone_number = ''.join(filter(str.isdigit, phone_number))
        
        if not phone_number.startswith('1'):
            phone_number = '1' + phone_number
        
        existing_user = User.query.filter_by(phone_number=phone_number).first()
        
        if existing_user:
            if existing_user.is_active:
                flash('You are already subscribed!', 'info')
            else:
                existing_user.is_active = True
                existing_user.language = language
                db.session.commit()
                flash('Welcome back! Your subscription has been reactivated.', 'success')
        else:
            new_user = User(
                phone_number=phone_number,
                language=language
            )
            db.session.add(new_user)
            db.session.commit()
            
            try:
                whatsapp_service.send_welcome_message(phone_number, language)
                flash('Welcome to DailyPod! You will receive your first news summary tomorrow at 7:30 AM.', 'success')
            except Exception as e:
                flash('Subscription successful, but there was an issue sending the welcome message.', 'warning')
        
        return redirect(url_for('index'))
    
    return render_template('subscribe.html')

@app.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        
        if not phone_number:
            flash('Phone number is required', 'error')
            return render_template('unsubscribe.html')
        
        phone_number = ''.join(filter(str.isdigit, phone_number))
        if not phone_number.startswith('1'):
            phone_number = '1' + phone_number
        
        user = User.query.filter_by(phone_number=phone_number).first()
        
        if user and user.is_active:
            user.is_active = False
            db.session.commit()
            
            try:
                whatsapp_service.send_unsubscribe_message(phone_number, user.language)
            except:
                pass
            
            flash('You have been successfully unsubscribed from DailyPod.', 'success')
        else:
            flash('No active subscription found for this phone number.', 'error')
        
        return redirect(url_for('index'))
    
    return render_template('unsubscribe.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            admin_user = AdminUser()
            login_user(admin_user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    print(f"Admin dashboard accessed by user: {current_user}")
    print(f"Current user ID: {current_user.id}")
    print(f"Current user phone: {current_user.phone_number}")
    
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_articles = NewsArticle.query.count()
    recent_articles = NewsArticle.query.filter(
        NewsArticle.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    ).count()
    
    recent_logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(10).all()
    
    users_by_language = db.session.query(User.language, db.func.count(User.id)).group_by(User.language).all()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         total_articles=total_articles,
                         recent_articles=recent_articles,
                         recent_logs=recent_logs,
                         users_by_language=users_by_language)

@app.route('/admin/users')
@login_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=50, error_out=False)
    return render_template('admin_users.html', users=users)

@app.route('/admin/articles')
@login_required
def admin_articles():
    page = request.args.get('page', 1, type=int)
    language = request.args.get('language', 'en')
    
    query = NewsArticle.query
    if language != 'all':
        query = query.filter_by(language=language)
    
    articles = query.order_by(NewsArticle.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin_articles.html', articles=articles, current_language=language)

@app.route('/api/fetch-news', methods=['POST'])
@login_required
def api_fetch_news():
    try:
        language = request.json.get('language', 'en')
        category = request.json.get('category', 'general')
        
        result = fetch_news_task.delay()
        
        return jsonify({
            'success': True,
            'message': f'News fetching initiated',
            'task_id': result.id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/manual-delivery', methods=['POST'])
@login_required
def api_manual_delivery():
    try:
        language = request.json.get('language', 'en')
        result = daily_delivery_task.delay()
        
        return jsonify({
            'success': True,
            'message': f'Manual delivery triggered for {language}',
            'task_id': result.id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats')
@login_required
def api_stats():
    try:
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_articles = NewsArticle.query.count()
        
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        recent_articles = NewsArticle.query.filter(NewsArticle.created_at >= today).count()
        recent_deliveries = DeliveryLog.query.filter(DeliveryLog.sent_at >= today).count()
        
        return jsonify({
            'total_users': total_users,
            'active_users': active_users,
            'total_articles': total_articles,
            'recent_articles': recent_articles,
            'recent_deliveries': recent_deliveries
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<int:user_id>/toggle', methods=['POST'])
@login_required
def api_toggle_user(user_id):
    try:
        user = User.query.get_or_404(user_id)
        user.is_active = not user.is_active
        db.session.commit()
        
        return jsonify({
            'success': True,
            'is_active': user.is_active,
            'message': f'User {"activated" if user.is_active else "deactivated"}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    try:
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )
    except KeyboardInterrupt:
        print("Shutting down DailyPod...") 