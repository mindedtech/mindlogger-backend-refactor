import uuid
from copy import deepcopy
from datetime import date, timedelta

from fastapi import Body, Depends
from firebase_admin.exceptions import FirebaseError

from apps.answers.errors import UserDoesNotHavePermissionError
from apps.applets.crud import AppletsCRUD, UserAppletAccessCRUD
from apps.applets.db.schemas import AppletSchema
from apps.applets.service import AppletService
from apps.authentication.deps import get_current_user
from apps.schedule.domain.schedule.filters import EventQueryParams
from apps.schedule.domain.schedule.public import (
    PublicEvent,
    PublicEventByUser,
    PublicEventCount,
)
from apps.schedule.domain.schedule.requests import (
    EventRequest,
    EventUpdateRequest,
)
from apps.schedule.service.schedule import ScheduleService
from apps.shared.domain import Response, ResponseMulti
from apps.shared.link import convert_link_key
from apps.shared.query_params import QueryParams, parse_query_params
from apps.users.domain import User
from apps.workspaces.domain.constants import Role
from apps.workspaces.service.check_access import CheckAccessService
from infrastructure.database import atomic
from infrastructure.database.deps import get_session
from infrastructure.logger import logger
from infrastructure.utility import FirebaseNotificationType


# TODO: Add logic to allow to create events by permissions
# TODO: Restrict by admin
async def schedule_create(
    applet_id: uuid.UUID,
    schema: EventRequest = Body(...),
    user: User = Depends(get_current_user),
    session=Depends(get_session),
) -> Response[PublicEvent]:
    """Create a new event for an applet."""
    applet_service = AppletService(session, user.id)
    async with atomic(session):
        await applet_service.exist_by_id(applet_id)
        await CheckAccessService(
            session, user.id
        ).check_applet_schedule_create_access(applet_id)
        service = ScheduleService(session)
        schedule = await service.create_schedule(schema, applet_id)

    try:
        await applet_service.send_notification_to_applet_respondents(
            applet_id,
            "Your schedule has been changed, click to update.",
            "Your schedule has been changed, click to update.",
            FirebaseNotificationType.SCHEDULE_UPDATED,
            respondent_ids=[schedule.respondent_id]
            if schedule.respondent_id
            else None,
        )
    except FirebaseError as e:
        # mute error
        logger.exception(e)

    return Response(result=PublicEvent(**schedule.dict()))


async def schedule_get_by_id(
    applet_id: uuid.UUID,
    schedule_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
) -> Response[PublicEvent]:
    """Get a schedule by id."""
    async with atomic(session):
        await AppletService(session, user.id).exist_by_id(applet_id)
        schedule = await ScheduleService(session).get_schedule_by_id(
            applet_id=applet_id, schedule_id=schedule_id
        )
    return Response(result=PublicEvent(**schedule.dict()))


async def schedule_get_all(
    applet_id: uuid.UUID,
    user: User = Depends(get_current_user),
    query_params: QueryParams = Depends(parse_query_params(EventQueryParams)),
    session=Depends(get_session),
) -> ResponseMulti[PublicEvent]:
    """Get schedules for an applet. If respondentId is provided,it
    will return only individual events for that respondent. If respondentId
    is not provided, it will return only general events for the applet."""
    async with atomic(session):
        await AppletService(session, user.id).exist_by_id(applet_id)
        schedules = await ScheduleService(session).get_all_schedules(
            applet_id, deepcopy(query_params)
        )

    roles: set = set(
        await UserAppletAccessCRUD(session).get_user_roles_to_applet(
            user.id, applet_id
        )
    )
    accessed_roles: set = {
        Role.SUPER_ADMIN.value,
        Role.OWNER.value,
        Role.MANAGER.value,
        Role.COORDINATOR.value,
    }
    if not roles & accessed_roles:
        raise UserDoesNotHavePermissionError()

    return ResponseMulti(result=schedules, count=len(schedules))


async def public_schedule_get_all(
    key: str,
    session=Depends(get_session),
) -> Response[PublicEventByUser]:
    """Get all schedules for an applet."""
    key_guid = convert_link_key(key)
    async with atomic(session):
        schedules = await ScheduleService(session).get_public_all_schedules(
            key_guid
        )

    return Response(result=schedules)


async def schedule_delete_all(
    applet_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """Delete all default schedules for an applet."""
    applet_service = AppletService(session, user.id)
    async with atomic(session):
        await applet_service.exist_by_id(applet_id)
        await CheckAccessService(
            session, user.id
        ).check_applet_schedule_create_access(applet_id)
        service = ScheduleService(session)
        await service.delete_all_schedules(applet_id)

    try:
        await applet_service.send_notification_to_applet_respondents(
            applet_id,
            "Your schedule has been changed, click to update.",
            "Your schedule has been changed, click to update.",
            FirebaseNotificationType.SCHEDULE_UPDATED,
        )
    except FirebaseError as e:
        # mute error
        logger.exception(e)


async def schedule_delete_by_id(
    applet_id: uuid.UUID,
    schedule_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """Delete a schedule by id."""
    applet_service = AppletService(session, user.id)
    async with atomic(session):
        await applet_service.exist_by_id(applet_id)
        await CheckAccessService(
            session, user.id
        ).check_applet_schedule_create_access(applet_id)
        service = ScheduleService(session)
        respondent_id = await service.delete_schedule_by_id(
            schedule_id, applet_id
        )

    try:
        await applet_service.send_notification_to_applet_respondents(
            applet_id,
            "Your schedule has been changed, click to update.",
            "Your schedule has been changed, click to update.",
            FirebaseNotificationType.SCHEDULE_UPDATED,
            respondent_ids=[respondent_id] if respondent_id else None,
        )
    except FirebaseError as e:
        # mute error
        logger.exception(e)


async def schedule_update(
    applet_id: uuid.UUID,
    schedule_id: uuid.UUID,
    user: User = Depends(get_current_user),
    schema: EventUpdateRequest = Body(...),
    session=Depends(get_session),
) -> Response[PublicEvent]:
    """Update a schedule by id."""
    applet_service = AppletService(session, user.id)
    async with atomic(session):
        await applet_service.exist_by_id(applet_id)
        await CheckAccessService(
            session, user.id
        ).check_applet_schedule_create_access(applet_id)
        service = ScheduleService(session)
        schedule = await service.update_schedule(
            applet_id, schedule_id, schema
        )

    try:
        await applet_service.send_notification_to_applet_respondents(
            applet_id,
            "Your schedule has been changed, click to update.",
            "Your schedule has been changed, click to update.",
            FirebaseNotificationType.SCHEDULE_UPDATED,
            respondent_ids=[schedule.respondent_id]
            if schedule.respondent_id
            else None,
        )
    except FirebaseError as e:
        # mute error
        logger.exception(e)

    return Response(result=PublicEvent(**schedule.dict()))


async def schedule_count(
    applet_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
) -> Response[PublicEventCount]:
    """Get the count of schedules for an applet."""
    async with atomic(session):
        await AppletService(session, user.id).exist_by_id(applet_id)
        count: PublicEventCount = await ScheduleService(
            session
        ).count_schedules(applet_id)
    return Response(result=count)


async def schedule_delete_by_user(
    applet_id: uuid.UUID,
    respondent_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """Delete all schedules for a respondent and create default ones."""
    applet_service = AppletService(session, user.id)
    async with atomic(session):
        await applet_service.exist_by_id(applet_id)
        await CheckAccessService(
            session, user.id
        ).check_applet_schedule_create_access(applet_id)
        service = ScheduleService(session)
        await service.delete_by_user_id(
            applet_id=applet_id, user_id=respondent_id
        )

    try:
        await applet_service.send_notification_to_applet_respondents(
            applet_id,
            "Your schedule has been changed, click to update.",
            "Your schedule has been changed, click to update.",
            FirebaseNotificationType.SCHEDULE_UPDATED,
            respondent_ids=[respondent_id],
        )
    except FirebaseError as e:
        # mute error
        logger.exception(e)


async def schedule_get_all_by_user(
    user: User = Depends(get_current_user),
    session=Depends(get_session),
) -> ResponseMulti[PublicEventByUser]:
    """Get all schedules for a user."""
    async with atomic(session):
        schedules = await ScheduleService(session).get_events_by_user(
            user_id=user.id
        )
        count = await ScheduleService(session).count_events_by_user(
            user_id=user.id
        )
    return ResponseMulti(result=schedules, count=count)


async def schedule_get_all_by_respondent_user(
    user: User = Depends(get_current_user),
    session=Depends(get_session),
) -> ResponseMulti[PublicEventByUser]:
    """Get all the respondent's schedules for the next 2 weeks."""
    max_date_from_event_delta_days = 15
    min_date_to_event_delta_days = 2
    today: date = date.today()
    max_start_date: date = today + timedelta(
        days=max_date_from_event_delta_days
    )
    min_end_date: date = today - timedelta(days=min_date_to_event_delta_days)

    async with atomic(session):
        # applets for this endpoint must be equal to
        # applets from /applets?roles=respondent endpoint
        query_params: QueryParams = QueryParams(
            filters={"roles": Role.RESPONDENT, "flat_list": False},
            limit=10000,
        )
        applets: list[AppletSchema] = await AppletsCRUD(
            session
        ).get_applets_by_roles(
            user_id=user.id,
            roles=[Role.RESPONDENT],
            query_params=query_params,
            exclude_without_encryption=True,
        )
        applet_ids: list[uuid.UUID] = [applet.id for applet in applets]

        schedules = await ScheduleService(session).get_upcoming_events_by_user(
            user_id=user.id,
            applet_ids=applet_ids,
            min_end_date=min_end_date,
            max_start_date=max_start_date,
        )
    return ResponseMulti(result=schedules, count=len(schedules))


async def schedule_get_by_user(
    applet_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
) -> Response[PublicEventByUser]:
    """Get all schedules for a respondent per applet id."""
    async with atomic(session):
        await AppletService(session, user.id).exist_by_id(applet_id)
        schedules = await ScheduleService(
            session
        ).get_events_by_user_and_applet(user_id=user.id, applet_id=applet_id)
    return Response(result=schedules)


async def schedule_remove_individual_calendar(
    applet_id: uuid.UUID,
    respondent_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """Remove individual calendar for a respondent."""
    applet_service = AppletService(session, user.id)
    async with atomic(session):
        await applet_service.exist_by_id(applet_id)
        await CheckAccessService(
            session, user.id
        ).check_applet_schedule_create_access(applet_id)
        service = ScheduleService(session)
        await service.remove_individual_calendar(
            applet_id=applet_id, user_id=respondent_id
        )
    try:
        await applet_service.send_notification_to_applet_respondents(
            applet_id,
            "Your schedule has been changed, click to update.",
            "Your schedule has been changed, click to update.",
            FirebaseNotificationType.SCHEDULE_UPDATED,
            respondent_ids=[respondent_id],
        )
    except FirebaseError as e:
        # mute error
        logger.exception(e)


# TODO: Add logic to allow to create events by permissions
# TODO: Restrict by admin
async def schedule_import(
    applet_id: uuid.UUID,
    schemas: list[EventRequest] = Body(...),
    user: User = Depends(get_current_user),
    session=Depends(get_session),
) -> ResponseMulti[PublicEvent]:
    """Create a new event for an applet."""
    async with atomic(session):
        await AppletService(session, user.id).exist_by_id(applet_id)
        schedules = await ScheduleService(session).import_schedule(
            schemas, applet_id
        )
    return ResponseMulti(
        result=schedules,
        count=len(schedules),
    )


# TODO: Add logic to allow to create events by permissions
# TODO: Restrict by admin
async def schedule_create_individual(
    applet_id: uuid.UUID,
    respondent_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
) -> ResponseMulti[PublicEvent]:
    """Create a new event for an applet."""
    applet_service = AppletService(session, user.id)
    async with atomic(session):
        await applet_service.exist_by_id(applet_id)
        await CheckAccessService(
            session, user.id
        ).check_applet_schedule_create_access(applet_id)
        service = ScheduleService(session)
        schedules = await service.create_schedule_individual(
            applet_id, respondent_id
        )

    try:
        await applet_service.send_notification_to_applet_respondents(
            applet_id,
            "Your schedule has been changed, click to update.",
            "Your schedule has been changed, click to update.",
            FirebaseNotificationType.SCHEDULE_UPDATED,
            respondent_ids=[respondent_id],
        )
    except FirebaseError as e:
        # mute error
        logger.exception(e)

    return ResponseMulti(result=schedules, count=len(schedules))
