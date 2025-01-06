from fastapi.routing import APIRouter

from starlette import status

from apps.integrations.prolific.api import prolific_integration_exists
from apps.integrations.prolific.domain import PublicProlificIntegration
from apps.shared.domain import Response
from apps.shared.domain.response.errors import AUTHENTICATION_ERROR_RESPONSES, DEFAULT_OPENAPI_RESPONSE


router = APIRouter(prefix="/integrations/prolific", tags=["Prolific"])

router.get(
    "",
    description="This endpoint is used to check if a prolific integration exists",
    response_model=None,
    status_code=status.HTTP_200_OK,
    responses= {
        status.HTTP_200_OK: {"model": Response[PublicProlificIntegration]},
        **DEFAULT_OPENAPI_RESPONSE,
        **AUTHENTICATION_ERROR_RESPONSES
    },
)(prolific_integration_exists)