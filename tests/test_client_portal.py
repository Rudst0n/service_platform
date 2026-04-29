from app.extensions import db
from app.models.service import Service


def portal_login(client, email, password):
    return client.post(
        "/client/login",
        data={
            "email": email,
            "password": password,
        },
        follow_redirects=True,
    )


def portal_logout(client):
    return client.post("/client/logout", follow_redirects=True)


def test_client_portal_login_page_loads(client):
    response = client.get("/client/login")
    assert response.status_code == 200


def test_client_portal_dashboard_requires_login(client):
    response = client.get("/client/dashboard", follow_redirects=False)
    assert response.status_code in (301, 302, 303, 308, 401, 403)


def test_client_portal_new_service_requires_login(client):
    response = client.get("/client/services/new", follow_redirects=False)
    assert response.status_code in (301, 302, 303, 308, 401, 403)


def test_client_portal_customer_can_login(client, portal_customer):
    response = portal_login(client, "portal@teste.com", "Senha@123")
    assert response.status_code == 200


def test_client_portal_login_fails_with_wrong_password(client, portal_customer):
    response = portal_login(client, "portal@teste.com", "SenhaErrada@123")
    assert response.status_code == 200


def test_client_portal_dashboard_loads_after_login(client, portal_customer):
    login_response = portal_login(client, "portal@teste.com", "Senha@123")
    assert login_response.status_code == 200

    response = client.get("/client/dashboard", follow_redirects=True)
    assert response.status_code == 200


def test_client_portal_customer_can_logout(client, portal_customer):
    login_response = portal_login(client, "portal@teste.com", "Senha@123")
    assert login_response.status_code == 200

    response = portal_logout(client)
    assert response.status_code == 200


def test_client_portal_customer_can_open_new_service_page(client, portal_customer):
    login_response = portal_login(client, "portal@teste.com", "Senha@123")
    assert login_response.status_code == 200

    response = client.get("/client/services/new", follow_redirects=True)
    assert response.status_code == 200


def test_client_portal_customer_can_create_service(client, portal_customer, admin_user):
    login_response = portal_login(client, "portal@teste.com", "Senha@123")
    assert login_response.status_code == 200

    response = client.post(
        "/client/services/new",
        data={
            "name": "Solicitação via Portal",
            "description": "Solicitação criada pelo cliente no portal",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with client.application.app_context():
        saved = Service.query.filter_by(name="Solicitação via Portal").first()

        assert saved is not None
        assert saved.customer_id == portal_customer.id
        assert saved.company_id == portal_customer.company_id
        assert saved.status == "orcamento"


def test_client_portal_new_service_requires_name(client, portal_customer):
    login_response = portal_login(client, "portal@teste.com", "Senha@123")
    assert login_response.status_code == 200

    response = client.post(
        "/client/services/new",
        data={
            "name": "",
            "description": "Sem título",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with client.application.app_context():
        saved = Service.query.filter_by(description="Sem título").first()
        assert saved is None