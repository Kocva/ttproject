import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///G:/Users/kocva/OneDrive/Рабочий стол/project/instance/tickets.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    login_manager.init_app(app)
    # Импорт маршрутов из других файлов
    from .web import web_bp
    from .api import api_bp

    # Устанавливаем страницу для логина
    login_manager.login_view = 'web.login'
    from .web import load_user
    login_manager.user_loader(load_user)
    # Регистрируем Blueprint для web.py
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    return app