"""Add stream ip address and port to applet

Revision ID: 46f285831ae8
Revises: 47405ad1f948
Create Date: 2024-01-09 14:20:00.181263

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "46f285831ae8"
down_revision = "47405ad1f948"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "applet_histories",
        sa.Column("stream_ip_address", sa.Text(), nullable=True),
    )
    op.add_column(
        "applet_histories",
        sa.Column("stream_port", sa.Integer(), nullable=True),
    )
    op.add_column(
        "applets", sa.Column("stream_ip_address", sa.Text(), nullable=True)
    )
    op.add_column(
        "applets", sa.Column("stream_port", sa.Integer(), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("applets", "stream_port")
    op.drop_column("applets", "stream_ip_address")
    op.drop_column("applet_histories", "stream_port")
    op.drop_column("applet_histories", "stream_ip_address")
    # ### end Alembic commands ###
