#!/usr/bin/env python3
"""
Веб-приложение для courses_generator
Flask приложение с аутентификацией, загрузкой видео и интеграцией с Wav2Lip
"""

import os
import secrets
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import subprocess
import json
import uuid
from pathlib import Path
import pyttsx3
from gtts import gTTS
import threading
import time

# Импорт Wav2Lip процессора
from wav2lip_processor import process_video_with_wav2lip

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация Flask
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'postgresql://courses_user:courses_password@postgres:5432/courses_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = '/app/uploads'
app.config['OUTPUT_FOLDER'] = '/app/outputs'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# Создание папок для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Инициализация расширений
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Модели базы данных
class User(UserMixin, db.Model):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Связи
    projects = db.relationship('Project', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Project(db.Model):
    """Модель проекта"""
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    video_path = db.Column(db.String(500))
    text_content = db.Column(db.Text)  # Текст для озвучивания
    generated_audio_path = db.Column(db.String(500))  # Сгенерированное аудио
    output_path = db.Column(db.String(500))
    status = db.Column(db.String(50), default='pending')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    tasks = db.relationship('ProcessingTask', backref='project', lazy=True)
    results = db.relationship('Result', backref='project', lazy=True)

class ProcessingTask(db.Model):
    """Модель задачи обработки"""
    __tablename__ = 'processing_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    task_type = db.Column(db.String(100), nullable=False)
    parameters = db.Column(db.JSON)
    status = db.Column(db.String(50), default='queued')
    progress = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Result(db.Model):
    """Модель результата"""
    __tablename__ = 'results'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('processing_tasks.id'), nullable=False)
    file_path = db.Column(db.String(500))
    file_size = db.Column(db.BigInteger)
    duration_seconds = db.Column(db.Integer)
    quality_metrics = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Загрузчик пользователей для Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_audio_from_text(text, output_path, language='ru'):
    """Генерация аудио из текста с помощью gTTS"""
    try:
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(output_path)
        return True
    except Exception as e:
        logger.error(f"Ошибка генерации аудио: {e}")
        return False

def generate_audio_from_text_local(text, output_path):
    """Генерация аудио из текста с помощью pyttsx3 (локально)"""
    try:
        engine = pyttsx3.init()
        engine.setProperty('rate', 150)  # Скорость речи
        engine.setProperty('volume', 0.9)  # Громкость
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        return True
    except Exception as e:
        logger.error(f"Ошибка локальной генерации аудио: {e}")
        return False

# Декоратор для проверки прав администратора
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Требуются права администратора', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Маршруты
@app.route('/')
def index():
    """Главная страница"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Страница входа"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            
            flash('Успешный вход!', 'success')
            return redirect(next_page)
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Страница регистрации"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Валидация
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Пароли не совпадают', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Пароль должен содержать минимум 6 символов', 'error')
            return render_template('register.html')
        
        # Создание пользователя
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация успешна! Теперь вы можете войти', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Личный кабинет"""
    projects = Project.query.filter_by(user_id=current_user.id).order_by(Project.created_at.desc()).all()
    return render_template('dashboard.html', projects=projects)

@app.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    """Создание нового проекта"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        if not name:
            flash('Название проекта обязательно', 'error')
            return render_template('new_project.html')
        
        # Создание проекта
        project = Project(
            name=name,
            description=description,
            user_id=current_user.id
        )
        
        db.session.add(project)
        db.session.commit()
        
        flash('Проект создан!', 'success')
        return redirect(url_for('project_detail', project_id=project.id))
    
    return render_template('new_project.html')

@app.route('/project/<int:project_id>')
@login_required
def project_detail(project_id):
    """Детали проекта"""
    project = Project.query.get_or_404(project_id)
    
    # Проверка прав доступа
    if project.user_id != current_user.id and not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('project_detail.html', project=project)

@app.route('/project/<int:project_id>/upload', methods=['POST'])
@login_required
def upload_files(project_id):
    """Загрузка файлов и текста для проекта"""
    project = Project.query.get_or_404(project_id)
    
    # Проверка прав доступа
    if project.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    video_file = request.files.get('video')
    text_content = request.form.get('text_content', '').strip()
    
    if not video_file:
        return jsonify({'error': 'Не выбран видео файл'}), 400
    
    if not text_content:
        return jsonify({'error': 'Не введен текст для озвучивания'}), 400
    
    try:
        # Создание папки для проекта
        project_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(project.id))
        os.makedirs(project_folder, exist_ok=True)
        
        # Загрузка видео
        video_filename = secure_filename(f"video_{uuid.uuid4()}.mp4")
        video_path = os.path.join(project_folder, video_filename)
        video_file.save(video_path)
        project.video_path = video_path
        
        # Сохранение текста
        project.text_content = text_content
        project.status = 'content_ready'
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Видео и текст загружены'})
        
    except Exception as e:
        logger.error(f"Ошибка загрузки файлов: {e}")
        return jsonify({'error': 'Ошибка загрузки файлов'}), 500

@app.route('/project/<int:project_id>/process', methods=['POST'])
@login_required
def process_project(project_id):
    """Запуск обработки проекта"""
    project = Project.query.get_or_404(project_id)
    
    # Проверка прав доступа
    if project.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    if not project.video_path or not project.text_content:
        return jsonify({'error': 'Не загружены видео и текст'}), 400
    
    try:
        # Создание папки для проекта
        project_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(project.id))
        os.makedirs(project_folder, exist_ok=True)
        
        # Генерация аудио из текста
        audio_filename = f"generated_audio_{uuid.uuid4()}.mp3"
        audio_path = os.path.join(project_folder, audio_filename)
        
        # Попробуем сначала gTTS (онлайн), потом pyttsx3 (локально)
        if not generate_audio_from_text(project.text_content, audio_path):
            if not generate_audio_from_text_local(project.text_content, audio_path):
                return jsonify({'error': 'Не удалось сгенерировать аудио'}), 500
        
        # Сохраняем путь к сгенерированному аудио
        project.generated_audio_path = audio_path
        
        # Создание пути для результата
        output_filename = f"result_{uuid.uuid4()}.mp4"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        
        # Создание задачи обработки
        task = ProcessingTask(
            project_id=project.id,
            task_type='text_to_speech_and_sync',
            parameters={
                'text': project.text_content,
                'audio_path': audio_path,
                'output_path': output_path,
                'fps': 25,
                'img_size': 96,
                'batch_size': 1
            },
            status='queued'
        )
        
        db.session.add(task)
        db.session.commit()
        
        # Обновление статуса проекта
        project.status = 'processing'
        db.session.commit()
        
                # Запуск обработки в отдельном потоке
        def process_in_background():
            with app.app_context():
                try:
                    logger.info(f"Начинаем обработку проекта {project.id}")
                    
                    # Обновляем статус задачи
                    task.status = 'processing'
                    task.started_at = datetime.utcnow()
                    db.session.commit()
                    
                    # Запускаем Wav2Lip обработку
                    success, result = process_video_with_wav2lip(
                        project.id,
                        project.video_path,
                        audio_path,
                        output_path
                    )
                    
                    if success:
                        # Обновляем проект
                        project.output_path = output_path
                        project.status = 'completed'
                        
                        # Обновляем задачу
                        task.status = 'completed'
                        task.completed_at = datetime.utcnow()
                        task.progress = 100
                        
                        logger.info(f"Обработка проекта {project.id} завершена успешно")
                    else:
                        # Ошибка обработки
                        project.status = 'failed'
                        task.status = 'failed'
                        task.error_message = str(result)
                        task.completed_at = datetime.utcnow()
                        
                        logger.error(f"Ошибка обработки проекта {project.id}: {result}")
                    
                    db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Ошибка в фоновой обработке проекта {project.id}: {e}")
                    
                    # Обновляем статус при ошибке
                    project.status = 'failed'
                    task.status = 'failed'
                    task.error_message = str(e)
                    task.completed_at = datetime.utcnow()
                    db.session.commit()
        
        # Запускаем обработку в фоне
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()
        
        flash('Обработка запущена! Генерация аудио и синхронизация Wav2Lip...', 'success')
        
        return jsonify({'success': True, 'task_id': task.id})
        
    except Exception as e:
        logger.error(f"Ошибка запуска обработки: {e}")
        return jsonify({'error': 'Ошибка запуска обработки'}), 500

@app.route('/project/<int:project_id>/download')
@login_required
def download_result(project_id):
    """Скачивание результата"""
    project = Project.query.get_or_404(project_id)
    
    # Проверка прав доступа
    if project.user_id != current_user.id and not current_user.is_admin:
        flash('Доступ запрещен', 'error')
        return redirect(url_for('dashboard'))
    
    if not project.output_path or not os.path.exists(project.output_path):
        flash('Результат еще не готов', 'error')
        return redirect(url_for('project_detail', project_id=project.id))
    
    return send_file(project.output_path, as_attachment=True)

@app.route('/admin')
@admin_required
def admin_panel():
    """Панель администратора"""
    users = User.query.all()
    projects = Project.query.all()
    tasks = ProcessingTask.query.all()
    
    return render_template('admin.html', users=users, projects=projects, tasks=tasks)

@app.route('/api/status/<int:task_id>')
@login_required
def task_status(task_id):
    """API для получения статуса задачи"""
    task = ProcessingTask.query.get_or_404(task_id)
    
    # Проверка прав доступа
    if task.project.user_id != current_user.id and not current_user.is_admin:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    return jsonify({
        'id': task.id,
        'status': task.status,
        'progress': task.progress,
        'error_message': task.error_message
    })

# Обработчики ошибок
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Создание таблиц при первом запуске
    with app.app_context():
        db.create_all()
        
        # Создание администратора по умолчанию
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            logger.info('Создан администратор по умолчанию: admin/admin123')
    
    app.run(host='0.0.0.0', port=5000, debug=True)
