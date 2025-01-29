
from unittest.mock import AsyncMock, patch
import uuid

from apps.shared.test.base import BaseTest
from apps.shared.test.client import TestClient
from apps.users.domain import User

from apps.integrations.prolific.router import router as prolific_router

class TestProlificService(BaseTest):

    @patch('apps.integrations.prolific.service.prolific.requests.get')
    async def test_get_completion_codes(self, mock_get, client: TestClient, user: User, uuid_zero: uuid.UUID):
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "completion_codes": [
                {
                    "code": "code1",
                    "code_type": "type1",
                    "actions": ["action1"],
                    "actor": "actor1"
                },
                {
                    "code": "code2",
                    "code_type": "type2",
                    "actions": ["action2"],
                    "actor": "actor2"
                }
            ]
        }
        mock_get.return_value = mock_response

        study_id = "study123"
        client.login(user)

        completion_codes_url = f"/integrations/prolific/applet/{uuid_zero}/completion_codes/{study_id}"
        result = await client.get(completion_codes_url)

        assert len(result.completion_codes) == 2
        assert result.completion_codes[0].code == "code1"
        assert result.completion_codes[1].code_type == "type2"

    @patch('apps.integrations.prolific.service.prolific.requests.get')
    async def test_get_completion_codes_failure(self, mock_get, client: TestClient, user: User, uuid_zero: uuid.UUID):
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}
        mock_get.return_value = mock_response

        study_id = "study123"
        client.login(user)
        completion_codes_url = f"/integrations/prolific/applet/{uuid_zero}/completion_codes/{study_id}"
        result = await client.get(completion_codes_url)
        
        assert result.status_code == 404