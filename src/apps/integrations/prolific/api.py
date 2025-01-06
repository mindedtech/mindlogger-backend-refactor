import uuid

from fastapi import Depends
from apps.authentication.deps import get_current_user
from apps.integrations.prolific.domain import PublicProlificIntegration
from apps.integrations.prolific.service.prolific import ProlificIntegrationService
from apps.users.domain import User
from infrastructure.database.deps import get_session


async def prolific_integration_exists(
        applet_id: uuid.UUID,
        user: User = Depends(get_current_user),
        session=Depends(get_session)) -> PublicProlificIntegration:
    exists = await ProlificIntegrationService(session=session, user=user, applet_id=applet_id).prolific_integration_exists()
    return PublicProlificIntegration(exists=exists)