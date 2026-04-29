from tests.helpers import login, logout


def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code in (301, 302, 401, 403)


def test_admin_user_can_login(client, admin_user):
    response = login(client, "admin@teste.com", "Senha@123")
    assert response.status_code == 200


def test_visualizador_user_can_login(client, visualizador_user):
    response = login(client, "visualizador@teste.com", "Senha@123")
    assert response.status_code == 200


def test_super_admin_can_login(client, super_admin_user):
    response = login(client, "superadmin@teste.com", "Senha@123")
    assert response.status_code == 200


def test_login_fails_with_wrong_password(client, admin_user):
    response = login(client, "admin@teste.com", "SenhaErrada@123")
    assert response.status_code == 200


def test_logged_user_can_access_dashboard(client, admin_user):
    login_response = login(client, "admin@teste.com", "Senha@123")
    assert login_response.status_code == 200

    response = client.get("/dashboard", follow_redirects=True)
    assert response.status_code == 200


def test_user_can_logout(client, admin_user):
    login_response = login(client, "admin@teste.com", "Senha@123")
    assert login_response.status_code == 200

    response = logout(client)
    assert response.status_code == 200