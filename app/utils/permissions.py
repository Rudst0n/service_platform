from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user


def require_company_role(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))

            if current_user.company_role not in roles:
                flash('Você não tem permissão para acessar esta funcionalidade.', 'danger')
                return redirect(url_for('main.dashboard'))

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_system_role(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))

            if current_user.system_role not in roles:
                flash('Acesso restrito.', 'danger')
                return redirect(url_for('main.dashboard'))

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_active_company():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.company or not current_user.company.is_access_allowed:
                flash('Sua empresa não possui acesso ativo.', 'warning')
                return redirect(url_for('main.dashboard'))

            return func(*args, **kwargs)
        return wrapper
    return decorator