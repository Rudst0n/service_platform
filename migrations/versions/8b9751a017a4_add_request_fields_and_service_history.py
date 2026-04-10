"""add request fields and service history

Revision ID: 8b9751a017a4
Revises: 8f4c2b1a9d10
Create Date: 2026-04-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8b9751a017a4"
down_revision = "8f4c2b1a9d10"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("services", schema=None) as batch_op:
        batch_op.add_column(sa.Column("request_number", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("request_code", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("finished_at", sa.DateTime(), nullable=True))

    connection = op.get_bind()

    services = connection.execute(
        sa.text("""
            SELECT id, name, company_id, status, created_at
            FROM services
            ORDER BY company_id, id
        """)
    ).fetchall()

    counters = {}

    for service in services:
        company_id = service.company_id
        counters[company_id] = counters.get(company_id, 0) + 1
        request_number = counters[company_id]
        request_code = f"REQ-{request_number:03d}"

        finished_at = service.created_at if service.status == "finalizado" else None

        connection.execute(
            sa.text("""
                UPDATE services
                SET request_number = :request_number,
                    request_code = :request_code,
                    finished_at = :finished_at
                WHERE id = :id
            """),
            {
                "request_number": request_number,
                "request_code": request_code,
                "finished_at": finished_at,
                "id": service.id,
            }
        )

    with op.batch_alter_table("services", schema=None) as batch_op:
        batch_op.alter_column("request_number", existing_type=sa.Integer(), nullable=False)
        batch_op.alter_column("request_code", existing_type=sa.String(length=20), nullable=False)


def downgrade():
    with op.batch_alter_table("services", schema=None) as batch_op:
        batch_op.drop_column("finished_at")
        batch_op.drop_column("request_code")
        batch_op.drop_column("request_number")