"""add must_change_password to user

Revision ID: 1bef9fed11eb
Revises: 5aa4e96ded62
Create Date: 2026-04-12

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1bef9fed11eb"
down_revision = "5aa4e96ded62"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("must_change_password", sa.Boolean(), nullable=True))

    connection = op.get_bind()

    connection.execute(
        sa.text("""
            UPDATE user
            SET must_change_password = 0
            WHERE must_change_password IS NULL
        """)
    )

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column(
            "must_change_password",
            existing_type=sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("must_change_password")