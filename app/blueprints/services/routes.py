from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from PIL import Image, UnidentifiedImageError

from app.blueprints.services import services_bp
from app.extensions import db
from app.models.customer import Customer
from app.models.service import Service
from app.models.service_image import ServiceImage
from app.models.user import User
from app.utils.access import block_if_trial_expired
from app.utils.audit import log_action
from app.utils.permissions import (
    can_create_service,
    can_delete_service,
    can_edit_service,
    can_update_service_status,
    can_upload_service_image,
    is_company_admin,
    is_employee,
    is_viewer,
)
from app.utils.plan_limits import is_limit_reached
from app.utils.storage import save_private_file


IMAGE_LIMITS = {
    "starter": 10,
    "pro": 50,
    "business": 200,
}

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_IMAGE_TYPES = {"orcamento", "antes", "depois"}
VALID_STATUS = ["orcamento", "aprovado", "em_andamento", "finalizado", "cancelado"]
EMPLOYEE_ALLOWED_STATUS = {"em_andamento", "finalizado"}


def allowed_image_file(filename):
    if not filename or "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_IMAGE_EXTENSIONS


def is_real_image(file_storage):
    file_storage.stream.seek(0)
    try:
        image = Image.open(file_storage.stream)
        image.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        file_storage.stream.seek(0)
        return False
    file_storage.stream.seek(0)
    return True


def get_service_form_options():
    customers = (
        Customer.query
        .filter_by(company_id=current_user.company_id)
        .order_by(Customer.name.asc())
        .all()
    )
    users = (
        User.query
        .filter_by(company_id=current_user.company_id, is_active=True)
        .order_by(User.name.asc())
        .all()
    )
    return customers, users


def get_service_or_404(service_id):
    return Service.query.filter_by(
        id=service_id,
        company_id=current_user.company_id
    ).first_or_404()


def resolve_viewer_customer():
    customer = None

    if current_user.email:
        customer = Customer.query.filter_by(
            company_id=current_user.company_id,
            email=current_user.email
        ).first()

    if not customer and current_user.cpf:
        customer = Customer.query.filter_by(
            company_id=current_user.company_id,
            cpf=current_user.cpf
        ).first()

    return customer


def validate_service_form(name, customer_id, assigned_to_id, price_raw):
    if not name or not customer_id:
        return False, "Nome e cliente são obrigatórios.", None, None, None

    customer = Customer.query.filter_by(
        id=customer_id,
        company_id=current_user.company_id
    ).first()
    if not customer:
        return False, "Cliente inválido.", None, None, None

    assigned_user = None
    if assigned_to_id:
        assigned_user = User.query.filter_by(
            id=assigned_to_id,
            company_id=current_user.company_id,
            is_active=True,
        ).first()
        if not assigned_user:
            return False, "Responsável inválido.", None, None, None

    price = None
    if price_raw:
        normalized_price = price_raw.replace(",", ".")
        try:
            price = Decimal(normalized_price)
            if price < 0:
                return False, "Preço inválido.", None, None, None
        except InvalidOperation:
            return False, "Preço inválido.", None, None, None

    return True, None, customer, assigned_user, price


def get_private_image_path(image):
    return Path(current_app.config["UPLOAD_FOLDER"]) / image.file_path


@services_bp.route("/")
@login_required
def list_services():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()
    customer_filter = request.args.get("customer_id", type=int)

    if is_employee():
        query = Service.query.filter_by(
            company_id=current_user.company_id,
            assigned_to_id=current_user.id
        ).filter(Service.status != "finalizado")

    elif is_viewer():
        query = Service.query.filter_by(
            company_id=current_user.company_id,
            created_by_id=current_user.id
        ).filter(Service.status != "finalizado")

    else:
        query = Service.query.filter_by(
            company_id=current_user.company_id
        ).filter(Service.status != "finalizado")

    if search:
        query = query.filter(
            (Service.name.ilike(f"%{search}%")) |
            (Service.request_code.ilike(f"%{search}%"))
        )

    if status_filter:
        query = query.filter(Service.status == status_filter)

    if customer_filter and not is_viewer():
        query = query.filter(Service.customer_id == customer_filter)

    pagination = (
        query.order_by(Service.id.desc())
        .paginate(page=page, per_page=10, error_out=False)
    )
    services = pagination.items

    company_plan = getattr(current_user.company, "plan", "starter")
    image_limit = IMAGE_LIMITS.get(company_plan, 10)
    customers = (
        Customer.query
        .filter_by(company_id=current_user.company_id)
        .order_by(Customer.name.asc())
        .all()
    ) if not is_viewer() else []

    service_cards = []
    for service in services:
        total_images = len(service.images)
        remaining = max(image_limit - total_images, 0)
        usage_percent = (total_images / image_limit * 100) if image_limit > 0 else 0

        if total_images >= image_limit:
            progress_class = "bg-danger"
        elif total_images >= image_limit * 0.7:
            progress_class = "bg-warning"
        else:
            progress_class = "bg-success"

        service_cards.append(
            {
                "service": service,
                "total_images": total_images,
                "remaining": remaining,
                "usage_percent": usage_percent,
                "progress_class": progress_class,
                "images_orcamento": [img for img in service.images if img.type == "orcamento"],
                "images_antes": [img for img in service.images if img.type == "antes"],
                "images_depois": [img for img in service.images if img.type == "depois"],
            }
        )

    return render_template(
        "services/services.html",
        service_cards=service_cards,
        company_plan=company_plan,
        image_limit=image_limit,
        customers=customers,
        search=search,
        status_filter=status_filter,
        customer_filter=customer_filter,
        pagination=pagination,
    )


@services_bp.route("/history")
@login_required
def services_history():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip()
    customer_filter = request.args.get("customer_id", type=int)

    if is_employee():
        query = Service.query.filter_by(
            company_id=current_user.company_id,
            assigned_to_id=current_user.id,
            status="finalizado",
        )

    elif is_viewer():
        query = Service.query.filter_by(
            company_id=current_user.company_id,
            created_by_id=current_user.id,
            status="finalizado",
        )

    else:
        query = Service.query.filter_by(
            company_id=current_user.company_id,
            status="finalizado",
        )

    if search:
        query = query.filter(
            (Service.name.ilike(f"%{search}%")) |
            (Service.request_code.ilike(f"%{search}%"))
        )

    if customer_filter and not is_viewer():
        query = query.filter(Service.customer_id == customer_filter)

    pagination = (
        query.order_by(Service.finished_at.desc(), Service.id.desc())
        .paginate(page=page, per_page=10, error_out=False)
    )

    customers = (
        Customer.query
        .filter_by(company_id=current_user.company_id)
        .order_by(Customer.name.asc())
        .all()
    ) if not is_viewer() else []

    return render_template(
        "services/services_history.html",
        services=pagination.items,
        pagination=pagination,
        customers=customers,
        search=search,
        customer_filter=customer_filter,
    )


@services_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_service():
    if not can_create_service():
        flash("Você não tem permissão para cadastrar serviços.", "danger")
        return redirect(url_for("services.list_services"))

    customers, users = get_service_form_options()

    if request.method == "POST":
        trial_block = block_if_trial_expired("serviços")
        if trial_block:
            return trial_block

        if is_limit_reached(current_user.company, Service, "services"):
            flash("Você atingiu o limite de serviços do seu plano.", "warning")
            return redirect(url_for("services.list_services"))

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price_raw = request.form.get("price", "").strip()
        customer_id = request.form.get("customer_id", "").strip()
        status = request.form.get("status", "orcamento").strip()
        assigned_to_raw = request.form.get("assigned_to_id", "").strip()

        if is_employee():
            status = "orcamento"
            assigned_to_id = current_user.id
            valid, error, customer, _, price = validate_service_form(
                name, customer_id, assigned_to_id, price_raw
            )
            assigned_user_id = current_user.id

        elif is_viewer():
            status = "orcamento"
            assigned_user_id = None
            price = None

            customer = resolve_viewer_customer()

            if not name:
                valid = False
                error = "Nome do serviço é obrigatório."
            elif not customer:
                valid = False
                error = "Não foi possível identificar seu cadastro de cliente. Cadastre um cliente com o mesmo e-mail ou CPF do seu usuário."
            else:
                valid = True
                error = None

        else:
            if status not in VALID_STATUS:
                status = "orcamento"

            valid, error, customer, assigned_user, price = validate_service_form(
                name, customer_id, assigned_to_raw, price_raw
            )

            assigned_user_id = assigned_user.id if assigned_user else None

        if not valid:
            flash(error, "danger")
            return render_template(
                "services/new_service.html",
                customers=customers,
                users=users,
                service=None,
            )

        last_service = (
            Service.query
            .filter_by(company_id=current_user.company_id)
            .order_by(Service.request_number.desc(), Service.id.desc())
            .first()
        )

        next_number = 1 if not last_service else last_service.request_number + 1
        request_code = f"REQ-{str(next_number).zfill(3)}"

        service = Service(
            request_number=next_number,
            request_code=request_code,
            name=name,
            description=description or None,
            price=price,
            status=status,
            customer_id=customer.id,
            company_id=current_user.company_id,
            assigned_to_id=assigned_user_id,
            created_by_id=current_user.id,
        )

        db.session.add(service)
        db.session.flush()

        log_action(
            "create_service",
            "service",
            service.id,
            f"Serviço {request_code} {name} criado com status {status}.",
            company_id=current_user.company_id,
            user_id=current_user.id,
        )

        db.session.commit()

        flash(f"Serviço {request_code} criado com sucesso.", "success")
        return redirect(url_for("services.list_services"))

    return render_template(
        "services/new_service.html",
        customers=customers,
        users=users,
        service=None,
    )


@services_bp.route("/<int:service_id>/edit", methods=["GET", "POST"])
@login_required
def edit_service(service_id):
    service = get_service_or_404(service_id)

    if not can_edit_service(service):
        flash("Você não tem permissão para editar este serviço.", "danger")
        return redirect(url_for("services.list_services"))

    customers, users = get_service_form_options()

    if request.method == "POST":
        trial_block = block_if_trial_expired("serviços")
        if trial_block:
            return trial_block

        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price_raw = request.form.get("price", "").strip()
        customer_id = request.form.get("customer_id", "").strip()
        status = request.form.get("status", service.status).strip()
        assigned_to_id = request.form.get("assigned_to_id", "").strip()

        if is_employee():
            assigned_to_id = str(service.assigned_to_id) if service.assigned_to_id else ""
            if status != service.status and status not in EMPLOYEE_ALLOWED_STATUS:
                flash("Você não pode definir esse status.", "danger")
                return render_template(
                    "services/new_service.html",
                    customers=customers,
                    users=users,
                    service=service,
                )
        else:
            if status not in VALID_STATUS:
                status = service.status

        valid, error, customer, assigned_user, price = validate_service_form(
            name, customer_id, assigned_to_id, price_raw
        )
        if not valid:
            flash(error, "danger")
            return render_template(
                "services/new_service.html",
                customers=customers,
                users=users,
                service=service,
            )

        service.name = name
        service.description = description or None
        service.price = price
        service.customer_id = customer.id

        if is_company_admin() or current_user.is_super_admin:
            service.status = status
            service.assigned_to_id = assigned_user.id if assigned_user else None
        else:
            if status in EMPLOYEE_ALLOWED_STATUS:
                service.status = status

        if service.status == "finalizado" and service.finished_at is None:
            service.finished_at = datetime.utcnow()
        elif service.status != "finalizado":
            service.finished_at = None

        log_action(
            "update_service",
            "service",
            service.id,
            f"Serviço {service.request_code} {service.name} atualizado.",
            company_id=current_user.company_id,
            user_id=current_user.id,
        )

        db.session.commit()

        flash("Serviço atualizado com sucesso.", "success")
        return redirect(url_for("services.list_services"))

    return render_template(
        "services/new_service.html",
        customers=customers,
        users=users,
        service=service,
    )


@services_bp.route("/<int:service_id>/update-status", methods=["POST"])
@login_required
def update_status(service_id):
    service = get_service_or_404(service_id)

    if not can_update_service_status(service):
        flash("Você não tem permissão para alterar este serviço.", "danger")
        return redirect(url_for("services.list_services"))

    if is_employee():
        allowed_status = EMPLOYEE_ALLOWED_STATUS
    else:
        allowed_status = set(VALID_STATUS)

    status = request.form.get("status", "").strip()
    if status not in allowed_status:
        flash("Status inválido para seu perfil.", "danger")
        return redirect(url_for("services.list_services"))

    service.status = status

    if status == "finalizado":
        service.finished_at = datetime.utcnow()
    else:
        service.finished_at = None

    log_action(
        "update_service_status",
        "service",
        service.id,
        f"Status do serviço {service.request_code} alterado para {status}.",
        company_id=current_user.company_id,
        user_id=current_user.id,
    )

    db.session.commit()

    flash("Status atualizado com sucesso.", "success")
    return redirect(url_for("services.list_services"))


@services_bp.route("/<int:service_id>/upload", methods=["POST"])
@login_required
def upload_image(service_id):
    service = get_service_or_404(service_id)

    if not can_upload_service_image(service):
        flash("Você não tem permissão para enviar imagens para este serviço.", "danger")
        return redirect(url_for("services.list_services"))

    files = request.files.getlist("image")
    image_type = request.form.get("type", "orcamento").strip().lower()

    if image_type not in ALLOWED_IMAGE_TYPES:
        flash("Tipo de imagem inválido.", "danger")
        return redirect(url_for("services.list_services"))

    if not files or all(not file.filename for file in files):
        flash("Nenhuma imagem enviada.", "danger")
        return redirect(url_for("services.list_services"))

    company_plan = getattr(current_user.company, "plan", "starter")
    limit = IMAGE_LIMITS.get(company_plan, 10)
    total_images = ServiceImage.query.filter_by(service_id=service.id).count()
    remaining_slots = limit - total_images
    valid_files = [file for file in files if file and file.filename]

    if remaining_slots <= 0:
        flash("Limite de imagens atingido para seu plano.", "warning")
        return redirect(url_for("services.list_services"))

    if len(valid_files) > remaining_slots:
        flash(f"Seu plano permite enviar mais {remaining_slots} imagem(ns) para este serviço.", "warning")
        return redirect(url_for("services.list_services"))

    for file in valid_files:
        if not allowed_image_file(file.filename):
            flash("Formato de arquivo inválido. Envie apenas PNG, JPG, JPEG ou WEBP.", "danger")
            return redirect(url_for("services.list_services"))
        if not is_real_image(file):
            flash("Um dos arquivos enviados não é uma imagem válida.", "danger")
            return redirect(url_for("services.list_services"))

    for file in valid_files:
        saved_path = save_private_file(
            file,
            subfolder=f"companies/{current_user.company_id}/services/{service.id}"
        )

        image = ServiceImage(
            file_path=saved_path,
            service_id=service.id,
            company_id=current_user.company_id,
            uploaded_by="empresa",
            type=image_type,
        )
        db.session.add(image)

    log_action(
        "upload_service_image",
        "service",
        service.id,
        f"Imagem adicionada ao serviço {service.request_code} {service.name}.",
        company_id=current_user.company_id,
        user_id=current_user.id,
    )

    db.session.commit()

    flash("Imagem(ns) enviada(s) com sucesso.", "success")
    return redirect(url_for("services.list_services"))


@services_bp.route("/image/<int:image_id>/delete", methods=["POST"])
@login_required
def delete_image(image_id):
    image = ServiceImage.query.filter_by(
        id=image_id,
        company_id=current_user.company_id
    ).first_or_404()

    service = get_service_or_404(image.service_id)

    if not can_upload_service_image(service):
        flash("Você não tem permissão para excluir imagens deste serviço.", "danger")
        return redirect(url_for("services.list_services"))

    absolute_path = get_private_image_path(image)
    if absolute_path.exists():
        try:
            absolute_path.unlink()
        except OSError:
            pass

    log_action(
        "delete_service_image",
        "service_image",
        image.id,
        f"Imagem removida do serviço {service.request_code} {service.name}.",
        company_id=current_user.company_id,
        user_id=current_user.id,
    )

    db.session.delete(image)
    db.session.commit()

    flash("Imagem removida com sucesso.", "success")
    return redirect(url_for("services.list_services"))


@services_bp.route("/<int:service_id>/delete", methods=["POST"])
@login_required
def delete_service(service_id):
    if not can_delete_service():
        flash("Você não tem permissão para excluir serviços.", "danger")
        return redirect(url_for("services.list_services"))

    service = get_service_or_404(service_id)

    for image in service.images:
        absolute_path = get_private_image_path(image)
        if absolute_path.exists():
            try:
                absolute_path.unlink()
            except OSError:
                pass

    log_action(
        "delete_service",
        "service",
        service.id,
        f"Serviço {service.request_code} {service.name} excluído.",
        company_id=current_user.company_id,
        user_id=current_user.id,
    )

    db.session.delete(service)
    db.session.commit()

    flash("Serviço removido com sucesso.", "success")
    return redirect(url_for("services.list_services"))