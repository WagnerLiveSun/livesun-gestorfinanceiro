import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent

class Config:
    """Base configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-change-in-production'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = True
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Upload files
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Database
    # Configuração para Render e Hostinger
    DB_TYPE = os.environ.get('DB_TYPE', 'mysql')
    DB_HOST = os.environ.get('DB_HOST', 'srv1124.hstgr.io')
    DB_PORT = int(os.environ.get('DB_PORT', 3306))
    DB_USER = os.environ.get('DB_USER', 'u951548013_gfinanceiro')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'quemsabe123!A')
    DB_NAME = os.environ.get('DB_NAME', 'u951548013_Gfinanceiro')
    SQLALCHEMY_DATABASE_URI = f'{DB_TYPE}+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    # Server
    SERVER_HOST = os.environ.get('SERVER_HOST', '0.0.0.0')
    SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000))
    
    # Security
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Config dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
