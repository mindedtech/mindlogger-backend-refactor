import asyncio
import uuid
from collections import defaultdict

from apps.activities.crud import ActivitiesCRUD
from apps.activities.db.schemas import ActivitySchema
from apps.activity_assignments.crud.assignments import ActivityAssigmentCRUD
from apps.activity_assignments.db.schemas import ActivityAssigmentSchema
from apps.activity_assignments.domain.assignments import (
    ActivityAssignment,
    ActivityAssignmentCreate,
    ActivityAssignmentWithSubject,
)
from apps.activity_flows.crud import FlowsCRUD
from apps.activity_flows.db.schemas import ActivityFlowSchema
from apps.applets.crud import AppletsCRUD
from apps.invitations.crud import InvitationCRUD
from apps.mailing.domain import MessageSchema
from apps.mailing.services import MailingService
from apps.shared.exception import NotFoundError, ValidationError
from apps.shared.query_params import QueryParams
from apps.subjects.crud import SubjectsCrud
from apps.subjects.db.schemas import SubjectSchema
from apps.subjects.domain import SubjectReadResponse
from config import settings


class ActivityAssignmentService:
    class _AssignmentEntities:
        activities: dict[uuid.UUID, ActivitySchema]
        flows: dict[uuid.UUID, ActivityFlowSchema]
        respondent_subjects: dict[uuid.UUID, SubjectSchema]
        target_subjects: dict[uuid.UUID, SubjectSchema]

    def __init__(self, session):
        self.session = session

    async def create_many(
        self, applet_id: uuid.UUID, assignments_create: list[ActivityAssignmentCreate]
    ) -> list[ActivityAssignment]:
        entities = await self._get_assignments_entities(applet_id, assignments_create)

        respondent_activities: dict[uuid.UUID, set[str]] = defaultdict(set)
        schemas = []
        for assignment in assignments_create:
            activity_or_flow_name: str = self._validate_assignment_and_get_activity_or_flow_name(assignment, entities)
            schema = ActivityAssigmentSchema(
                id=uuid.uuid4(),
                activity_id=assignment.activity_id,
                activity_flow_id=assignment.activity_flow_id,
                respondent_subject_id=assignment.respondent_subject_id,
                target_subject_id=assignment.target_subject_id,
            )
            if await ActivityAssigmentCRUD(self.session).already_exists(schema):
                continue

            schemas.append(schema)

            pending_invitation = await InvitationCRUD(self.session).get_pending_subject_invitation(
                applet_id, assignment.respondent_subject_id
            )
            if not pending_invitation:
                respondent_activities[assignment.respondent_subject_id].add(activity_or_flow_name)

        assignment_schemas: list[ActivityAssigmentSchema] = await ActivityAssigmentCRUD(self.session).create_many(
            schemas
        )

        await self.send_email_notification(applet_id, entities.respondent_subjects, respondent_activities)

        return [
            ActivityAssignment(
                id=assignment.id,
                activity_id=assignment.activity_id,
                activity_flow_id=assignment.activity_flow_id,
                respondent_subject_id=assignment.respondent_subject_id,
                target_subject_id=assignment.target_subject_id,
            )
            for assignment in assignment_schemas
        ]

    async def check_for_assignment_and_notify(self, applet_id: uuid.UUID, respondent_subject_id: uuid.UUID) -> None:
        assignments = await ActivityAssigmentCRUD(self.session).get_by_respondent_subject_id(respondent_subject_id)
        if not assignments:
            return

        activity_ids = []
        flow_ids = []
        for assignment in assignments:
            if assignment.activity_id:
                activity_ids.append(assignment.activity_id)
            if assignment.activity_flow_id:
                flow_ids.append(assignment.activity_flow_id)

        activities = {
            activity.id: activity
            for activity in await ActivitiesCRUD(self.session).get_by_applet_id_and_activities_ids(
                applet_id, activity_ids
            )
        }
        flows = {
            flow.id: flow for flow in await FlowsCRUD(self.session).get_by_applet_id_and_flows_ids(applet_id, flow_ids)
        }

        respondent_subject = await SubjectsCrud(self.session).get_by_id(respondent_subject_id)
        assert respondent_subject

        respondent_activities: dict[uuid.UUID, set[str]] = defaultdict(set)
        for assignment in assignments:
            activity_or_flow = activities.get(assignment.activity_id) or flows.get(assignment.activity_flow_id)
            if activity_or_flow:
                respondent_activities[respondent_subject_id].add(activity_or_flow.name)

        if len(respondent_activities[respondent_subject_id]) > 0:
            await self.send_email_notification(
                applet_id, {respondent_subject_id: respondent_subject}, respondent_activities
            )

    async def send_email_notification(
        self,
        applet_id: uuid.UUID,
        subjects: dict[uuid.UUID, SubjectSchema],
        respondent_activities: dict[uuid.UUID, set[str]],
    ) -> None:
        service = MailingService()
        applet = await AppletsCRUD(self.session).get_by_id(applet_id)
        for respondent_subject_id, activities in respondent_activities.items():
            respondent_subject: SubjectSchema = subjects[respondent_subject_id]

            language = respondent_subject.language or "en"
            template_name = self._get_email_template_name(language)

            domain = settings.service.urls.frontend.web_base
            path = settings.service.urls.frontend.applet_home
            link = (
                f"https://{domain}/{path}/{applet.id}"
                if not domain.startswith("http")
                else f"{domain}/{path}/{applet.id}"
            )

            message = MessageSchema(
                recipients=[respondent_subject.email],
                subject=self._get_email_assignment_subject(language),
                body=service.get_template(
                    path=template_name,
                    first_name=respondent_subject.first_name,
                    applet_name=applet.display_name,
                    link=link,
                    language=language,
                    activity_or_flows_names=activities,
                ),
            )
            _ = asyncio.create_task(service.send(message))

    async def _check_for_already_existing_assignment(self, schema: ActivityAssigmentSchema) -> bool:
        return await ActivityAssigmentCRUD(self.session).already_exists(schema)

    @staticmethod
    def _validate_assignment_and_get_activity_or_flow_name(
        assignment: ActivityAssignmentCreate, entities: _AssignmentEntities
    ) -> str:
        name: str = ""
        activity_flow_message = ""
        if assignment.activity_id:
            if (activity := entities.activities.get(assignment.activity_id)) is None:
                raise ValidationError(f"Invalid activity id {assignment.activity_id}")

            activity_flow_message = f"for assignment to activity {activity.name}"
            name = activity.name

        if assignment.activity_flow_id:
            if (flow := entities.flows.get(assignment.activity_flow_id)) is None:
                raise ValidationError(f"Invalid flow id {assignment.activity_flow_id}")

            activity_flow_message = f"for assignment to activity flow {flow.name}"
            name = flow.name

        if entities.respondent_subjects.get(assignment.respondent_subject_id) is None:
            raise ValidationError(
                f"Invalid respondent subject id {assignment.respondent_subject_id} {activity_flow_message}"
            )

        if entities.target_subjects.get(assignment.target_subject_id) is None:
            raise ValidationError(f"Invalid target subject id {assignment.target_subject_id} {activity_flow_message}")

        return name

    async def _get_assignments_entities(
        self, applet_id: uuid.UUID, assignments_create: list[ActivityAssignmentCreate]
    ) -> _AssignmentEntities:
        activity_ids = []
        flow_ids = []
        target_subject_ids = []
        respondent_subject_ids = []
        for assignment in assignments_create:
            if assignment.activity_id:
                activity_ids.append(assignment.activity_id)
            if assignment.activity_flow_id:
                flow_ids.append(assignment.activity_flow_id)
            respondent_subject_ids.append(assignment.respondent_subject_id)
            target_subject_ids.append(assignment.target_subject_id)

        entities = self._AssignmentEntities()
        entities.activities = {
            activity.id: activity
            for activity in await ActivitiesCRUD(self.session).get_by_applet_id_and_activities_ids(
                applet_id, activity_ids
            )
        }
        entities.flows = {
            flow.id: flow for flow in await FlowsCRUD(self.session).get_by_applet_id_and_flows_ids(applet_id, flow_ids)
        }

        entities.respondent_subjects = {
            subject.id: subject
            for subject in await SubjectsCrud(self.session).get_by_ids(respondent_subject_ids)
            if subject.applet_id == applet_id and subject.email is not None
        }

        entities.target_subjects = {
            subject.id: subject
            for subject in await SubjectsCrud(self.session).get_by_ids(target_subject_ids)
            if subject.applet_id == applet_id
        }

        return entities

    async def get_all(self, applet_id: uuid.UUID, query_params: QueryParams) -> list[ActivityAssignment]:
        assignments = await ActivityAssigmentCRUD(self.session).get_by_applet(applet_id, query_params)

        return [
            ActivityAssignment(
                id=assignment.id,
                activity_id=assignment.activity_id,
                activity_flow_id=assignment.activity_flow_id,
                respondent_subject_id=assignment.respondent_subject_id,
                target_subject_id=assignment.target_subject_id,
            )
            for assignment in assignments
        ]

    async def get_all_by_respondent(
        self, applet_id: uuid.UUID, respondent_subject_id: uuid.UUID
    ) -> list[ActivityAssignmentWithSubject]:
        respondent_subject = await SubjectsCrud(self.session).get_by_id(respondent_subject_id)
        if not respondent_subject:
            raise NotFoundError(f"Respondent subject id {respondent_subject_id} not found")

        assignments = await ActivityAssigmentCRUD(self.session).get_by_applet_and_respondent(
            applet_id, respondent_subject_id
        )

        target_subject_ids = [assignment.target_subject_id for assignment in assignments]

        target_subjects = {
            subject.id: SubjectReadResponse(
                id=subject.id,
                first_name=subject.first_name,
                last_name=subject.last_name,
                email=subject.email,
                language=subject.language,
                nickname=subject.nickname,
                secret_user_id=subject.secret_user_id,
                tag=subject.tag,
                applet_id=subject.applet_id,
            )
            for subject in await SubjectsCrud(self.session).get_by_ids(target_subject_ids)
        }

        return [
            ActivityAssignmentWithSubject(
                activity_id=assignment.activity_id,
                activity_flow_id=assignment.activity_flow_id,
                respondent_subject=SubjectReadResponse(
                    id=respondent_subject.id,
                    first_name=respondent_subject.first_name,
                    last_name=respondent_subject.last_name,
                    email=respondent_subject.email,
                    language=respondent_subject.language,
                    nickname=respondent_subject.nickname,
                    secret_user_id=respondent_subject.secret_user_id,
                    tag=respondent_subject.tag,
                    applet_id=respondent_subject.applet_id,
                ),
                target_subject=target_subjects[assignment.target_subject_id],
            )
            for assignment in assignments
        ]

    @staticmethod
    def _get_email_template_name(language: str) -> str:
        return f"new_activity_assignments_{language}"

    @staticmethod
    def _get_email_assignment_subject(language: str) -> str:
        translations = {
            "en": "Assignment Notification",
            "fr": "Notification d'attribution",
        }
        return translations.get(language, translations["en"])