from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def has_company_role(*roles):
    if not current_user.is_authenticated:
        return False

    return current_user.company_role in roles


def has_system_role(*roles):
    if not current_user.is_authenticated:
        return False

    return current_user.system_role in roles


def company_access_is_active():
    if not current_user.is_authenticated:
        return False

    if not current_user.company:
        return False

    return current_user.company.is_access_allowed


def require_company_role(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))

            if not has_company_role(*roles):
                flash("Você não tem permissão para acessar esta funcionalidade.", "danger")
                return redirect(url_for("main.dashboard"))

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_system_role(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))

            if not has_system_role(*roles):
                flash("Acesso restrito.", "danger")
                return redirect(url_for("main.dashboard"))

            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_active_company():
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not company_access_is_active():
                flash("Sua empresa não possui acesso ativo.", "warning")
                return redirect(url_for("main.dashboard"))

            return func(*args, **kwargs)

        return wrapper

    return decorator