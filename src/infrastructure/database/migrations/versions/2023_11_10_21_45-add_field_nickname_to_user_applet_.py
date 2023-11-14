"""Add field nickname to user_applet_accesses

Revision ID: a7faad5855cc
Revises: 8c59c7363c67
Create Date: 2023-11-10 21:45:42.636562

"""
from alembic import op
import sqlalchemy as sa
import json

from sqlalchemy_utils.types.encrypted.encrypted_type import StringEncryptedType
from apps.shared.encryption import decrypt, encrypt, get_key


# revision identifiers, used by Alembic.
revision = "a7faad5855cc"
down_revision = "8c59c7363c67"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT id, meta FROM user_applet_accesses WHERE role='respondent'"
        )
    )
    op.add_column(
        "user_applet_accesses",
        sa.Column(
            "nickname",
            StringEncryptedType(sa.Unicode, get_key),
            nullable=True,
        ),
    )
    for row in result:
        pk, meta = row
        nickname = meta.get("nickname")
        if nickname and nickname != "":
            encrypted_field = StringEncryptedType(
                sa.Unicode, get_key
            ).process_bind_param(nickname, dialect=conn.dialect)
            meta["nickname"] = None
            print(encrypted_field)
            print(meta)
            conn.execute(
                sa.text(
                    f"""
                        UPDATE user_applet_accesses 
                        SET nickname = :encrypted_field, meta= :meta
                        WHERE id = :pk
                    """
                ),
                {
                    "encrypted_field": encrypted_field,
                    "meta": json.dumps(meta),
                    "pk": pk,
                },
            )

    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT id, nickname, meta FROM user_applet_accesses  WHERE role='respondent'"
        )
    )
    print(result)
    op.drop_column("user_applet_accesses", "nickname")
    for row in result:
        pk, nickname, meta = row
        if nickname is not None:
            print(nickname)
            decrypted_field = StringEncryptedType(
                sa.Unicode, get_key
            ).process_result_value(nickname, dialect=conn.dialect)
            meta["nickname"] = decrypted_field
            print(meta)
            conn.execute(
                sa.text(
                    f"""
                        UPDATE user_applet_accesses
                        SET meta = :decrypted_field
                        WHERE id = :pk
                    """
                ),
                {"decrypted_field": json.dumps(meta), "pk": pk},
            )
    # ### end Alembic commands ###
