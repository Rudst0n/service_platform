from functools import wraps

from flask import flash, redirect, url_for
from flask_login import current_user


def _resolve_user(user=None):
    return user if user is not None else current_user


def has_company_role(*roles):
    user = _resolve_user()
    if not user.is_authenticated:
        return False

    return user.company_role in roles


def has_system_role(*roles):
    user = _resolve_user()
    if not user.is_authenticated:
        return False

    return user.system_role in roles


def is_super_admin(user=None):
    user = _resolve_user(user)
    return user.is_authenticated and user.system_role == "super_admin"


def is_company_admin(user=None):
    user = _resolve_user(user)
    return user.is_authenticated and user.company_role == "admin_empresa"


def is_employee(user=None):
    user = _resolve_user(user)
    return user.is_authenticated and user.company_role == "funcionario"


def company_access_is_active(user=None):
    user = _resolve_user(user)

    if not user.is_authenticated:
        return False

    if is_super_admin(user):
        return True

    if not user.company:
        return False

    return user.company.is_access_allowed


def can_manage_company_users(user=None):
    user = _resolve_user(user)
    return user.is_authenticated and (is_super_admin(user) or is_company_admin(user))


def can_manage_company_data(user=None):
    user = _resolve_user(user)
    return user.is_authenticated and (is_super_admin(user) or is_company_admin(user))


def can_create_customer(user=None):
    user = _resolve_user(user)
    return user.is_authenticated and (
        is_super_admin(user) or is_company_admin(user) or is_employee(user)
    )


def can_edit_customer(user=None):
    return can_create_customer(user)


def can_create_service(user=None):
    user = _resolve_user(user)
    return user.is_authenticated and (
        is_super_admin(user) or is_company_admin(user) or is_employee(user)
    )


def can_view_service(service, user=None):
    user = _resolve_user(user)

    if not user.is_authenticated or service is None:
        return False

    if is_super_admin(user):
        return True

    if service.company_id != user.company_id:
        return False

    if is_company_admin(user):
        return True

    if is_employee(user):
        return service.assigned_to_id == user.id

    return False


def can_edit_service(service, user=None):
    user = _resolve_user(user)

    if not can_view_service(service, user):
        return False

    if is_super_admin(user) or is_company_admin(user):
        return True

    if is_employee(user):
        return service.assigned_to_id == user.id

    return False


def can_update_service_status(service, user=None):
    return can_edit_service(service, user)


def can_upload_service_image(service, user=None):
    return can_edit_service(service, user)


def can_delete_service(user=None):
    user = _resolve_user(user)
    return user.is_authenticated and (is_super_admin(user) or is_company_admin(user))


def can_manage_company_record(user=None):
    user = _resolve_user(user)
    return user.is_authenticated and is_super_admin(user)


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