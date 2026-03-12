from app.extensions import db


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(150))

    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)