import pytest
from types import SimpleNamespace
from werkzeug.exceptions import Forbidden
from flask_login import login_user, logout_user

from app.models.user import User
from app.utils.permissions import (
    is_super_admin,
    is_company_admin,
    is_employee,
    is_viewer,
    can_access_customers_area,
    can_create_customer,
    can_edit_customer,
    can_delete_customer,
    can_access_users_area,
    can_create_service,
    can_delete_service,
    can_view_service,
    can_edit_service,
    can_update_service_status,
    can_upload_service_image,
    require_system_role,
    require_company_role,
)


def make_user(
    *,
    user_id=1,
    system_role="company_user",
    company_role=None,
    company_id=1,
):
    user = User(
        name=f"User {user_id}",
        email=f"user{user_id}@test.com",
        password_hash="hash",
        system_role=system_role,
        company_role=company_role,
        company_id=company_id,
        is_active=True,
        email_confirmed=True,
    )
    user.id = user_id
    return user


def make_service(*, company_id=1, assigned_to_id=None, created_by_id=None):
    return SimpleNamespace(
        company_id=company_id,
        assigned_to_id=assigned_to_id,
        created_by_id=created_by_id,
    )


def test_is_super_admin_true(app):
    user = make_user(user_id=1, system_role="super_admin", company_role=None)

    with app.test_request_context():
        login_user(user)
        assert is_super_admin() is True


def test_is_super_admin_false_for_company_admin(app):
    user = make_user(user_id=2, system_role="company_user", company_role="admin_empresa")

    with app.test_request_context():
        login_user(user)
        assert is_super_admin() is False


def test_is_company_admin_true(app):
    user = make_user(user_id=3, company_role="admin_empresa")

    with app.test_request_context():
        login_user(user)
        assert is_company_admin() is True


def test_is_company_admin_false_for_employee(app):
    user = make_user(user_id=4, company_role="funcionario")

    with app.test_request_context():
        login_user(user)
        assert is_company_admin() is False


def test_is_employee_true(app):
    user = make_user(user_id=5, company_role="funcionario")

    with app.test_request_context():
        login_user(user)
        assert is_employee() is True


def test_is_employee_false_for_viewer(app):
    user = make_user(user_id=6, company_role="visualizador")

    with app.test_request_context():
        login_user(user)
        assert is_employee() is False


def test_is_viewer_true(app):
    user = make_user(user_id=7, company_role="visualizador")

    with app.test_request_context():
        login_user(user)
        assert is_viewer() is True


def test_is_viewer_false_for_admin(app):
    user = make_user(user_id=8, company_role="admin_empresa")

    with app.test_request_context():
        login_user(user)
        assert is_viewer() is False


def test_can_access_customers_area_for_super_admin(app):
    user = make_user(user_id=9, system_role="super_admin")

    with app.test_request_context():
        login_user(user)
        assert can_access_customers_area() is True


def test_can_access_customers_area_for_company_admin(app):
    user = make_user(user_id=10, company_role="admin_empresa")

    with app.test_request_context():
        login_user(user)
        assert can_access_customers_area() is True


def test_can_access_customers_area_for_employee(app):
    user = make_user(user_id=11, company_role="funcionario")

    with app.test_request_context():
        login_user(user)
        assert can_access_customers_area() is True


def test_can_access_customers_area_denied_for_viewer(app):
    user = make_user(user_id=12, company_role="visualizador")

    with app.test_request_context():
        login_user(user)
        assert can_access_customers_area() is False


def test_can_create_customer_for_super_admin(app):
    user = make_user(user_id=13, system_role="super_admin")

    with app.test_request_context():
        login_user(user)
        assert can_create_customer() is True


def test_can_create_customer_for_company_admin(app):
    user = make_user(user_id=14, company_role="admin_empresa")

    with app.test_request_context():
        login_user(user)
        assert can_create_customer() is True


def test_can_create_customer_for_employee(app):
    user = make_user(user_id=15, company_role="funcionario")

    with app.test_request_context():
        login_user(user)
        assert can_create_customer() is True


def test_can_create_customer_denied_for_viewer(app):
    user = make_user(user_id=16, company_role="visualizador")

    with app.test_request_context():
        login_user(user)
        assert can_create_customer() is False


def test_can_edit_customer_for_super_admin(app):
    user = make_user(user_id=17, system_role="super_admin")

    with app.test_request_context():
        login_user(user)
        assert can_edit_customer() is True


def test_can_edit_customer_for_company_admin(app):
    user = make_user(user_id=18, company_role="admin_empresa")

    with app.test_request_context():
        login_user(user)
        assert can_edit_customer() is True


def test_can_edit_customer_for_employee(app):
    user = make_user(user_id=19, company_role="funcionario")

    with app.test_request_context():
        login_user(user)
        assert can_edit_customer() is True


def test_can_edit_customer_denied_for_viewer(app):
    user = make_user(user_id=20, company_role="visualizador")

    with app.test_request_context():
        login_user(user)
        assert can_edit_customer() is False


def test_can_delete_customer_for_super_admin(app):
    user = make_user(user_id=21, system_role="super_admin")

    with app.test_request_context():
        login_user(user)
        assert can_delete_customer() is True


def test_can_delete_customer_for_company_admin(app):
    user = make_user(user_id=22, company_role="admin_empresa")

    with app.test_request_context():
        login_user(user)
        assert can_delete_customer() is True


def test_can_delete_customer_denied_for_employee(app):
    user = make_user(user_id=23, company_role="funcionario")

    with app.test_request_context():
        login_user(user)
        assert can_delete_customer() is False


def test_can_delete_customer_denied_for_viewer(app):
    user = make_user(user_id=24, company_role="visualizador")

    with app.test_request_context():
        login_user(user)
        assert can_delete_customer() is False


def test_can_access_users_area_for_super_admin(app):
    user = make_user(user_id=25, system_role="super_admin")

    with app.test_request_context():
        login_user(user)
        assert can_access_users_area() is True


def test_can_access_users_area_for_company_admin(app):
    user = make_user(user_id=26, company_role="admin_empresa")

    with app.test_request_context():
        login_user(user)
        assert can_access_users_area() is True


def test_can_access_users_area_denied_for_employee(app):
    user = make_user(user_id=27, company_role="funcionario")

    with app.test_request_context():
        login_user(user)
        assert can_access_users_area() is False


def test_can_access_users_area_denied_for_viewer(app):
    user = make_user(user_id=28, company_role="visualizador")

    with app.test_request_context():
        login_user(user)
        assert can_access_users_area() is False


def test_can_create_service_for_super_admin(app):
    user = make_user(user_id=29, system_role="super_admin")

    with app.test_request_context():
        login_user(user)
        assert can_create_service() is True


def test_can_create_service_for_company_admin(app):
    user = make_user(user_id=30, company_role="admin_empresa")

    with app.test_request_context():
        login_user(user)
        assert can_create_service() is True


def test_can_create_service_for_employee(app):
    user = make_user(user_id=31, company_role="funcionario")

    with app.test_request_context():
        login_user(user)
        assert can_create_service() is True


def test_can_create_service_for_viewer(app):
    user = make_user(user_id=32, company_role="visualizador")

    with app.test_request_context():
        login_user(user)
        assert can_create_service() is True


def test_can_delete_service_for_super_admin(app):
    user = make_user(user_id=33, system_role="super_admin")

    with app.test_request_context():
        login_user(user)
        assert can_delete_service() is True


def test_can_delete_service_for_company_admin(app):
    user = make_user(user_id=34, company_role="admin_empresa")

    with app.test_request_context():
        login_user(user)
        assert can_delete_service() is True


def test_can_delete_service_denied_for_employee(app):
    user = make_user(user_id=35, company_role="funcionario")

    with app.test_request_context():
        login_user(user)
        assert can_delete_service() is False


def test_can_delete_service_denied_for_viewer(app):
    user = make_user(user_id=36, company_role="visualizador")

    with app.test_request_context():
        login_user(user)
        assert can_delete_service() is False


def test_can_view_service_denied_for_anonymous(app):
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    with app.test_request_context():
        assert can_view_service(service) is False


def test_can_view_service_allowed_for_super_admin():
    user = make_user(user_id=37, system_role="super_admin", company_id=999)
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    assert can_view_service(service, user=user) is True


def test_can_view_service_denied_for_different_company():
    user = make_user(user_id=38, company_role="admin_empresa", company_id=2)
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    assert can_view_service(service, user=user) is False


def test_can_view_service_allowed_for_company_admin_same_company():
    user = make_user(user_id=39, company_role="admin_empresa", company_id=1)
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    assert can_view_service(service, user=user) is True


def test_can_view_service_allowed_for_employee_when_assigned():
    user = make_user(user_id=40, company_role="funcionario", company_id=1)
    service = make_service(company_id=1, assigned_to_id=40, created_by_id=20)

    assert can_view_service(service, user=user) is True


def test_can_view_service_denied_for_employee_when_not_assigned():
    user = make_user(user_id=41, company_role="funcionario", company_id=1)
    service = make_service(company_id=1, assigned_to_id=999, created_by_id=20)

    assert can_view_service(service, user=user) is False


def test_can_view_service_allowed_for_viewer_when_created_by_him():
    user = make_user(user_id=42, company_role="visualizador", company_id=1)
    service = make_service(company_id=1, assigned_to_id=999, created_by_id=42)

    assert can_view_service(service, user=user) is True


def test_can_view_service_denied_for_viewer_when_not_created_by_him():
    user = make_user(user_id=43, company_role="visualizador", company_id=1)
    service = make_service(company_id=1, assigned_to_id=999, created_by_id=77)

    assert can_view_service(service, user=user) is False


def test_can_edit_service_denied_for_anonymous(app):
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    with app.test_request_context():
        assert can_edit_service(service) is False


def test_can_edit_service_allowed_for_super_admin():
    user = make_user(user_id=44, system_role="super_admin", company_id=999)
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    assert can_edit_service(service, user=user) is True


def test_can_edit_service_denied_for_different_company():
    user = make_user(user_id=45, company_role="admin_empresa", company_id=2)
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    assert can_edit_service(service, user=user) is False


def test_can_edit_service_allowed_for_company_admin_same_company():
    user = make_user(user_id=46, company_role="admin_empresa", company_id=1)
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    assert can_edit_service(service, user=user) is True


def test_can_edit_service_allowed_for_employee_when_assigned():
    user = make_user(user_id=47, company_role="funcionario", company_id=1)
    service = make_service(company_id=1, assigned_to_id=47, created_by_id=20)

    assert can_edit_service(service, user=user) is True


def test_can_edit_service_denied_for_employee_when_not_assigned():
    user = make_user(user_id=48, company_role="funcionario", company_id=1)
    service = make_service(company_id=1, assigned_to_id=999, created_by_id=20)

    assert can_edit_service(service, user=user) is False


def test_can_edit_service_denied_for_viewer():
    user = make_user(user_id=49, company_role="visualizador", company_id=1)
    service = make_service(company_id=1, assigned_to_id=999, created_by_id=49)

    assert can_edit_service(service, user=user) is False


def test_can_update_service_status_denied_for_anonymous(app):
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    with app.test_request_context():
        assert can_update_service_status(service) is False


def test_can_update_service_status_allowed_for_super_admin():
    user = make_user(user_id=50, system_role="super_admin", company_id=999)
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    assert can_update_service_status(service, user=user) is True


def test_can_update_service_status_denied_for_different_company():
    user = make_user(user_id=51, company_role="admin_empresa", company_id=2)
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    assert can_update_service_status(service, user=user) is False


def test_can_update_service_status_allowed_for_company_admin_same_company():
    user = make_user(user_id=52, company_role="admin_empresa", company_id=1)
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    assert can_update_service_status(service, user=user) is True


def test_can_update_service_status_allowed_for_employee_when_assigned():
    user = make_user(user_id=53, company_role="funcionario", company_id=1)
    service = make_service(company_id=1, assigned_to_id=53, created_by_id=20)

    assert can_update_service_status(service, user=user) is True


def test_can_update_service_status_denied_for_employee_when_not_assigned():
    user = make_user(user_id=54, company_role="funcionario", company_id=1)
    service = make_service(company_id=1, assigned_to_id=999, created_by_id=20)

    assert can_update_service_status(service, user=user) is False


def test_can_update_service_status_denied_for_viewer():
    user = make_user(user_id=55, company_role="visualizador", company_id=1)
    service = make_service(company_id=1, assigned_to_id=999, created_by_id=55)

    assert can_update_service_status(service, user=user) is False


def test_can_upload_service_image_denied_for_anonymous(app):
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    with app.test_request_context():
        assert can_upload_service_image(service) is False


def test_can_upload_service_image_allowed_for_super_admin():
    user = make_user(user_id=56, system_role="super_admin", company_id=999)
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    assert can_upload_service_image(service, user=user) is True


def test_can_upload_service_image_denied_for_different_company():
    user = make_user(user_id=57, company_role="admin_empresa", company_id=2)
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    assert can_upload_service_image(service, user=user) is False


def test_can_upload_service_image_allowed_for_company_admin_same_company():
    user = make_user(user_id=58, company_role="admin_empresa", company_id=1)
    service = make_service(company_id=1, assigned_to_id=10, created_by_id=20)

    assert can_upload_service_image(service, user=user) is True


def test_can_upload_service_image_allowed_for_employee_when_assigned():
    user = make_user(user_id=59, company_role="funcionario", company_id=1)
    service = make_service(company_id=1, assigned_to_id=59, created_by_id=20)

    assert can_upload_service_image(service, user=user) is True


def test_can_upload_service_image_denied_for_employee_when_not_assigned():
    user = make_user(user_id=60, company_role="funcionario", company_id=1)
    service = make_service(company_id=1, assigned_to_id=999, created_by_id=20)

    assert can_upload_service_image(service, user=user) is False


def test_can_upload_service_image_denied_for_viewer():
    user = make_user(user_id=61, company_role="visualizador", company_id=1)
    service = make_service(company_id=1, assigned_to_id=999, created_by_id=61)

    assert can_upload_service_image(service, user=user) is False


def test_require_system_role_allows_matching_role(app):
    @require_system_role("super_admin")
    def protected_view():
        return "ok"

    user = make_user(user_id=62, system_role="super_admin")

    with app.test_request_context():
        login_user(user)
        assert protected_view() == "ok"


def test_require_system_role_denies_wrong_role(app):
    @require_system_role("super_admin")
    def protected_view():
        return "ok"

    user = make_user(user_id=63, system_role="company_user", company_role="admin_empresa")

    with app.test_request_context():
        login_user(user)
        with pytest.raises(Forbidden):
            protected_view()


def test_require_system_role_denies_anonymous(app):
    @require_system_role("super_admin")
    def protected_view():
        return "ok"

    with app.test_request_context():
        with pytest.raises(Forbidden):
            protected_view()


def test_require_company_role_allows_matching_company_role(app):
    @require_company_role("admin_empresa", "funcionario")
    def protected_view():
        return "ok"

    user = make_user(user_id=64, system_role="company_user", company_role="admin_empresa")

    with app.test_request_context():
        login_user(user)
        assert protected_view() == "ok"


def test_require_company_role_allows_super_admin(app):
    @require_company_role("admin_empresa")
    def protected_view():
        return "ok"

    user = make_user(user_id=65, system_role="super_admin", company_role=None)

    with app.test_request_context():
        login_user(user)
        assert protected_view() == "ok"


def test_require_company_role_denies_wrong_company_role(app):
    @require_company_role("admin_empresa")
    def protected_view():
        return "ok"

    user = make_user(user_id=66, system_role="company_user", company_role="visualizador")

    with app.test_request_context():
        login_user(user)
        with pytest.raises(Forbidden):
            protected_view()


def test_require_company_role_denies_anonymous(app):
    @require_company_role("admin_empresa")
    def protected_view():
        return "ok"

    with app.test_request_context():
        with pytest.raises(Forbidden):
            protected_view()