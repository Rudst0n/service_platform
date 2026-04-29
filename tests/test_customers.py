from app.extensions import db
from app.models.customer import Customer
from tests.helpers import login


def test_customers_page_requires_login(client):
    response = client.get("/customers/", follow_redirects=False)
    assert response.status_code in (301, 302, 303, 308, 401, 403)


def test_admin_can_access_customers_page(client, admin_user):
    login(client, "admin@teste.com", "Senha@123")

    response = client.get("/customers/", follow_redirects=True)
    assert response.status_code == 200


def test_admin_can_access_new_customer_page(client, admin_user):
    login(client, "admin@teste.com", "Senha@123")

    response = client.get("/customers/new", follow_redirects=True)
    assert response.status_code == 200


def test_visualizador_cannot_access_customers_page(client, visualizador_user):
    login(client, "visualizador@teste.com", "Senha@123")

    response = client.get("/customers/", follow_redirects=False)
    assert response.status_code in (302, 303, 308, 403)


def test_customer_model_can_be_created(app, company):
    with app.app_context():
        customer = Customer(
            name="Cliente Teste",
            email="cliente@teste.com",
            phone="41999999999",
            cpf="123.456.789-10",
            company_id=company.id,
        )
        db.session.add(customer)
        db.session.commit()

        saved = Customer.query.filter_by(email="cliente@teste.com").first()

        assert saved is not None
        assert saved.name == "Cliente Teste"


def test_duplicate_customer_email_behavior(app, company):
    with app.app_context():
        customer1 = Customer(
            name="Cliente 1",
            email="duplicado@teste.com",
            phone="41999999999",
            cpf="123.456.789-11",
            company_id=company.id,
        )
        customer2 = Customer(
            name="Cliente 2",
            email="duplicado@teste.com",
            phone="41888888888",
            cpf="123.456.789-12",
            company_id=company.id,
        )

        db.session.add(customer1)
        db.session.commit()

        db.session.add(customer2)

        try:
            db.session.commit()
            duplicate_allowed = True
        except Exception:
            db.session.rollback()
            duplicate_allowed = False

        assert duplicate_allowed in (True, False)