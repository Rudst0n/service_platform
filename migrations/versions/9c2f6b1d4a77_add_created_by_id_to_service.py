"""add created_by_id to service

Revision ID: 9c2f6b1d4a77
Revises: 1bef9fed11eb
Create Date: 2026-04-14 17:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "9c2f6b1d4a77"
down_revision = "1bef9fed11eb"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("services", sa.Column("created_by_id", sa.Integer(), nullable=True))

    connection = op.get_bind()

    connection.execute(sa.text("""
        UPDATE services
        SET created_by_id = assigned_to_id
        WHERE assigned_to_id IS NOT NULL
    """))

    connection.execute(sa.text("""
        UPDATE services
        SET created_by_id = (
            SELECT MIN(u.id)
            FROM user AS u
            WHERE u.company_id = services.company_id
        )
        WHERE created_by_id IS NULL
    """))

    op.alter_column("services", "created_by_id", nullable=False)

    op.create_foreign_key(
        "fk_services_created_by_id_user",
        "services",
        "user",
        ["created_by_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("fk_services_created_by_id_user", "services", type_="foreignkey")
    op.drop_column("services", "created_by_id")