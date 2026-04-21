"""add portal access to customer"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = "0485f4b25322"
down_revision = "5d525a59c894"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("customer", schema=None) as batch_op:
        batch_op.add_column(sa.Column("password_hash", sa.String(length=255), nullable=True))

        batch_op.add_column(
            sa.Column(
                "is_portal_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false()
            )
        )

        batch_op.add_column(
            sa.Column(
                "must_change_password",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false()
            )
        )

        batch_op.add_column(
            sa.Column("last_login_at", sa.DateTime(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("customer", schema=None) as batch_op:
        batch_op.drop_column("last_login_at")
        batch_op.drop_column("must_change_password")
        batch_op.drop_column("is_portal_active")
        batch_op.drop_column("password_hash")