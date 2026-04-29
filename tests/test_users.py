from app.extensions import db
from app.models.user import User
from tests.helpers import login


def test_users_page_requires_login(client):
    response = client.get("/users/", follow_redirects=False)
    assert response.status_code in (301, 302, 303, 308, 401, 403)


def test_admin_can_access_users_page(client, admin_user):
    login(client, "admin@teste.com", "Senha@123")

    response = client.get("/users/", follow_redirects=True)
    assert response.status_code == 200


def test_visualizador_cannot_access_users_page(client, visualizador_user):
    login(client, "visualizador@teste.com", "Senha@123")

    response = client.get("/users/", follow_redirects=False)
    assert response.status_code in (302, 303, 308, 403)


def test_admin_can_access_new_user_page(client, admin_user):
    login(client, "admin@teste.com", "Senha@123")

    response = client.get("/users/new", follow_redirects=True)
    assert response.status_code == 200


def test_super_admin_can_access_users_page(client, super_admin_user):
    login(client, "superadmin@teste.com", "Senha@123")

    response = client.get("/users/", follow_redirects=True)
    assert response.status_code == 200


def test_user_model_can_be_created(app, company):
    with app.app_context():
        user = User(
            name="Funcionario Teste",
            email="funcionario@teste.com",
            cpf="123.456.789-30",
            system_role="company_user",
            company_role="funcionario",
            company_id=company.id,
            is_active=True,
            email_confirmed=True,
            must_change_password=False,
        )
        user.set_password("Senha@123")

        db.session.add(user)
        db.session.commit()

        saved = User.query.filter_by(email="funcionario@teste.com").first()

        assert saved is not None
        assert saved.name == "Funcionario Teste"
        assert saved.company_role == "funcionario"


def test_user_password_is_hashed(app, company):
    with app.app_context():
        user = User(
            name="Hash Teste",
            email="hash@teste.com",
            cpf="123.456.789-31",
            system_role="company_user",
            company_role="funcionario",
            company_id=company.id,
            is_active=True,
            email_confirmed=True,
            must_change_password=False,
        )
        user.set_password("Senha@123")

        db.session.add(user)
        db.session.commit()

        saved = User.query.filter_by(email="hash@teste.com").first()

        assert saved is not None
        assert saved.password_hash != "Senha@123"
        assert saved.check_password("Senha@123") is True


def test_duplicate_user_email_behavior(app, company):
    with app.app_context():
        user1 = User(
            name="Usuario 1",
            email="duplicado.user@teste.com",
            cpf="123.456.789-32",
            system_role="company_user",
            company_role="funcionario",
            company_id=company.id,
            is_active=True,
            email_confirmed=True,
            must_change_password=False,
        )
        user1.set_password("Senha@123")

        user2 = User(
            name="Usuario 2",
            email="duplicado.user@teste.com",
            cpf="123.456.789-33",
            system_role="company_user",
            company_role="funcionario",
            company_id=company.id,
            is_active=True,
            email_confirmed=True,
            must_change_password=False,
        )
        user2.set_password("Senha@123")

        db.session.add(user1)
        db.session.commit()

        db.session.add(user2)

        try:
            db.session.commit()
            duplicate_allowed = True
        except Exception:
            db.session.rollback()
            duplicate_allowed = False

        assert duplicate_allowed is False


def test_duplicate_user_cpf_behavior(app, company):
    with app.app_context():
        user1 = User(
            name="Usuario CPF 1",
            email="cpf1@teste.com",
            cpf="123.456.789-34",
            system_role="company_user",
            company_role="funcionario",
            company_id=company.id,
            is_active=True,
            email_confirmed=True,
            must_change_password=False,
        )
        user1.set_password("Senha@123")

        user2 = User(
            name="Usuario CPF 2",
            email="cpf2@teste.com",
            cpf="123.456.789-34",
            system_role="company_user",
            company_role="funcionario",
            company_id=company.id,
            is_active=True,
            email_confirmed=True,
            must_change_password=False,
        )
        user2.set_password("Senha@123")

        db.session.add(user1)
        db.session.commit()

        db.session.add(user2)

        try:
            db.session.commit()
            duplicate_allowed = True
        except Exception:
            db.session.rollback()
            duplicate_allowed = False

        assert duplicate_allowed is False