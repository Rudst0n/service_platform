from flask import abort
from sqlalchemy import or_

from app.extensions import db
from app.models.customer import Customer
from app.models.service import Service
from app.utils.audit import log_action
from app.utils.normalizer import normalize_email, normalize_phone, normalize_text, only_digits


class CustomerServiceError(Exception):
    pass


class CustomerValidationError(CustomerServiceError):
    pass


class CustomerService:
    @staticmethod
    def normalize_form_data(form):
        return {
            "name": normalize_text(form.get("name")),
            "phone": normalize_phone(form.get("phone")),
            "email": normalize_email(form.get("email")),
        }

    @staticmethod
    def validate_data(data):
        name = data.get("name")
        phone = data.get("phone")
        email = data.get("email")

        if not name:
            raise CustomerValidationError("O nome do cliente é obrigatório.")

        if len(name) < 3:
            raise CustomerValidationError("O nome do cliente deve ter pelo menos 3 caracteres.")

        if phone:
            phone_digits = only_digits(phone)
            if phone_digits and len(phone_digits) not in (10, 11):
                raise CustomerValidationError("Telefone inválido. Informe um número com DDD.")

        if email and "@" not in email:
            raise CustomerValidationError("E-mail inválido.")

    @staticmethod
    def _find_duplicate(company_id, data, ignore_customer_id=None):
        filters = []

        if data.get("email"):
            filters.append(Customer.email == data["email"])

        phone_digits = only_digits(data.get("phone"))
        if phone_digits:
            customers_same_company = Customer.query.filter_by(company_id=company_id).all()
            for customer in customers_same_company:
                if ignore_customer_id and customer.id == ignore_customer_id:
                    continue

                existing_phone_digits = only_digits(customer.phone)
                if existing_phone_digits and existing_phone_digits == phone_digits:
                    return customer

        if filters:
            query = Customer.query.filter(
                Customer.company_id == company_id,
                or_(*filters),
            )

            if ignore_customer_id:
                query = query.filter(Customer.id != ignore_customer_id)

            duplicate = query.first()
            if duplicate:
                return duplicate

        return None

    @staticmethod
    def list_paginated(company_id, page=1, per_page=10, search=None):
        query = Customer.query.filter_by(company_id=company_id)

        if search:
            search = search.strip()
            search_digits = only_digits(search)

            conditions = [Customer.name.ilike(f"%{search}%")]

            if "@" in search:
                conditions.append(Customer.email.ilike(f"%{search}%"))

            customers_same_company = Customer.query.filter_by(company_id=company_id).all()
            matching_ids_by_phone = []

            if search_digits:
                for customer in customers_same_company:
                    customer_phone_digits = only_digits(customer.phone)
                    if customer_phone_digits and search_digits in customer_phone_digits:
                        matching_ids_by_phone.append(customer.id)

            if matching_ids_by_phone:
                conditions.append(Customer.id.in_(matching_ids_by_phone))

            query = query.filter(or_(*conditions))

        return query.order_by(Customer.id.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )

    @staticmethod
    def get_or_404(customer_id, company_id):
        customer = Customer.query.filter_by(
            id=customer_id,
            company_id=company_id,
        ).first()

        if not customer:
            abort(404)

        return customer

    @staticmethod
    def create_customer(data, company_id, actor_user_id):
        CustomerService.validate_data(data)

        duplicate = CustomerService._find_duplicate(company_id=company_id, data=data)
        if duplicate:
            raise CustomerValidationError(
                "Já existe um cliente com este telefone ou e-mail cadastrado na empresa."
            )

        customer = Customer(
            name=data["name"],
            phone=data.get("phone"),
            email=data.get("email"),
            company_id=company_id,
        )

        db.session.add(customer)
        db.session.commit()

        log_action(
            action="create_customer",
            entity_type="customer",
            entity_id=customer.id,
            description=f"Cliente {customer.name} criado.",
            company_id=company_id,
            user_id=actor_user_id,
        )

        return customer

    @staticmethod
    def update_customer(customer, data, actor_user_id):
        CustomerService.validate_data(data)

        duplicate = CustomerService._find_duplicate(
            company_id=customer.company_id,
            data=data,
            ignore_customer_id=customer.id,
        )
        if duplicate:
            raise CustomerValidationError(
                "Já existe outro cliente com este telefone ou e-mail cadastrado na empresa."
            )

        customer.name = data["name"]
        customer.phone = data.get("phone")
        customer.email = data.get("email")

        db.session.commit()

        log_action(
            action="update_customer",
            entity_type="customer",
            entity_id=customer.id,
            description=f"Cliente {customer.name} atualizado.",
            company_id=customer.company_id,
            user_id=actor_user_id,
        )

        return customer

    @staticmethod
    def delete_customer(customer, actor_user_id):
        linked_services = Service.query.filter_by(customer_id=customer.id).count()
        if linked_services > 0:
            raise CustomerServiceError(
                "Este cliente possui serviços vinculados e não pode ser excluído."
            )

        customer_name = customer.name
        company_id = customer.company_id
        customer_id = customer.id

        db.session.delete(customer)
        db.session.commit()

        log_action(
            action="delete_customer",
            entity_type="customer",
            entity_id=customer_id,
            description=f"Cliente {customer_name} excluído.",
            company_id=company_id,
            user_id=actor_user_id,
        )