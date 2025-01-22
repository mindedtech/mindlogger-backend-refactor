import uuid

from fastapi import Depends
from apps.authentication.deps import get_current_user
from apps.integrations.prolific.domain import PublicProlificIntegration
from apps.integrations.prolific.service.prolific import ProlificIntegrationService
from apps.users.domain import User
from infrastructure.database.deps import get_session
from infrastructure.http.deps import get_language


async def get_public_prolific_integration(
    applet_id: uuid.UUID,
    language: str = Depends(get_language),
    session=Depends(get_session),
) -> PublicProlificIntegration:
    return await ProlificIntegrationService(session=session, applet_id=applet_id).get_public_prolific_integration(language)

async def get_study_completion_codes(
        study_id: str,
        applet_id: uuid.UUID,
        session=Depends(get_session)) -> list[str]:
    return await ProlificIntegrationService(session=session, applet_id=applet_id).get_completion_codes(study_id)
