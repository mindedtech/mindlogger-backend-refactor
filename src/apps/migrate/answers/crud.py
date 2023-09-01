import uuid

from sqlalchemy import select, func
from sqlalchemy.orm import Query

from apps.activities.db.schemas import ActivityHistorySchema
from apps.activity_flows.db.schemas import ActivityFlowHistoriesSchema
from apps.answers.crud.answers import AnswersCRUD
from apps.migrate.utilities import uuid_to_mongoid


class MigrateAnswersCRUD(AnswersCRUD):
    async def get_answers_migration_params(self):
        query: Query = select(
            ActivityHistorySchema.id,
            func.split_part(ActivityHistorySchema.applet_id, "_", 1).label(
                "applet_id"
            ),
            func.split_part(ActivityHistorySchema.applet_id, "_", 2).label(
                "version"
            ),
        )

        db_result = await self._execute(query)
        db_result = db_result.all()
        result = []
        for row in db_result:
            result.append(
                {
                    "activity_id": uuid_to_mongoid(row[0]),
                    "applet_id": uuid_to_mongoid(uuid.UUID(row[1])),
                    "version": row[2],
                }
            )
        return result

    async def get_flow_history_id_version(self, flow_id: str):
        query: Query = select(ActivityFlowHistoriesSchema.id_version).where(
            ActivityFlowHistoriesSchema.id == flow_id
        )
        db_result = await self._execute(query)
        db_result = db_result.scalars().one_or_none()
        return db_result