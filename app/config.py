import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f"sqlite:///{BASE_DIR / 'instance' / 'app.db'}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 5 * 1024 * 1024))

    APP_NAME = os.getenv('APP_NAME', 'ServHub')
    APP_SLOGAN = os.getenv('APP_SLOGAN', 'Organização que acompanha seu serviço')
    SUPPORT_WHATSAPP = os.getenv('SUPPORT_WHATSAPP', '(41) 99999-9999')
    SUPPORT_EMAIL = os.getenv('SUPPORT_EMAIL', 'contato@servhub.com')
    SUPPORT_INSTAGRAM = os.getenv('SUPPORT_INSTAGRAM', '@servhub.oficial')

    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT', 'change-me-too')
    REQUIRE_EMAIL_CONFIRMATION = os.getenv('REQUIRE_EMAIL_CONFIRMATION', '0') == '1'
    TRIAL_DAYS = int(os.getenv('TRIAL_DAYS', '7'))

    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_SAMESITE = 'Lax'


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
