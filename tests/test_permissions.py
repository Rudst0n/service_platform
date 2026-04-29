from tests.helpers import login


def test_visualizador_cannot_access_users_page(client, visualizador_user):
    login(client, "visualizador@teste.com", "Senha@123")

    response = client.get("/users/", follow_redirects=False)
    assert response.status_code in (302, 303, 308, 403)


def test_visualizador_cannot_access_new_customer_page(client, visualizador_user):
    login(client, "visualizador@teste.com", "Senha@123")

    response = client.get("/customers/new", follow_redirects=False)
    assert response.status_code in (302, 303, 308, 403)


def test_admin_company_can_access_users_page(client, admin_user):
    login(client, "admin@teste.com", "Senha@123")

    response = client.get("/users/", follow_redirects=True)
    assert response.status_code == 200


def test_super_admin_can_access_companies_page(client, super_admin_user):
    login(client, "superadmin@teste.com", "Senha@123")

    response = client.get("/admin/companies", follow_redirects=True)
    assert response.status_code == 200