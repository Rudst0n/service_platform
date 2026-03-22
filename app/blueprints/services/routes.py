import os
import uuid

from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.blueprints.services import services_bp
from app.extensions import db
from app.models.service import Service
from app.models.customer import Customer
from app.models.service_image import ServiceImage


PLANS = {
    "free": 3,
    "basic": 10,
    "pro": 50
}


@services_bp.route("/")
@login_required
def list_services():
    services = (
        Service.query
        .filter_by(company_id=current_user.company_id)
        .order_by(Service.id.desc())
        .all()
    )

    company_plan = getattr(current_user.company, "plan", "free") if hasattr(current_user, "company") else "free"
    image_limit = PLANS.get(company_plan, 3)

    service_cards = []

    for service in services:
        total_images = len(service.images)
        remaining = max(image_limit - total_images, 0)
        usage_percent = (total_images / image_limit * 100) if image_limit > 0 else 0

        if total_images >= image_limit:
            progress_class = "bg-danger"
        elif total_images >= (image_limit * 0.7):
            progress_class = "bg-warning"
        else:
            progress_class = "bg-success"

        images_orcamento = [img for img in service.images if img.type == "orcamento"]
        images_antes = [img for img in service.images if img.type == "antes"]
        images_depois = [img for img in service.images if img.type == "depois"]

        service_cards.append({
            "service": service,
            "total_images": total_images,
            "remaining": remaining,
            "usage_percent": usage_percent,
            "progress_class": progress_class,
            "images_orcamento": images_orcamento,
            "images_antes": images_antes,
            "images_depois": images_depois,
        })

    return render_template(
        "services/services.html",
        service_cards=service_cards,
        company_plan=company_plan,
        image_limit=image_limit
    )


@services_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_service():
    customers = (
        Customer.query
        .filter_by(company_id=current_user.company_id)
        .order_by(Customer.name.asc())
        .all()
    )

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", "").strip()
        customer_id = request.form.get("customer_id", "").strip()

        if not name or not customer_id:
            flash("Nome e cliente são obrigatórios.", "danger")
            return render_template("services/new_service.html", customers=customers)

        customer = Customer.query.filter_by(
            id=customer_id,
            company_id=current_user.company_id
        ).first()

        if not customer:
            flash("Cliente inválido.", "danger")
            return render_template("services/new_service.html", customers=customers)

        service = Service(
            name=name,
            description=description or None,
            price=float(price) if price else None,
            customer_id=customer.id,
            company_id=current_user.company_id
        )

        db.session.add(service)
        db.session.commit()

        flash("Serviço criado com sucesso.", "success")
        return redirect(url_for("services.list_services"))

    return render_template("services/new_service.html", customers=customers)


@services_bp.route("/<int:service_id>/upload", methods=["POST"])
@login_required
def upload_image(service_id):
    service = Service.query.filter_by(
        id=service_id,
        company_id=current_user.company_id
    ).first_or_404()

    files = request.files.getlist("image")
    image_type = request.form.get("type", "orcamento")

    if not files or all(file.filename == "" for file in files):
        flash("Nenhuma imagem enviada.", "danger")
        return redirect(url_for("services.list_services"))

    company_plan = getattr(current_user.company, "plan", "free") if hasattr(current_user, "company") else "free"
    limit = PLANS.get(company_plan, 3)

    total_images = ServiceImage.query.filter_by(service_id=service.id).count()
    remaining_slots = limit - total_images

    valid_files = [file for file in files if file and file.filename != ""]

    if remaining_slots <= 0:
        flash("Limite de imagens atingido para seu plano.", "warning")
        return redirect(url_for("services.list_services"))

    if len(valid_files) > remaining_slots:
        flash(f"Seu plano permite enviar mais {remaining_slots} imagem(ns) para este serviço.", "warning")
        return redirect(url_for("services.list_services"))

    upload_folder = "app/static/uploads/services"
    os.makedirs(upload_folder, exist_ok=True)

    for file in valid_files:
        filename = secure_filename(file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"

        file_path_abs = os.path.join(upload_folder, unique_name)
        file.save(file_path_abs)

        image = ServiceImage(
            file_path=f"uploads/services/{unique_name}",
            service_id=service.id,
            company_id=current_user.company_id,
            uploaded_by="empresa",
            type=image_type
        )

        db.session.add(image)

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

    absolute_path = os.path.join("app/static", image.file_path)

    if os.path.exists(absolute_path):
        try:
            os.remove(absolute_path)
        except OSError:
            pass

    db.session.delete(image)
    db.session.commit()

    flash("Imagem removida com sucesso.", "success")
    return redirect(url_for("services.list_services"))


@services_bp.route("/<int:service_id>/delete", methods=["POST"])
@login_required
def delete_service(service_id):
    service = Service.query.filter_by(
        id=service_id,
        company_id=current_user.company_id
    ).first_or_404()

    for image in service.images:
        absolute_path = os.path.join("app/static", image.file_path)
        if os.path.exists(absolute_path):
            try:
                os.remove(absolute_path)
            except OSError:
                pass

    db.session.delete(service)
    db.session.commit()

    flash("Serviço removido com sucesso.", "success")
    return redirect(url_for("services.list_services"))