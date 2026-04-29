from app.extensions import db
from app.models.service import Service
from tests.helpers import login


def test_services_page_requires_login(client):
    response = client.get("/services/", follow_redirects=False)
    assert response.status_code in (301, 302, 303, 308, 401, 403)


def test_admin_can_access_services_page(client, admin_user):
    login(client, "admin@teste.com", "Senha@123")

    response = client.get("/services/", follow_redirects=True)
    assert response.status_code == 200


def test_visualizador_can_access_services_page(client, visualizador_user):
    login(client, "visualizador@teste.com", "Senha@123")

    response = client.get("/services/", follow_redirects=True)
    assert response.status_code == 200


def test_admin_can_access_new_service_page(client, admin_user):
    login(client, "admin@teste.com", "Senha@123")

    response = client.get("/services/new", follow_redirects=True)
    assert response.status_code == 200


def test_service_model_can_be_created(app, company, customer, admin_user):
    with app.app_context():
        service = Service(
            request_number=1,
            request_code="REQ-0001",
            name="Serviço Teste",
            description="Descrição do serviço teste",
            price=150.00,
            status="orcamento",
            customer_id=customer.id,
            company_id=company.id,
            created_by_id=admin_user.id,
            assigned_to_id=admin_user.id,
        )
        db.session.add(service)
        db.session.commit()

        saved = Service.query.filter_by(request_code="REQ-0001").first()

        assert saved is not None
        assert saved.company_id == company.id
        assert saved.customer_id == customer.id
        assert saved.status == "orcamento"


def test_service_status_can_be_updated(app, company, customer, admin_user):
    with app.app_context():
        service = Service(
            request_number=2,
            request_code="REQ-0002",
            name="Serviço Atualização",
            description="Teste de atualização",
            price=250.00,
            status="orcamento",
            customer_id=customer.id,
            company_id=company.id,
            created_by_id=admin_user.id,
            assigned_to_id=admin_user.id,
        )
        db.session.add(service)
        db.session.commit()

        service.status = "em_andamento"
        db.session.commit()

        updated = Service.query.get(service.id)

        assert updated is not None
        assert updated.status == "em_andamento"


def test_service_belongs_to_company(app, company, customer, admin_user):
    with app.app_context():
        service = Service(
            request_number=3,
            request_code="REQ-0003",
            name="Serviço Empresa",
            description="Vinculação com empresa",
            price=300.00,
            status="finalizado",
            customer_id=customer.id,
            company_id=company.id,
            created_by_id=admin_user.id,
            assigned_to_id=admin_user.id,
        )
        db.session.add(service)
        db.session.commit()

        saved = Service.query.filter_by(request_code="REQ-0003").first()

        assert saved is not None
        assert saved.company_id == company.id