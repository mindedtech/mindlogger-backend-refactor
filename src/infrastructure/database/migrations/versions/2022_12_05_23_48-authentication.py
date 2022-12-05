"""authentication

Revision ID: 00d6c68a3b4e
Revises: 
Create Date: 2022-12-05 23:48:46.299774

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "00d6c68a3b4e"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=True),
        sa.Column("email", sa.String(length=100), nullable=True),
        sa.Column("access_token", sa.String(length=256), nullable=True),
        sa.Column("refresh_token", sa.String(length=256), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=True),
        sa.Column("email", sa.String(length=100), nullable=True),
        sa.Column("full_name", sa.String(length=100), nullable=True),
        sa.Column("hashed_password", sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("users")
    op.drop_table("tokens")
    # ### end Alembic commands ###
