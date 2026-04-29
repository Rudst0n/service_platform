import pytest
from werkzeug.exceptions import NotFound

from app.extensions import db
from app.models.customer import Customer
from app.models.service import Service
from app.services.customer_service import (
    CustomerService,
    CustomerServiceError,
    CustomerValidationError,
)


def test_normalize_form_data_basic():
    data = CustomerService.normalize_form_data(
        {
            "name": "  Joao   Silva  ",
            "phone": "(41) 99999-8888",
            "email": "  TESTE@EMAIL.COM  ",
            "cpf": "12345678901",
            "is_portal_active": "on",
            "password": "123456",
            "confirm_password": "123456",
        }
    )

    assert data["name"] == "Joao Silva"
    assert data["phone"] == "(41) 99999-8888"
    assert data["email"] == "teste@email.com"
    assert data["cpf"] == "123.456.789-01"
    assert data["is_portal_active"] is True
    assert data["password"] == "123456"
    assert data["confirm_password"] == "123456"


def test_validate_data_requires_name():
    with pytest.raises(CustomerValidationError, match="nome do cliente é obrigatório"):
        CustomerService.validate_data(
            {
                "name": "",
                "phone": "(41) 99999-8888",
                "email": None,
                "cpf": None,
                "is_portal_active": False,
                "password": "",
                "confirm_password": "",
            }
        )


def test_validate_data_requires_name_with_min_length():
    with pytest.raises(CustomerValidationError, match="pelo menos 3 caracteres"):
        CustomerService.validate_data(
            {
                "name": "Al",
                "phone": "(41) 99999-8888",
                "email": None,
                "cpf": None,
                "is_portal_active": False,
                "password": "",
                "confirm_password": "",
            }
        )


def test_validate_data_requires_phone_or_email():
    with pytest.raises(CustomerValidationError, match="Informe pelo menos um contato válido"):
        CustomerService.validate_data(
            {
                "name": "Cliente Teste",
                "phone": None,
                "email": None,
                "cpf": None,
                "is_portal_active": False,
                "password": "",
                "confirm_password": "",
            }
        )


def test_validate_data_rejects_invalid_phone():
    with pytest.raises(CustomerValidationError, match="Telefone inválido"):
        CustomerService.validate_data(
            {
                "name": "Cliente Teste",
                "phone": "123",
                "email": None,
                "cpf": None,
                "is_portal_active": False,
                "password": "",
                "confirm_password": "",
            }
        )


def test_validate_data_rejects_invalid_email():
    with pytest.raises(CustomerValidationError, match="E-mail inválido"):
        CustomerService.validate_data(
            {
                "name": "Cliente Teste",
                "phone": None,
                "email": "email-invalido",
                "cpf": None,
                "is_portal_active": False,
                "password": "",
                "confirm_password": "",
            }
        )


def test_validate_data_rejects_placeholder_email():
    with pytest.raises(CustomerValidationError, match="e-mail real"):
        CustomerService.validate_data(
            {
                "name": "Cliente Teste",
                "phone": None,
                "email": "teste@gmail.com",
                "cpf": None,
                "is_portal_active": False,
                "password": "",
                "confirm_password": "",
            }
        )


def test_validate_data_rejects_invalid_cpf():
    with pytest.raises(CustomerValidationError, match="CPF inválido"):
        CustomerService.validate_data(
            {
                "name": "Cliente Teste",
                "phone": "(41) 99999-8888",
                "email": None,
                "cpf": "123",
                "is_portal_active": False,
                "password": "",
                "confirm_password": "",
            }
        )


def test_validate_data_requires_email_when_portal_active():
    with pytest.raises(CustomerValidationError, match="informe um e-mail"):
        CustomerService.validate_data(
            {
                "name": "Cliente Portal",
                "phone": "(41) 99999-8888",
                "email": None,
                "cpf": None,
                "is_portal_active": True,
                "password": "123456",
                "confirm_password": "123456",
            }
        )


def test_validate_data_requires_password_when_portal_active():
    with pytest.raises(CustomerValidationError, match="senha de acesso do portal"):
        CustomerService.validate_data(
            {
                "name": "Cliente Portal",
                "phone": None,
                "email": "portal@gmail.com",
                "cpf": None,
                "is_portal_active": True,
                "password": "",
                "confirm_password": "",
            }
        )


def test_validate_data_requires_matching_passwords():
    with pytest.raises(CustomerValidationError, match="senhas não conferem"):
        CustomerService.validate_data(
            {
                "name": "Cliente Portal",
                "phone": None,
                "email": "portal@gmail.com",
                "cpf": None,
                "is_portal_active": True,
                "password": "123456",
                "confirm_password": "654321",
            }
        )


def test_validate_data_requires_min_password_length():
    with pytest.raises(CustomerValidationError, match="mínimo 6 caracteres"):
        CustomerService.validate_data(
            {
                "name": "Cliente Portal",
                "phone": None,
                "email": "portal@gmail.com",
                "cpf": None,
                "is_portal_active": True,
                "password": "123",
                "confirm_password": "123",
            }
        )


def test_find_duplicate_by_email(app, company):
    with app.app_context():
        customer = Customer(
            name="Cliente Duplicado",
            email="duplicado@gmail.com",
            phone="(41) 99999-0001",
            cpf="123.456.789-50",
            company_id=company.id,
        )
        db.session.add(customer)
        db.session.commit()

        duplicate = CustomerService._find_duplicate(
            company.id,
            {
                "name": "Outro Cliente",
                "email": "duplicado@gmail.com",
                "phone": None,
                "cpf": None,
            },
        )

        assert duplicate is not None
        assert duplicate.email == "duplicado@gmail.com"


def test_find_duplicate_by_cpf(app, company):
    with app.app_context():
        customer = Customer(
            name="Cliente CPF",
            email="cpf@gmail.com",
            phone="(41) 99999-0002",
            cpf="123.456.789-51",
            company_id=company.id,
        )
        db.session.add(customer)
        db.session.commit()

        duplicate = CustomerService._find_duplicate(
            company.id,
            {
                "name": "Outro Cliente",
                "email": None,
                "phone": None,
                "cpf": "123.456.789-51",
            },
        )

        assert duplicate is not None
        assert duplicate.cpf == "123.456.789-51"


def test_find_duplicate_by_phone_digits(app, company):
    with app.app_context():
        customer = Customer(
            name="Cliente Telefone",
            email="telefone@gmail.com",
            phone="(41) 99999-0003",
            cpf="123.456.789-52",
            company_id=company.id,
        )
        db.session.add(customer)
        db.session.commit()

        duplicate = CustomerService._find_duplicate(
            company.id,
            {
                "name": "Outro Cliente",
                "email": None,
                "phone": "41999990003",
                "cpf": None,
            },
        )

        assert duplicate is not None
        assert duplicate.phone == "(41) 99999-0003"


def test_create_customer(app, company, admin_user):
    with app.app_context():
        customer = CustomerService.create_customer(
            data={
                "name": "Cliente Criado",
                "phone": "(41) 99999-1111",
                "email": "criado@gmail.com",
                "cpf": "123.456.789-53",
                "is_portal_active": False,
                "password": "",
                "confirm_password": "",
            },
            company_id=company.id,
            actor_user_id=admin_user.id,
        )

        assert customer is not None
        assert customer.name == "Cliente Criado"
        assert customer.company_id == company.id


def test_create_customer_with_portal_password(app, company, admin_user):
    with app.app_context():
        customer = CustomerService.create_customer(
            data={
                "name": "Cliente Portal",
                "phone": "(41) 99999-1112",
                "email": "portal.criado@gmail.com",
                "cpf": "123.456.789-54",
                "is_portal_active": True,
                "password": "123456",
                "confirm_password": "123456",
            },
            company_id=company.id,
            actor_user_id=admin_user.id,
        )

        assert customer.is_portal_active is True
        assert customer.password_hash is not None
        assert customer.check_password("123456") is True


def test_create_customer_rejects_duplicate(app, company, admin_user):
    with app.app_context():
        existing = Customer(
            name="Existente",
            email="existente@gmail.com",
            phone="(41) 99999-1113",
            cpf="123.456.789-55",
            company_id=company.id,
        )
        db.session.add(existing)
        db.session.commit()

        with pytest.raises(CustomerValidationError, match="Já existe um cliente"):
            CustomerService.create_customer(
                data={
                    "name": "Duplicado",
                    "phone": "(41) 99999-9999",
                    "email": "existente@gmail.com",
                    "cpf": None,
                    "is_portal_active": False,
                    "password": "",
                    "confirm_password": "",
                },
                company_id=company.id,
                actor_user_id=admin_user.id,
            )


def test_update_customer(app, company, admin_user):
    with app.app_context():
        customer = Customer(
            name="Antes",
            email="antes@gmail.com",
            phone="(41) 99999-1114",
            cpf="123.456.789-56",
            company_id=company.id,
        )
        db.session.add(customer)
        db.session.commit()

        updated = CustomerService.update_customer(
            customer,
            data={
                "name": "Depois",
                "phone": "(41) 98888-1114",
                "email": "depois@gmail.com",
                "cpf": "123.456.789-57",
                "is_portal_active": False,
                "password": "",
                "confirm_password": "",
            },
            actor_user_id=admin_user.id,
        )

        assert updated.name == "Depois"
        assert updated.email == "depois@gmail.com"
        assert updated.phone == "(41) 98888-1114"


def test_update_customer_rejects_duplicate(app, company, admin_user):
    with app.app_context():
        customer1 = Customer(
            name="Cliente 1",
            email="cliente1@gmail.com",
            phone="(41) 99999-1115",
            cpf="123.456.789-58",
            company_id=company.id,
        )
        customer2 = Customer(
            name="Cliente 2",
            email="cliente2@gmail.com",
            phone="(41) 99999-1116",
            cpf="123.456.789-59",
            company_id=company.id,
        )
        db.session.add_all([customer1, customer2])
        db.session.commit()

        with pytest.raises(CustomerValidationError, match="Já existe outro cliente"):
            CustomerService.update_customer(
                customer2,
                data={
                    "name": "Cliente 2",
                    "phone": "(41) 99999-1116",
                    "email": "cliente1@gmail.com",
                    "cpf": "123.456.789-59",
                    "is_portal_active": False,
                    "password": "",
                    "confirm_password": "",
                },
                actor_user_id=admin_user.id,
            )


def test_delete_customer_without_services(app, company, admin_user):
    with app.app_context():
        customer = Customer(
            name="Cliente Excluir",
            email="excluir@gmail.com",
            phone="(41) 99999-1117",
            cpf="123.456.789-60",
            company_id=company.id,
        )
        db.session.add(customer)
        db.session.commit()

        customer_id = customer.id
        CustomerService.delete_customer(customer, actor_user_id=admin_user.id)

        deleted = db.session.get(Customer, customer_id)
        assert deleted is None


def test_delete_customer_with_services_raises_error(app, company, admin_user, customer):
    with app.app_context():
        service = Service(
            request_number=900,
            request_code="REQ-0900",
            name="Servico Vinculado",
            description="Teste",
            price=100,
            status="orcamento",
            customer_id=customer.id,
            company_id=company.id,
            created_by_id=admin_user.id,
            assigned_to_id=admin_user.id,
        )
        db.session.add(service)
        db.session.commit()

        with pytest.raises(CustomerServiceError, match="serviços vinculados"):
            CustomerService.delete_customer(customer, actor_user_id=admin_user.id)


def test_get_or_404_returns_customer(app, company, customer):
    with app.app_context():
        found = CustomerService.get_or_404(customer.id, company.id)
        assert found.id == customer.id


def test_get_or_404_raises_not_found(app, company):
    with app.app_context():
        with pytest.raises(NotFound):
            CustomerService.get_or_404(999999, company.id)


def test_list_paginated_returns_results(app, company):
    with app.app_context():
        for i in range(3):
            customer = Customer(
                name=f"Cliente Pag {i}",
                email=f"pag{i}@gmail.com",
                phone=f"(41) 99999-12{i:02d}",
                cpf=f"123.456.790-{i:02d}",
                company_id=company.id,
            )
            db.session.add(customer)

        db.session.commit()

        result = CustomerService.list_paginated(company.id, page=1, per_page=10)

        assert result is not None
        assert len(result.items) == 3


def test_list_paginated_search_by_name(app, company):
    with app.app_context():
        db.session.add(
            Customer(
                name="Carlos Silva",
                email="carlos@gmail.com",
                phone="(41) 99999-1300",
                cpf="123.456.791-00",
                company_id=company.id,
            )
        )
        db.session.commit()

        result = CustomerService.list_paginated(
            company.id,
            page=1,
            per_page=10,
            search="Carlos",
        )

        assert len(result.items) == 1
        assert result.items[0].name == "Carlos Silva"