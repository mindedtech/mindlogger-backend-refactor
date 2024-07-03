"""Add new input_subject_id to answers

Revision ID: f436ffa84be1
Revises: f099d463803a
Create Date: 2024-06-10 14:16:51.674859

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "f436ffa84be1"
down_revision = "f099d463803a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "answers",
        sa.Column(
            "input_subject_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
    )
    op.create_index(
        op.f("ix_answers_input_subject_id"),
        "answers",
        ["input_subject_id"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_answers_input_subject_id"), table_name="answers")
    op.drop_column("answers", "input_subject_id")
    # ### end Alembic commands ###
