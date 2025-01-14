import ast
from http.client import HTTPException
import uuid

import requests

from apps.integrations.crud.integrations import IntegrationsCRUD
from apps.integrations.db.schemas import IntegrationsSchema
from apps.integrations.domain import AvailableIntegrations
from apps.integrations.prolific.errors import ProlificInvalidApiTokenError
from apps.integrations.prolific.domain import ProlificCompletionCode, ProlificCompletionCodeList, ProlificIntegration
from apps.users.domain import User


class ProlificIntegrationService:
    def __init__(self, applet_id: uuid.UUID, session, user: User = None) -> None:
        self.applet_id = applet_id
        self.session = session
        self.user = user
        self.type = AvailableIntegrations.PROLIFIC

    async def create_prolific_integration(self, api_key: str) -> ProlificIntegration:
        prolific_response = requests.get(
            "https://api.prolific.com/api/v1/users/me/",
            headers={"Authorization": f"Token {api_key}", "Content-Type": "application/json"},
        )

        if prolific_response.status_code != 200:
            raise ProlificInvalidApiTokenError()

        integration_schema = await IntegrationsCRUD(self.session).create(
            IntegrationsSchema(
                applet_id=self.applet_id,
                type=self.type,
                configuration={
                    "api_key": api_key,
                },
            )
        )

        return ProlificIntegration.from_schema(integration_schema)
    
    async def get_completion_codes(self, study_id: str) -> ProlificCompletionCodeList:
        integration = await IntegrationsCRUD(self.session).retrieve_by_applet_and_type(
            applet_id=self.applet_id,
            integration_type=self.type
        )

        api_key = ast.literal_eval(integration.configuration)["api_key"]

        prolific_response = requests.get(
            f"https://api.prolific.com/api/v1/studies/{study_id}/",
            headers={
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json"
                })
        
        if (prolific_response.status_code != 200):
            raise HTTPException(status_code=prolific_response.status_code, detail=prolific_response.detail)

        prolific_completion_codes = prolific_response.json()["completion_codes"]
        print(prolific_completion_codes)
        completion_codes = []
        for code in prolific_completion_codes:
            completion_codes.append(ProlificCompletionCode(code=code["code"], code_type=code["code_type"], actions=code["actions"], actor=code["actor"]))

        print(completion_codes)
        tmp =  ProlificCompletionCodeList(completion_codes=prolific_response.json()["completion_codes"])
        print(tmp)
        return tmp
