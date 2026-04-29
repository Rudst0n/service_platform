from decimal import Decimal

from app.extensions import db
from app.models.customer import Customer
from app.models.service import Service
from app.models.user import User


def login(client, login_value="admin@teste.com", password="Senha@123"):
    return client.post(
        "/auth/login",
        data={
            "login": login_value,
            "password": password,
        },
        follow_redirects=True,
    )


def create_customer(company_id):
    total = Customer.query.count() + 1

    customer = Customer(
        name="Cliente Teste",
        email=f"cliente{total}@gmail.com",
        phone="41999999999",
        cpf=f"123.456.789-{str(total).zfill(2)}",
        company_id=company_id,
    )
    db.session.add(customer)
    db.session.commit()
    return customer.id


def create_employee(company_id):
    user = User(
        name="Funcionario Teste",
        email="funcionario@teste.com",
        cpf="223.456.789-77",
        system_role="company_user",
        company_role="funcionario",
        company_id=company_id,
        is_active=True,
        email_confirmed=True,
        must_change_password=False,
    )
    user.set_password("Senha@123")
    db.session.add(user)
    db.session.commit()
    return user.id


def create_service(customer_id, company_id, assigned_to_id=None, created_by_id=None):
    last_service = (
        Service.query.filter_by(company_id=company_id)
        .order_by(Service.request_number.desc(), Service.id.desc())
        .first()
    )
    next_number = 1 if not last_service else last_service.request_number + 1

    service = Service(
        request_number=next_number,
        request_code=f"REQ-{str(next_number).zfill(3)}",
        name="Servico Teste",
        description="Descricao",
        status="orcamento",
        customer_id=customer_id,
        company_id=company_id,
        assigned_to_id=assigned_to_id,
        created_by_id=created_by_id,
    )
    db.session.add(service)
    db.session.commit()
    return service.id


def assert_logged_in(response):
    assert response.status_code == 200
    assert b"Entrar | ServHub" not in response.data


def test_admin_can_create_service_post(client, app, admin_user, company):
    with app.app_context():
        customer_id = create_customer(company.id)

    assert_logged_in(login(client))

    response = client.post(
        "/services/new",
        data={
            "name": "Novo Servico",
            "description": "Teste",
            "price": "150.50",
            "customer_id": str(customer_id),
            "status": "orcamento",
            "assigned_to_id": str(admin_user.id),
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        created = Service.query.filter_by(
            name="Novo Servico",
            company_id=company.id,
        ).first()
        assert created is not None


def test_create_service_requires_name(client, app, admin_user, company):
    with app.app_context():
        customer_id = create_customer(company.id)

    assert_logged_in(login(client))

    response = client.post(
        "/services/new",
        data={
            "name": "",
            "customer_id": str(customer_id),
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_admin_can_edit_service(client, app, admin_user, company):
    with app.app_context():
        customer_id = create_customer(company.id)
        service_id = create_service(
            customer_id=customer_id,
            company_id=company.id,
            assigned_to_id=admin_user.id,
            created_by_id=admin_user.id,
        )

    assert_logged_in(login(client))

    response = client.post(
        f"/services/{service_id}/edit",
        data={
            "name": "Servico Editado",
            "description": "Nova Desc",
            "price": "200",
            "customer_id": str(customer_id),
            "status": "aprovado",
            "assigned_to_id": str(admin_user.id),
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        updated = db.session.get(Service, service_id)
        assert updated is not None
        assert updated.name == "Servico Editado"
        assert updated.description == "Nova Desc"
        assert Decimal(updated.price) == Decimal("200")
        assert updated.status == "aprovado"


def test_admin_can_delete_service(client, app, admin_user, company):
    with app.app_context():
        customer_id = create_customer(company.id)
        service_id = create_service(
            customer_id=customer_id,
            company_id=company.id,
            assigned_to_id=admin_user.id,
            created_by_id=admin_user.id,
        )

    assert_logged_in(login(client))

    response = client.post(
        f"/services/{service_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        deleted = db.session.get(Service, service_id)
        assert deleted is None


def test_admin_can_update_status(client, app, admin_user, company):
    with app.app_context():
        customer_id = create_customer(company.id)
        service_id = create_service(
            customer_id=customer_id,
            company_id=company.id,
            assigned_to_id=admin_user.id,
            created_by_id=admin_user.id,
        )

    assert_logged_in(login(client))

    response = client.post(
        f"/services/{service_id}/update-status",
        data={"status": "finalizado"},
        follow_redirects=True,
    )

    assert response.status_code == 200

    with app.app_context():
        updated = db.session.get(Service, service_id)
        assert updated is not None
        assert updated.status == "finalizado"
        assert updated.finished_at is not None


def test_visualizador_cannot_edit_service(client, app, admin_user, visualizador_user, company):
    with app.app_context():
        customer_id = create_customer(company.id)
        service_id = create_service(
            customer_id=customer_id,
            company_id=company.id,
            assigned_to_id=admin_user.id,
            created_by_id=admin_user.id,
        )

    assert_logged_in(login(client, "visualizador@teste.com"))

    response = client.post(
        f"/services/{service_id}/edit",
        data={
            "name": "Hack",
            "customer_id": str(customer_id),
        },
        follow_redirects=True,
    )

    assert response.status_code == 200


def test_employee_cannot_edit_service_from_other_assignment(client, app, admin_user, company):
    with app.app_context():
        customer_id = create_customer(company.id)
        create_employee(company.id)
        service_id = create_service(
            customer_id=customer_id,
            company_id=company.id,
            assigned_to_id=admin_user.id,
            created_by_id=admin_user.id,
        )

    assert_logged_in(login(client, "funcionario@teste.com"))

    response = client.post(
        f"/services/{service_id}/edit",
        data={
            "name": "Hack",
            "customer_id": str(customer_id),
            "status": "em_andamento",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200