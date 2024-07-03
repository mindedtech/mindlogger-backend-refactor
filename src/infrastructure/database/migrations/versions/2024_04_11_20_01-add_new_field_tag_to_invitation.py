"""Add new field tag to invitation

Revision ID: a38714b9e23b
Revises: 809b07a71159
Create Date: 2024-04-11 20:01:34.420307

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a38714b9e23b"
down_revision = "809b07a71159"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("invitations", sa.Column("tag", sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("invitations", "tag")
    # ### end Alembic commands ###
