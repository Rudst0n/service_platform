from functools import wraps

from flask import abort
from flask_login import current_user


def is_super_admin():
    return current_user.is_authenticated and current_user.system_role == "super_admin"


def is_company_admin():
    return current_user.is_authenticated and current_user.company_role == "admin_empresa"


def is_employee():
    return current_user.is_authenticated and current_user.company_role == "funcionario"


def is_viewer():
    return current_user.is_authenticated and current_user.company_role == "visualizador"


def can_access_customers_area():
    if is_super_admin():
        return True
    return is_company_admin() or is_employee()


def can_create_customer():
    if is_super_admin():
        return True
    return is_company_admin() or is_employee()


def can_edit_customer():
    if is_super_admin():
        return True
    return is_company_admin() or is_employee()


def can_delete_customer():
    if is_super_admin():
        return True
    return is_company_admin()


def can_access_users_area():
    if is_super_admin():
        return True
    return is_company_admin()


def can_create_service():
    if is_super_admin():
        return True
    return is_company_admin() or is_employee() or is_viewer()


def can_delete_service():
    if is_super_admin():
        return True
    return is_company_admin()


def can_view_service(service, user=None):
    user = user or current_user

    if not user.is_authenticated:
        return False

    if user.system_role == "super_admin":
        return True

    if user.company_id != service.company_id:
        return False

    if user.company_role == "admin_empresa":
        return True

    if user.company_role == "funcionario":
        return service.assigned_to_id == user.id

    if user.company_role == "visualizador":
        return service.created_by_id == user.id

    return False


def can_edit_service(service, user=None):
    user = user or current_user

    if not user.is_authenticated:
        return False

    if user.system_role == "super_admin":
        return True

    if user.company_id != service.company_id:
        return False

    if user.company_role == "admin_empresa":
        return True

    if user.company_role == "funcionario":
        return service.assigned_to_id == user.id

    return False


def can_update_service_status(service, user=None):
    user = user or current_user

    if not user.is_authenticated:
        return False

    if user.system_role == "super_admin":
        return True

    if user.company_id != service.company_id:
        return False

    if user.company_role == "admin_empresa":
        return True

    if user.company_role == "funcionario":
        return service.assigned_to_id == user.id

    return False


def can_upload_service_image(service, user=None):
    user = user or current_user

    if not user.is_authenticated:
        return False

    if user.system_role == "super_admin":
        return True

    if user.company_id != service.company_id:
        return False

    if user.company_role == "admin_empresa":
        return True

    if user.company_role == "funcionario":
        return service.assigned_to_id == user.id

    return False


def require_system_role(role_name):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)

            if current_user.system_role != role_name:
                abort(403)

            return view(*args, **kwargs)

        return wrapped

    return decorator


def require_company_role(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)

            if current_user.system_role == "super_admin":
                return view(*args, **kwargs)

            if current_user.company_role not in roles:
                abort(403)

            return view(*args, **kwargs)

        return wrapped

    return decorator