from tests.helpers import login


def test_admin_companies_page_requires_login(client):
    response = client.get("/admin/companies", follow_redirects=False)
    assert response.status_code in (301, 302, 303, 308, 401, 403)


def test_super_admin_can_access_companies_page(client, super_admin_user):
    login(client, "superadmin@teste.com", "Senha@123")

    response = client.get("/admin/companies", follow_redirects=True)
    assert response.status_code == 200


def test_company_admin_cannot_access_companies_page(client, admin_user):
    login(client, "admin@teste.com", "Senha@123")

    response = client.get("/admin/companies", follow_redirects=False)
    assert response.status_code in (302, 303, 308, 403)


def test_visualizador_cannot_access_companies_page(client, visualizador_user):
    login(client, "visualizador@teste.com", "Senha@123")

    response = client.get("/admin/companies", follow_redirects=False)
    assert response.status_code in (302, 303, 308, 403)


def test_super_admin_can_open_companies_page_multiple_times(client, super_admin_user):
    login(client, "superadmin@teste.com", "Senha@123")

    response1 = client.get("/admin/companies", follow_redirects=True)
    response2 = client.get("/admin/companies", follow_redirects=True)

    assert response1.status_code == 200
    assert response2.status_code == 200


def test_admin_companies_page_has_expected_response_after_login(client, super_admin_user):
    login(client, "superadmin@teste.com", "Senha@123")

    response = client.get("/admin/companies", follow_redirects=True)

    assert response.status_code == 200
    assert response.data is not None
    assert len(response.data) > 0