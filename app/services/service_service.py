from flask import abort

from app.extensions import db
from app.models.customer import Customer
from app.models.service import Service
from app.utils.audit import log_action
from app.utils.normalizer import normalize_text


class ServiceServiceError(Exception):
    pass


class ServiceValidationError(ServiceServiceError):
    pass


class ServiceService:
    @staticmethod
    def normalize_form_data(form):
        customer_id_raw = (form.get("customer_id") or "").strip()

        customer_id = None
        if customer_id_raw.isdigit():
            customer_id = int(customer_id_raw)

        return {
            "name": normalize_text(form.get("name")),
            "customer_id": customer_id,
        }

    @staticmethod
    def validate_payload(data, company_id):
        name = data.get("name")
        customer_id = data.get("customer_id")

        if not name or not customer_id:
            raise ServiceValidationError("Preencha os campos obrigatórios.")

        customer_exists = Customer.query.filter_by(
            id=customer_id,
            company_id=company_id
        ).first()

        if not customer_exists:
            raise ServiceValidationError("Cliente inválido para esta empresa.")

    @staticmethod
    def base_query(company_id):
        return Service.query.filter_by(company_id=company_id)

    @staticmethod
    def list_all(company_id):
        return (
            ServiceService.base_query(company_id)
            .order_by(Service.id.desc())
            .all()
        )

    @staticmethod
    def get_or_404(service_id, company_id):
        service = (
            ServiceService.base_query(company_id)
            .filter_by(id=service_id)
            .first()
        )

        if not service:
            abort(404)

        return service

    @staticmethod
    def create_service(data, company_id, actor_user_id):
        ServiceService.validate_payload(data, company_id)

        try:
            service = Service(
                name=data["name"],
                customer_id=data["customer_id"],
                company_id=company_id,
            )

            db.session.add(service)
            db.session.flush()

            log_action(
                "create_service",
                "service",
                service.id,
                f"Serviço {service.name} criado.",
                company_id=company_id,
                user_id=actor_user_id,
            )

            db.session.commit()
            return service

        except ServiceValidationError:
            raise
        except Exception as exc:
            db.session.rollback()
            raise ServiceServiceError("Erro ao criar serviço.") from exc

    @staticmethod
    def update_service(service, data, actor_user_id):
        ServiceService.validate_payload(data, service.company_id)

        try:
            service.name = data["name"]
            service.customer_id = data["customer_id"]

            log_action(
                "update_service",
                "service",
                service.id,
                f"Serviço {service.name} atualizado.",
                company_id=service.company_id,
                user_id=actor_user_id,
            )

            db.session.commit()
            return service

        except ServiceValidationError:
            raise
        except Exception as exc:
            db.session.rollback()
            raise ServiceServiceError("Erro ao atualizar serviço.") from exc

    @staticmethod
    def delete_service(service, actor_user_id):
        try:
            log_action(
                "delete_service",
                "service",
                service.id,
                f"Serviço {service.name} excluído.",
                company_id=service.company_id,
                user_id=actor_user_id,
            )

            db.session.delete(service)
            db.session.commit()

        except Exception as exc:
            db.session.rollback()
            raise ServiceServiceError("Erro ao excluir serviço.") from exc