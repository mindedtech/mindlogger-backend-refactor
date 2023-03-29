import base64
import json
import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Query

from apps.answers.db.schemas import AnswerActivityItemsSchema
from apps.answers.domain import AppletAnswerCreate
from apps.applets.crud import AppletsCRUD
from apps.shared.encryption import decrypt, encrypt, generate_iv
from infrastructure.database.crud import BaseCRUD


class AnswerActivityItemsCRUD(BaseCRUD[AnswerActivityItemsSchema]):
    schema_class = AnswerActivityItemsSchema

    async def create_many(
        self, schemas: list[AnswerActivityItemsSchema]
    ) -> list[AnswerActivityItemsSchema]:
        applet = await AppletsCRUD(self.session).get_by_id(
            schemas[0].applet_id
        )
        system_encrypted_key = base64.b64decode(
            applet.system_encrypted_key.encode()
        )
        iv = generate_iv(str(applet.id))
        key = decrypt(system_encrypted_key, iv=iv)
        for schema in schemas:
            encrypted_answer = self._encrypt(
                schema.id, key, schema.answer.encode()
            )
            schema.answer = base64.b64encode(encrypted_answer).decode()

        schemas = await self._create_many(schemas)

        for schema in schemas:
            schema.answer = self._decrypt(
                schema.id, key, base64.b64decode(schema.answer.encode())
            ).decode()

        return schemas

    def _encrypt(
        self,
        unique_identifier: uuid.UUID,
        system_encrypted_key: bytes,
        value: bytes,
    ) -> bytes:
        iv = generate_iv(str(unique_identifier))
        key = decrypt(system_encrypted_key)
        encrypted_value = encrypt(value, key, iv)
        return encrypted_value

    def _decrypt(
        self,
        unique_identifier: uuid.UUID,
        system_encrypted_key: bytes,
        encrypted_value: bytes,
    ) -> bytes:
        iv = generate_iv(str(unique_identifier))
        key = decrypt(system_encrypted_key)
        answer = decrypt(encrypted_value, key, iv)
        return answer

    async def delete_by_applet_id(self, applet_id: uuid.UUID):
        query: Query = delete(AnswerActivityItemsSchema)
        query = query.where(AnswerActivityItemsSchema.applet_id == applet_id)
        await self._execute(query)

    async def get_for_answers_created(
        self,
        respondent_id: uuid.UUID,
        applet_answer: AppletAnswerCreate,
        activity_item_id_version,
    ) -> list[AnswerActivityItemsSchema]:

        answers = list()
        for activity_item_answer in applet_answer.answers:
            answers.append(json.dumps(activity_item_answer.answer.dict()))

        query: Query = select(AnswerActivityItemsSchema)
        query = query.where(
            AnswerActivityItemsSchema.applet_id == applet_answer.applet_id
        )
        query = query.where(
            AnswerActivityItemsSchema.respondent_id == respondent_id
        )
        query = query.where(
            AnswerActivityItemsSchema.activity_item_history_id
            == activity_item_id_version
        )
        query = query.where(AnswerActivityItemsSchema.answer.in_(answers))

        result = await self._execute(query)

        return result.scalars().all()
