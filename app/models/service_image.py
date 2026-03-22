from datetime import datetime
from app.extensions import db


class ServiceImage(db.Model):
    __tablename__ = "service_images"

    id = db.Column(db.Integer, primary_key=True)

    file_path = db.Column(db.String(255), nullable=False)

    service_id = db.Column(db.Integer, db.ForeignKey("services.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)

    uploaded_by = db.Column(db.String(50), nullable=True)
    type = db.Column(db.String(20), nullable=False, default="orcamento")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ServiceImage {self.file_path}>"