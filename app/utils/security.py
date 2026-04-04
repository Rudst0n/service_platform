import hashlib
import re

from flask import current_app
from itsdangerous import URLSafeTimedSerializer

EMAIL_REGEX = re.compile(r'^[^\s@]+@[^\s@]+\.[^\s@]+$')


def normalize_text(value):
    if not value:
        return ''
    return ' '.join(value.strip().split())


def only_digits(value):
    if not value:
        return None
    digits = ''.join(filter(str.isdigit, str(value)))
    return digits or None


def format_cpf(value):
    value = only_digits(value)
    if not value:
        return None
    if len(value) != 11:
        return value
    return f'{value[:3]}.{value[3:6]}.{value[6:9]}-{value[9:]}'


def format_cnpj(value):
    value = only_digits(value)
    if not value:
        return None
    if len(value) != 14:
        return value
    return f'{value[:2]}.{value[2:5]}.{value[5:8]}/{value[8:12]}-{value[12:]}'


def is_valid_email(email):
    return bool(email and EMAIL_REGEX.match(email))


def is_strong_password(password):
    if len(password) < 8:
        return False, 'A senha deve ter pelo menos 8 caracteres.'
    if not re.search(r'[A-Z]', password):
        return False, 'A senha deve ter pelo menos uma letra maiúscula.'
    if not re.search(r'[a-z]', password):
        return False, 'A senha deve ter pelo menos uma letra minúscula.'
    if not re.search(r'\d', password):
        return False, 'A senha deve ter pelo menos um número.'
    return True, None


def get_password_fingerprint(password_hash):
    if not password_hash:
        return None
    return hashlib.sha256(password_hash.encode('utf-8')).hexdigest()[:16]


def build_user_token_payload(user, purpose):
    return {
        'user_id': user.id,
        'email': user.email,
        'purpose': purpose,
        'pwd': get_password_fingerprint(user.password_hash),
    }


def generate_token(payload, salt):
    serializer = URLSafeTimedSerializer(
        secret_key=current_app.config['SECRET_KEY'],
        salt=current_app.config.get('SECURITY_PASSWORD_SALT', 'change-me-too'),
    )
    return serializer.dumps(payload, salt=salt)


def read_token(token, salt, max_age=3600):
    serializer = URLSafeTimedSerializer(
        secret_key=current_app.config['SECRET_KEY'],
        salt=current_app.config.get('SECURITY_PASSWORD_SALT', 'change-me-too'),
    )
    return serializer.loads(token, salt=salt, max_age=max_age)


def validate_user_token_payload(user, payload, expected_purpose):
    if not payload:
        return False

    if payload.get('user_id') != user.id:
        return False

    if payload.get('email') != user.email:
        return False

    if payload.get('purpose') != expected_purpose:
        return False

    current_pwd_fingerprint = get_password_fingerprint(user.password_hash)
    if payload.get('pwd') != current_pwd_fingerprint:
        return False

    return True