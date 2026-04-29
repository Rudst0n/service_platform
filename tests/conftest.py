import os
import tempfile

import pytest

from app import create_app
from app.extensions import db
from app.models.company import Company, CompanyStatus
from app.models.user import User
from app.models.customer import Customer


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp(suffix=".db")

    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path}",
        SERVER_NAME="localhost.localdomain",
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


@pytest.fixture
def company(app):
    with app.app_context():
        company = Company(
            name="Empresa Teste",
            cnpj="12.345.678/0001-99",
            plan="starter",
            status=CompanyStatus.ACTIVE,
            is_active=True,
        )
        db.session.add(company)
        db.session.commit()
        db.session.refresh(company)
        return company


@pytest.fixture
def admin_user(app, company):
    with app.app_context():
        user = User(
            name="Administrador Teste",
            email="admin@teste.com",
            cpf="123.456.789-00",
            system_role="company_user",
            company_role="admin_empresa",
            company_id=company.id,
            is_active=True,
            email_confirmed=True,
            must_change_password=False,
        )
        user.set_password("Senha@123")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture
def visualizador_user(app, company):
    with app.app_context():
        user = User(
            name="Visualizador Teste",
            email="visualizador@teste.com",
            cpf="123.456.789-01",
            system_role="company_user",
            company_role="visualizador",
            company_id=company.id,
            is_active=True,
            email_confirmed=True,
            must_change_password=False,
        )
        user.set_password("Senha@123")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user


@pytest.fixture
def super_admin_user(app, company):
    with app.app_context():
        user = User(
            name="Super Admin",
            email="superadmin@teste.com",
            cpf="123.456.789-02",
            system_role="super_admin",
            company_role=None,
            company_id=company.id,
            is_active=True,
            email_confirmed=True,
            must_change_password=False,
        )
        user.set_password("Senha@123")
        db.session.add(user)
        db.session.commit()
        db.session.refresh(user)
        return user
    

@pytest.fixture
def customer(app, company):
    with app.app_context():
        customer = Customer(
            name="Cliente Base",
            email="cliente.base@teste.com",
            phone="41999999999",
            cpf="123.456.789-20",
            company_id=company.id,
        )
        db.session.add(customer)
        db.session.commit()
        db.session.refresh(customer)
        return customer 
    

@pytest.fixture
def portal_customer(app, company):
    with app.app_context():
        customer = Customer(
            name="Cliente Portal",
            email="portal@teste.com",
            phone="41999999998",
            cpf="123.456.789-40",
            company_id=company.id,
            is_portal_active=True,
            must_change_password=False,
        )
        customer.set_password("Senha@123")
        db.session.add(customer)
        db.session.commit()
        db.session.refresh(customer)
        return customer