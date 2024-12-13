import uuid

from fastapi import HTTPException
from apps.users.cruds.user import UsersCRUD
from apps.users.domain import ProlificToken

import requests


class ProlificService:
    def __init__(self, session) -> None:
        self.session = session

    async def get_prolific_token(self, user_id: uuid.UUID) -> ProlificToken | None:
        prolific_token = await UsersCRUD(self.session).get_user_prolific_token(user_id)
        return ProlificToken(api_token=prolific_token) if prolific_token else None

    async def save_prolific_token(self, user_id: uuid.UUID, prolific_token: ProlificToken, test: bool = False) -> None:
        if not test:
            prolific_response = requests.get(
                "https://api.prolific.com/api/v1/users/me/",
                headers={
                    "Authorization": f"Token {prolific_token.api_token}",
                    "Content-Type": "application/json"
                    })

            print(prolific_response.reason)
            if prolific_response.status_code != 200:
                raise HTTPException(status_code=prolific_response.status_code, detail="Prolific token is invalid")

        token = prolific_token.api_token
        await UsersCRUD(self.session).save_user_prolific_token(user_id, token)