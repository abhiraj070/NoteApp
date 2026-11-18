"""Create users and notes tables."""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("users",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("name", sa.String(), nullable=False),
                    sa.Column("username", sa.String(), nullable=False),
                    sa.Column("password", sa.String(), nullable=False),
                    sa.Column("refreshtoken", sa.String(), nullable=True))
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_table("notes",
                    sa.Column("id", sa.Integer(), primary_key=True),
                    sa.Column("content", sa.Text(), nullable=False),
                    sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False))
    op.create_index("ix_notes_user_id", "notes", ["user_id"])


def downgrade():
    op.drop_table("notes")
    op.drop_table("users")
