from flask import abort

from app.extensions import db
from app.models.customer import Customer
from app.utils.audit import log_action
from app.utils.normalizer import normalize_email, normalize_phone, normalize_text
from app.utils.security import is_valid_email


class CustomerServiceError(Exception):
    pass


class CustomerValidationError(CustomerServiceError):
    pass


class CustomerNotFoundError(CustomerServiceError):
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
    def validate_payload(data):
        name = data.get("name")
        email = data.get("email")

        if not name:
            raise CustomerValidationError("Nome é obrigatório.")

        if email and not is_valid_email(email):
            raise CustomerValidationError("E-mail inválido.")

    @staticmethod
    def base_query(company_id):
        return Customer.query.filter_by(company_id=company_id)

    @staticmethod
    def list_paginated(company_id, page=1, per_page=10):
        return (
            CustomerService.base_query(company_id)
            .order_by(Customer.id.desc())
            .paginate(page=page, per_page=per_page, error_out=False)
        )

    @staticmethod
    def get_or_404(customer_id, company_id):
        customer = CustomerService.base_query(company_id).filter_by(id=customer_id).first()
        if not customer:
            abort(404)
        return customer

    @staticmethod
    def create_customer(data, company_id, actor_user_id):
        CustomerService.validate_payload(data)

        try:
            customer = Customer(
                name=data["name"],
                phone=data["phone"],
                email=data["email"],
                company_id=company_id,
            )

            db.session.add(customer)
            db.session.flush()

            log_action(
                "create_customer",
                "customer",
                customer.id,
                f"Cliente {customer.name} criado.",
                company_id=company_id,
                user_id=actor_user_id,
            )

            db.session.commit()
            return customer

        except CustomerValidationError:
            raise
        except Exception as exc:
            db.session.rollback()
            raise CustomerServiceError("Erro ao criar cliente.") from exc

    @staticmethod
    def update_customer(customer, data, actor_user_id):
        CustomerService.validate_payload(data)

        try:
            customer.name = data["name"]
            customer.phone = data["phone"]
            customer.email = data["email"]

            log_action(
                "update_customer",
                "customer",
                customer.id,
                f"Cliente {customer.name} atualizado.",
                company_id=customer.company_id,
                user_id=actor_user_id,
            )

            db.session.commit()
            return customer

        except CustomerValidationError:
            raise
        except Exception as exc:
            db.session.rollback()
            raise CustomerServiceError("Erro ao atualizar cliente.") from exc

    @staticmethod
    def delete_customer(customer, actor_user_id):
        try:
            log_action(
                "delete_customer",
                "customer",
                customer.id,
                f"Cliente {customer.name} excluído.",
                company_id=customer.company_id,
                user_id=actor_user_id,
            )

            db.session.delete(customer)
            db.session.commit()

        except Exception as exc:
            db.session.rollback()
            raise CustomerServiceError("Erro ao excluir cliente.") from exc