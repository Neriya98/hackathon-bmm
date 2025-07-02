import os
from datetime import timedelta

class Config:
    """Configuration de base pour SecureDeal"""
    
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///securedeal.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }
    
    # JWT Configuration
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # Bitcoin Configuration
    BITCOIN_NETWORK = os.environ.get('BITCOIN_NETWORK') or 'signet'
    BITCOIN_RPC_URL = os.environ.get('BITCOIN_RPC_URL') or 'https://blockstream.info/signet/api/'
    BITCOIN_RPC_USER = os.environ.get('BITCOIN_RPC_USER')
    BITCOIN_RPC_PASSWORD = os.environ.get('BITCOIN_RPC_PASSWORD')
    DEFAULT_FEE_RATE = int(os.environ.get('DEFAULT_FEE_RATE') or 10)  # sat/vB
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or MAIL_USERNAME
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = REDIS_URL
    RATELIMIT_DEFAULT = "100 per hour"
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    
    # Application Settings
    CONTRACTS_PER_PAGE = 20
    MAX_PARTICIPANTS_PER_CONTRACT = 15
    CONTRACT_EXPIRY_DAYS = 30
    INVITATION_EXPIRY_HOURS = 72
    
    # Security Headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE')
    
    # Development settings
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///securedeal_dev.db'
    
    # Relaxed security for development
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    RATELIMIT_DEFAULT = "1000 per hour"
    
    # Email debug
    MAIL_SUPPRESS_SEND = False
    MAIL_DEBUG = True


class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Fast token expiry for testing
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=30)
    
    # Disable email sending in tests
    MAIL_SUPPRESS_SEND = True
    
    # Use sync tasks in tests
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True


class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    
    # Production database (PostgreSQL recommandé)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://securedeal:password@localhost/securedeal_prod'
    
    # Strict security
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'pool_size': 20,
        'max_overflow': 30
    }
    
    # Production logging
    LOG_LEVEL = 'WARNING'
    
    # Stricter rate limiting
    RATELIMIT_DEFAULT = "50 per hour"


class DockerConfig(Config):
    """Configuration pour Docker"""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://securedeal:securedeal@db:5432/securedeal'
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://redis:6379/0'


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Retourne la configuration basée sur la variable d'environnement"""
    config_name = os.environ.get('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])
