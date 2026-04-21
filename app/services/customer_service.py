from flask import abort
from sqlalchemy import or_

from app.extensions import db
from app.models.customer import Customer
from app.models.service import Service
from app.utils.audit import log_action
from app.utils.normalizer import (
    normalize_email,
    normalize_phone,
    normalize_text,
    only_digits,
)
from app.utils.security import is_valid_email


class CustomerServiceError(Exception):
    pass


class CustomerValidationError(CustomerServiceError):
    pass


class CustomerService:
    PLACEHOLDER_EMAIL_WORDS = {
        "teste",
        "test",
        "fake",
        "falso",
        "email",
        "exemplo",
        "example",
        "kkkk",
        "kkkkk",
        "abc",
        "asdf",
        "qwerty",
    }

    @staticmethod
    def normalize_form_data(form):
        raw_phone = form.get("phone")
        raw_email = form.get("email")
        raw_cpf = form.get("cpf")

        phone_digits = only_digits(raw_phone)
        cpf_digits = only_digits(raw_cpf)

        normalized_phone = normalize_phone(phone_digits) if phone_digits else None
        normalized_email = normalize_email(raw_email)

        normalized_cpf = None
        if cpf_digits and len(cpf_digits) == 11:
            normalized_cpf = (
                f"{cpf_digits[:3]}.{cpf_digits[3:6]}."
                f"{cpf_digits[6:9]}-{cpf_digits[9:]}"
            )

        return {
            "name": normalize_text(form.get("name")),
            "phone": normalized_phone,
            "email": normalized_email,
            "cpf": normalized_cpf,
            "is_portal_active": form.get("is_portal_active") == "on",
            "password": form.get("password", "").strip(),
            "confirm_password": form.get("confirm_password", "").strip(),
        }

    @staticmethod
    def _looks_like_placeholder_email(email):
        if not email or "@" not in email:
            return False

        local_part, domain = email.split("@", 1)
        domain_name = domain.split(".", 1)[0] if "." in domain else domain

        local_clean = "".join(ch for ch in local_part.lower() if ch.isalnum())
        domain_clean = "".join(ch for ch in domain_name.lower() if ch.isalnum())

        if local_clean in CustomerService.PLACEHOLDER_EMAIL_WORDS:
            return True

        if domain_clean in CustomerService.PLACEHOLDER_EMAIL_WORDS:
            return True

        if local_clean and len(set(local_clean)) == 1 and len(local_clean) >= 4:
            return True

        if domain_clean and len(set(domain_clean)) == 1 and len(domain_clean) >= 4:
            return True

        return False

    @staticmethod
    def validate_data(data):
        name = data.get("name")
        phone = data.get("phone")
        email = data.get("email")
        cpf = data.get("cpf")
        is_portal_active = data.get("is_portal_active")
        password = data.get("password")
        confirm_password = data.get("confirm_password")

        if not name:
            raise CustomerValidationError("O nome do cliente é obrigatório.")

        if len(name) < 3:
            raise CustomerValidationError(
                "O nome do cliente deve ter pelo menos 3 caracteres."
            )

        if not phone and not email:
            raise CustomerValidationError(
                "Informe pelo menos um contato válido: telefone ou e-mail."
            )

        if phone:
            phone_digits = only_digits(phone)

            if not phone_digits:
                raise CustomerValidationError("Telefone inválido.")

            if len(phone_digits) not in (10, 11):
                raise CustomerValidationError(
                    "Telefone inválido. Informe um número com DDD."
                )

        if email:
            if not is_valid_email(email):
                raise CustomerValidationError("E-mail inválido.")

            if CustomerService._looks_like_placeholder_email(email):
                raise CustomerValidationError(
                    "Informe um e-mail real do cliente."
                )

        if cpf:
            cpf_digits = only_digits(cpf)

            if len(cpf_digits) != 11:
                raise CustomerValidationError("CPF inválido.")

        if is_portal_active:
            if not email:
                raise CustomerValidationError(
                    "Para ativar o portal, informe um e-mail."
                )

            if not password:
                raise CustomerValidationError(
                    "Informe a senha de acesso do portal."
                )

            if password != confirm_password:
                raise CustomerValidationError(
                    "As senhas não conferem."
                )

            if len(password) < 6:
                raise CustomerValidationError(
                    "A senha deve ter no mínimo 6 caracteres."
                )

    @staticmethod
    def _find_duplicate(company_id, data, ignore_customer_id=None):
        filters = []

        if data.get("email"):
            filters.append(Customer.email == data["email"])

        if data.get("cpf"):
            filters.append(Customer.cpf == data["cpf"])

        phone_digits = only_digits(data.get("phone"))
        if phone_digits:
            customers_same_company = Customer.query.filter_by(
                company_id=company_id
            ).all()

            for customer in customers_same_company:
                if ignore_customer_id and customer.id == ignore_customer_id:
                    continue

                existing_phone_digits = only_digits(customer.phone)

                if existing_phone_digits == phone_digits:
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

            conditions = [
                Customer.name.ilike(f"%{search}%")
            ]

            if "@" in search:
                conditions.append(
                    Customer.email.ilike(f"%{search}%")
                )

            if search_digits:
                conditions.append(
                    Customer.cpf.ilike(f"%{search}%")
                )

                customers_same_company = Customer.query.filter_by(
                    company_id=company_id
                ).all()

                matching_ids_by_phone = []

                for customer in customers_same_company:
                    customer_phone_digits = only_digits(customer.phone)

                    if (
                        customer_phone_digits
                        and search_digits in customer_phone_digits
                    ):
                        matching_ids_by_phone.append(customer.id)

                if matching_ids_by_phone:
                    conditions.append(
                        Customer.id.in_(matching_ids_by_phone)
                    )

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

        duplicate = CustomerService._find_duplicate(company_id, data)

        if duplicate:
            raise CustomerValidationError(
                "Já existe um cliente com este telefone, e-mail ou CPF cadastrado na empresa."
            )

        customer = Customer(
            name=data["name"],
            phone=data.get("phone"),
            email=data.get("email"),
            cpf=data.get("cpf"),
            company_id=company_id,
            is_portal_active=data.get("is_portal_active", False),
        )

        if data.get("is_portal_active"):
            customer.set_password(data["password"])

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
                "Já existe outro cliente com este telefone, e-mail ou CPF cadastrado na empresa."
            )

        customer.name = data["name"]
        customer.phone = data.get("phone")
        customer.email = data.get("email")
        customer.cpf = data.get("cpf")
        customer.is_portal_active = data.get("is_portal_active", False)

        if data.get("password"):
            customer.set_password(data["password"])

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
        linked_services = Service.query.filter_by(
            customer_id=customer.id
        ).count()

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