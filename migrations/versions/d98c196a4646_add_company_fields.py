from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d98c196a4646"
down_revision = "63ad2059fe5f"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("company", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "plan",
                sa.String(length=50),
                nullable=False,
                server_default="starter"
            )
        )
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("'2026-01-01 00:00:00'")
            )
        )
        batch_op.add_column(
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("1")
            )
        )


def downgrade():
    with op.batch_alter_table("company", schema=None) as batch_op:
        batch_op.drop_column("is_active")
        batch_op.drop_column("created_at")
        batch_op.drop_column("plan")