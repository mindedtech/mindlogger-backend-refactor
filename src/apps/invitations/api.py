import uuid
from copy import deepcopy

from fastapi import Body, Depends
from fastapi.exceptions import RequestValidationError
from pydantic.error_wrappers import ErrorWrapper

from apps.applets.service import AppletService
from apps.authentication.deps import get_current_user
from apps.invitations.domain import (
    InvitationDetailForReviewer,
    InvitationManagersRequest,
    InvitationManagersResponse,
    InvitationRespondentRequest,
    InvitationRespondentResponse,
    InvitationResponse,
    InvitationReviewerRequest,
    InvitationReviewerResponse,
    PrivateInvitationResponse,
    ShallAccountInvitation,
)
from apps.invitations.errors import ManagerInvitationExist, NonUniqueValue, RespondentInvitationExist
from apps.invitations.filters import InvitationQueryParams
from apps.invitations.services import InvitationsService, PrivateInvitationService
from apps.shared.domain import Response, ResponseMulti
from apps.shared.exception import NotFoundError, ValidationError
from apps.shared.query_params import QueryParams, parse_query_params
from apps.subjects.domain import SubjectCreate
from apps.subjects.errors import SecretIDUniqueViolationError
from apps.subjects.services import SubjectsService
from apps.users import UserNotFound
from apps.users.domain import User
from apps.users.services.user import UserService
from apps.workspaces.domain.constants import Role
from apps.workspaces.service.check_access import CheckAccessService
from apps.workspaces.service.user_applet_access import UserAppletAccessService
from infrastructure.database import atomic
from infrastructure.database.deps import get_session


async def invitation_list(
    user: User = Depends(get_current_user),
    query_params: QueryParams = Depends(parse_query_params(InvitationQueryParams)),
    session=Depends(get_session),
) -> ResponseMulti[InvitationResponse]:
    """Fetch all invitations whose status is pending
    for the specific user who is invitor.
    """
    if query_params.filters.get("applet_id"):
        await CheckAccessService(session, user.id).check_applet_invite_access(query_params.filters["applet_id"])
    service = InvitationsService(session, user)
    invitations = await service.fetch_all(deepcopy(query_params))
    count = await service.fetch_all_count(deepcopy(query_params))

    return ResponseMulti[InvitationResponse](
        result=[InvitationResponse(**invitation.dict()) for invitation in invitations],
        count=count,
    )


async def invitation_retrieve(
    key: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
) -> Response[InvitationResponse]:
    """Get specific invitation with approve key for user
    who was invited.
    """
    invitation = await InvitationsService(session, user).get(key)
    return Response(result=InvitationResponse.from_orm(invitation))


async def private_invitation_retrieve(
    key: uuid.UUID,
    session=Depends(get_session),
) -> Response[PrivateInvitationResponse]:
    invitation = await PrivateInvitationService(session).get_invitation(key)
    return Response(result=PrivateInvitationResponse.from_orm(invitation))


async def invitation_respondent_send(
    applet_id: uuid.UUID,
    user: User = Depends(get_current_user),
    invitation_schema: InvitationRespondentRequest = Body(...),
    session=Depends(get_session),
) -> Response[InvitationRespondentResponse]:
    """
    General endpoint for sending invitations to the concrete applet
    for the concrete user giving him a role "respondent".
    """

    async with atomic(session):
        await AppletService(session, user.id).exist_by_id(applet_id)
        await CheckAccessService(session, user.id).check_applet_invite_access(applet_id)
        invitation_service = InvitationsService(session, user)
        try:
            invited_user = await UserService(session).get_by_email(invitation_schema.email)
            is_role_exist = await UserAppletAccessService(session, invited_user.id, applet_id).has_role(Role.RESPONDENT)
            if is_role_exist:
                raise RespondentInvitationExist()
        except UserNotFound:
            pass

        subject_service = SubjectsService(session, user.id)
        try:
            subject = await subject_service.create(
                SubjectCreate(creator_id=user.id, applet_id=applet_id, **invitation_schema.dict(by_alias=False))
            )
        except SecretIDUniqueViolationError:
            wrapper = ErrorWrapper(
                ValueError(NonUniqueValue()), ("body", InvitationRespondentRequest.field_alias("secret_user_id"))
            )
            raise RequestValidationError([wrapper])
        invitation = await invitation_service.send_respondent_invitation(applet_id, invitation_schema, subject.id)

    return Response[InvitationRespondentResponse](result=InvitationRespondentResponse(**invitation.dict()))


async def invitation_reviewer_send(
    applet_id: uuid.UUID,
    user: User = Depends(get_current_user),
    invitation_schema: InvitationReviewerRequest = Body(...),
    session=Depends(get_session),
) -> Response[InvitationReviewerResponse]:
    """
    General endpoint for sending invitations to the concrete applet
    for the concrete user giving him role "reviewer" for specific respondents.
    """

    async with atomic(session):
        await AppletService(session, user.id).exist_by_id(applet_id)
        await CheckAccessService(session, user.id).check_applet_invite_access(applet_id)
        invitation_srv = InvitationsService(session, user)
        try:
            invited_user = await UserService(session).get_by_email(invitation_schema.email)
            is_role_exist = await UserAppletAccessService(session, invited_user.id, applet_id).has_role(Role.REVIEWER)
            if is_role_exist:
                raise ManagerInvitationExist()
        except UserNotFound:
            pass

        invitation: InvitationDetailForReviewer = await invitation_srv.send_reviewer_invitation(
            applet_id, invitation_schema
        )

    return Response[InvitationReviewerResponse](result=InvitationReviewerResponse(**invitation.dict()))


async def invitation_managers_send(
    applet_id: uuid.UUID,
    user: User = Depends(get_current_user),
    invitation_schema: InvitationManagersRequest = Body(...),
    session=Depends(get_session),
) -> Response[InvitationManagersResponse]:
    """
    General endpoint for sending invitations to the concrete applet
    for the concrete user giving him a one of roles:
    "manager", "coordinator", "editor".
    """

    async with atomic(session):
        await AppletService(session, user.id).exist_by_id(applet_id)
        await CheckAccessService(session, user.id).check_applet_invite_access(applet_id)
        invitation_srv = InvitationsService(session, user)
        try:
            invited_user = await UserService(session).get_by_email(invitation_schema.email)
            is_role_exist = await UserAppletAccessService(session, invited_user.id, applet_id).has_role(
                invitation_schema.role
            )
            if is_role_exist:
                raise ManagerInvitationExist()
        except UserNotFound:
            pass

        invitation = await invitation_srv.send_managers_invitation(applet_id, invitation_schema)

    return Response[InvitationManagersResponse](result=InvitationManagersResponse(**invitation.dict()))


async def invitation_accept(
    key: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """General endpoint to approve the applet invitation."""
    async with atomic(session):
        await InvitationsService(session, user).accept(key)


async def private_invitation_accept(
    key: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    async with atomic(session):
        await PrivateInvitationService(session).accept_invitation(user, key)


async def invitation_decline(
    key: uuid.UUID,
    user: User = Depends(get_current_user),
    session=Depends(get_session),
):
    """General endpoint to decline the applet invitation."""
    async with atomic(session):
        await InvitationsService(session, user).decline(key)


async def invitation_subject_send(
    applet_id: uuid.UUID,
    user: User = Depends(get_current_user),
    schema: ShallAccountInvitation = Body(...),
    session=Depends(get_session),
) -> Response[InvitationRespondentResponse]:
    async with atomic(session):
        await AppletService(session, user.id).exist_by_id(applet_id)
        await CheckAccessService(session, user.id).check_applet_invite_access(applet_id)

        subject_service = SubjectsService(session, user.id)
        subject = await subject_service.get_if_soft_exist(schema.subject_id)
        if not subject:
            raise NotFoundError()
        if subject.user_id:
            raise ValidationError("Subject already assigned.")

        # check role exists
        invitation_service = InvitationsService(session, user)
        try:
            invited_user = await UserService(session).get_by_email(schema.email)
            is_role_exist = await UserAppletAccessService(session, invited_user.id, applet_id).has_role(Role.RESPONDENT)
            if is_role_exist:
                raise RespondentInvitationExist()
        except UserNotFound:
            pass

        invitation_schema = InvitationRespondentRequest(
            email=schema.email,
            first_name=subject.first_name,
            last_name=subject.last_name,
            language=subject.language,
            secret_user_id=subject.secret_user_id,
            nickname=subject.nickname,
        )
        invitation = await invitation_service.send_respondent_invitation(applet_id, invitation_schema, subject.id)
        if subject.email != schema.email:
            await subject_service.update(subject.id, email=schema.email)

    return Response[InvitationRespondentResponse](result=InvitationRespondentResponse(**invitation.dict()))
