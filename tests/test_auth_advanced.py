from datetime import datetime, timedelta

from app.extensions import db
from app.models.company import CompanyStatus


def advanced_login(client, login_value, password):
    return client.post(
        "/auth/login",
        data={
            "login": login_value,
            "password": password,
        },
        follow_redirects=True,
    )


def ensure_logout(client):
    client.post("/auth/logout", follow_redirects=True)


def test_inactive_user_cannot_login(client, app, admin_user):
    ensure_logout(client)

    with app.app_context():
        admin_user.is_active = False
        db.session.commit()

    response = advanced_login(client, "admin@teste.com", "Senha@123")
    assert response.status_code == 200


def test_unconfirmed_email_user_cannot_login_when_required(client, app, admin_user):
    ensure_logout(client)

    with app.app_context():
        admin_user.email_confirmed = False
        db.session.commit()

    app.config["REQUIRE_EMAIL_CONFIRMATION"] = True

    response = advanced_login(client, "admin@teste.com", "Senha@123")
    assert response.status_code == 200


def test_user_can_login_when_email_confirmation_disabled(client, app, admin_user):
    ensure_logout(client)

    with app.app_context():
        admin_user.email_confirmed = False
        db.session.commit()

    app.config["REQUIRE_EMAIL_CONFIRMATION"] = False

    response = advanced_login(client, "admin@teste.com", "Senha@123")
    assert response.status_code == 200


def test_blocked_company_user_cannot_login(client, app, admin_user, company):
    ensure_logout(client)

    with app.app_context():
        company.status = CompanyStatus.BLOCKED
        db.session.commit()

    response = advanced_login(client, "admin@teste.com", "Senha@123")
    assert response.status_code == 200


def test_inactive_company_user_cannot_login(client, app, admin_user, company):
    ensure_logout(client)

    with app.app_context():
        company.status = CompanyStatus.INACTIVE
        db.session.commit()

    response = advanced_login(client, "admin@teste.com", "Senha@123")
    assert response.status_code == 200


def test_pending_company_user_cannot_login(client, app, admin_user, company):
    ensure_logout(client)

    with app.app_context():
        company.status = CompanyStatus.PENDING
        db.session.commit()

    response = advanced_login(client, "admin@teste.com", "Senha@123")
    assert response.status_code == 200


def test_user_with_must_change_password_redirects(client, app, admin_user):
    ensure_logout(client)

    with app.app_context():
        admin_user.must_change_password = True
        db.session.commit()

    response = advanced_login(client, "admin@teste.com", "Senha@123")
    assert response.status_code == 200


def test_locked_user_cannot_login(client, app, admin_user):
    ensure_logout(client)

    with app.app_context():
        admin_user.locked_until = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()

    response = advanced_login(client, "admin@teste.com", "Senha@123")
    assert response.status_code == 200


def test_failed_login_attempts_can_lock_user(client, app, admin_user):
    ensure_logout(client)

    app.config["LOGIN_MAX_ATTEMPTS"] = 2
    app.config["LOGIN_LOCK_MINUTES"] = 1

    advanced_login(client, "admin@teste.com", "SenhaErrada")
    advanced_login(client, "admin@teste.com", "SenhaErrada")

    with app.app_context():
        refreshed = db.session.get(type(admin_user), admin_user.id)
        assert refreshed.locked_until is not None


def test_login_with_cpf_works(client):
    ensure_logout(client)

    response = advanced_login(client, "123.456.789-00", "Senha@123")
    assert response.status_code == 200