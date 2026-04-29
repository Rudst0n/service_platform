from tests.helpers import login


def test_services_route_requires_login(client):
    response = client.get("/services/", follow_redirects=False)
    assert response.status_code in (301, 302, 303, 308, 401, 403)


def test_new_service_route_requires_login(client):
    response = client.get("/services/new", follow_redirects=False)
    assert response.status_code in (301, 302, 303, 308, 401, 403)


def test_admin_can_open_services_list_route(client, admin_user):
    login(client, "admin@teste.com", "Senha@123")

    response = client.get("/services/", follow_redirects=True)
    assert response.status_code == 200
    assert b"servi" in response.data.lower()


def test_admin_can_open_new_service_route(client, admin_user):
    login(client, "admin@teste.com", "Senha@123")

    response = client.get("/services/new", follow_redirects=True)
    assert response.status_code == 200


def test_visualizador_can_open_services_list_route(client, visualizador_user):
    login(client, "visualizador@teste.com", "Senha@123")

    response = client.get("/services/", follow_redirects=True)
    assert response.status_code == 200


def test_visualizador_cannot_open_new_service_route(client, visualizador_user):
    login(client, "visualizador@teste.com", "Senha@123")

    response = client.get("/services/new", follow_redirects=False)
    assert response.status_code in (302, 303, 308, 403)


def test_super_admin_can_open_services_list_route(client, super_admin_user):
    login(client, "superadmin@teste.com", "Senha@123")

    response = client.get("/services/", follow_redirects=True)
    assert response.status_code == 200


def test_super_admin_can_open_new_service_route(client, super_admin_user):
    login(client, "superadmin@teste.com", "Senha@123")

    response = client.get("/services/new", follow_redirects=True)
    assert response.status_code == 200


def test_services_list_route_is_stable_after_multiple_requests(client, admin_user):
    login(client, "admin@teste.com", "Senha@123")

    response1 = client.get("/services/", follow_redirects=True)
    response2 = client.get("/services/", follow_redirects=True)

    assert response1.status_code == 200
    assert response2.status_code == 200


def test_new_service_route_is_stable_after_multiple_requests(client, admin_user):
    login(client, "admin@teste.com", "Senha@123")

    response1 = client.get("/services/new", follow_redirects=True)
    response2 = client.get("/services/new", follow_redirects=True)

    assert response1.status_code == 200
    assert response2.status_code == 200