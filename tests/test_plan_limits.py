from app.extensions import db
from app.models.customer import Customer
from app.models.service import Service
from app.models.user import User
from app.utils.plan_limits import get_limit, get_usage, is_limit_reached, get_usage_data


def test_get_limit_returns_starter_customer_limit(company):
    company.plan = "starter"
    assert get_limit(company, "customers") == 50


def test_get_limit_returns_pro_service_limit(company):
    company.plan = "pro"
    assert get_limit(company, "services") == 1000


def test_get_limit_returns_none_for_business(company):
    company.plan = "business"
    assert get_limit(company, "customers") is None
    assert get_limit(company, "services") is None
    assert get_limit(company, "users") is None


def test_get_limit_falls_back_to_starter_for_unknown_plan(company):
    company.plan = "plano_invalido"
    assert get_limit(company, "customers") == 50
    assert get_limit(company, "services") == 100
    assert get_limit(company, "users") == 2


def test_get_usage_counts_customers(app, company):
    with app.app_context():
        customer1 = Customer(
            name="Cliente Uso 1",
            email="uso1@teste.com",
            phone="41999990001",
            cpf="123.456.780-01",
            company_id=company.id,
        )
        customer2 = Customer(
            name="Cliente Uso 2",
            email="uso2@teste.com",
            phone="41999990002",
            cpf="123.456.780-02",
            company_id=company.id,
        )

        db.session.add_all([customer1, customer2])
        db.session.commit()

        usage = get_usage(company, Customer)
        assert usage == 2


def test_is_limit_not_reached_for_customers_under_starter_limit(app, company):
    with app.app_context():
        company.plan = "starter"
        db.session.commit()

        customer = Customer(
            name="Cliente Limite",
            email="limite1@teste.com",
            phone="41999990003",
            cpf="123.456.780-03",
            company_id=company.id,
        )
        db.session.add(customer)
        db.session.commit()

        reached = is_limit_reached(company, Customer, "customers")
        assert reached is False


def test_is_limit_reached_for_users_on_starter_plan(app, company):
    with app.app_context():
        company.plan = "starter"
        db.session.commit()

        user1 = User(
            name="User Limite 1",
            email="userlimite1@teste.com",
            cpf="123.456.780-04",
            system_role="company_user",
            company_role="funcionario",
            company_id=company.id,
            is_active=True,
            email_confirmed=True,
            must_change_password=False,
        )
        user1.set_password("Senha@123")

        user2 = User(
            name="User Limite 2",
            email="userlimite2@teste.com",
            cpf="123.456.780-05",
            system_role="company_user",
            company_role="funcionario",
            company_id=company.id,
            is_active=True,
            email_confirmed=True,
            must_change_password=False,
        )
        user2.set_password("Senha@123")

        db.session.add_all([user1, user2])
        db.session.commit()

        reached = is_limit_reached(company, User, "users")
        assert reached is True


def test_business_plan_never_reaches_customer_limit(app, company):
    with app.app_context():
        company.plan = "business"
        db.session.commit()

        for i in range(5):
            customer = Customer(
                name=f"Cliente Business {i}",
                email=f"business{i}@teste.com",
                phone=f"41999991{i:03d}",
                cpf=f"123.456.781-{i:02d}",
                company_id=company.id,
            )
            db.session.add(customer)

        db.session.commit()

        reached = is_limit_reached(company, Customer, "customers")
        assert reached is False


def test_get_usage_data_returns_expected_structure(app, company):
    with app.app_context():
        company.plan = "starter"
        db.session.commit()

        customer = Customer(
            name="Cliente Dados",
            email="dados@teste.com",
            phone="41999990010",
            cpf="123.456.780-10",
            company_id=company.id,
        )
        db.session.add(customer)
        db.session.commit()

        data = get_usage_data(company)

        assert "customers" in data
        assert "services" in data
        assert "users" in data

        assert "limit" in data["customers"]
        assert "usage" in data["customers"]
        assert "percent" in data["customers"]

        assert data["customers"]["limit"] == 50
        assert data["customers"]["usage"] >= 1


def test_get_usage_data_percent_for_customers(app, company):
    with app.app_context():
        company.plan = "starter"
        db.session.commit()

        for i in range(5):
            customer = Customer(
                name=f"Cliente Percent {i}",
                email=f"percent{i}@teste.com",
                phone=f"41888881{i:03d}",
                cpf=f"123.456.782-{i:02d}",
                company_id=company.id,
            )
            db.session.add(customer)

        db.session.commit()

        data = get_usage_data(company)

        assert data["customers"]["usage"] == 5
        assert data["customers"]["limit"] == 50
        assert data["customers"]["percent"] == 10