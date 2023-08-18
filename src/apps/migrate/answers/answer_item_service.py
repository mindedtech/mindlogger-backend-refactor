from apps.answers.crud import AnswerItemsCRUD
from apps.answers.db.schemas import AnswerItemSchema, AnswerSchema
from apps.girderformindlogger.models.item import Item
from apps.migrate.utilities import mongoid_to_uuid
from infrastructure.database import session_manager, atomic
from datetime import datetime


class AnswerItemMigrationService:
    async def create_item(self, *, session, mongo_answer: dict, **kwargs):
        identifier = mongo_answer["meta"]["subject"].get("identifier", "")
        answer_item = await AnswerItemsCRUD(session).create(
            AnswerItemSchema(
                created_at=mongo_answer["created"],
                updated_at=mongo_answer["updated"],
                answer_id=kwargs["answer_id"],
                answer=mongo_answer["meta"]["dataSource"],
                item_ids=self._get_item_ids(mongo_answer),
                events=mongo_answer["meta"].get("events", ""),
                respondent_id=mongoid_to_uuid(mongo_answer["creatorId"]),
                identifier=mongo_answer["meta"]["subject"].get(
                    "identifier", ""
                ),
                user_public_key=str(mongo_answer["meta"]["userPublicKey"]),
                scheduled_datetime=self._fromtimestamp(
                    mongo_answer["meta"].get("scheduledTime")
                ),
                start_datetime=self._fromtimestamp(
                    mongo_answer["meta"].get("responseStarted")
                ),
                end_datetime=self._fromtimestamp(
                    mongo_answer["meta"].get("responseCompleted")
                ),
                is_assessment=kwargs["is_assessment"],
                migrated_date=datetime.now(),
                migrated_data=self._get_migrated_data(identifier),
            )
        )
        return answer_item

    def _get_migrated_data(self, identifier):
        if not identifier:
            return None
        return {"is_identifier_encrypted": True}

    def _get_item_ids(self, mongo_answer):
        responses_keys = list(mongo_answer["meta"]["responses"])

        if not all([k.startswith("http") for k in responses_keys]):
            return [
                str(mongoid_to_uuid(k.split("/")[1]))
                for k in list(mongo_answer["meta"]["responses"])
            ]

        return [
            str(
                mongoid_to_uuid(i["_id"])
                for i in Item().find(
                    query={
                        "meta.activityId": mongo_answer["meta"]["activity"][
                            "@id"
                        ],
                        "meta.screen.schema:url": {"$in": responses_keys},
                    }
                )
            )
        ]

    def _fromtimestamp(self, timestamp: int | None):
        if timestamp is None:
            return None
        return datetime.fromtimestamp((float(timestamp) / 1000))
