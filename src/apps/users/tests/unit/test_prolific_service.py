import base64
import random
import secrets
import string
from apps.users.domain import ProlificToken, User
from sqlalchemy.ext.asyncio import AsyncSession

from apps.users.services.prolific import ProlificService

def generate_string_token(length=120):
    char_pool = string.ascii_letters + string.digits + "-_"
    token = ''.join(random.choices(char_pool, k=length))
    
    return token

async def test_prolific_token(session: AsyncSession, user: User):
    service = ProlificService(session)
    
    prolific_token = await service.get_prolific_token(user.id)
    assert prolific_token is None
    
    random_token = generate_string_token()
    await service.save_prolific_token(user.id, ProlificToken(api_token=random_token), test=True)

    prolific_token = await service.get_prolific_token(user.id)
    assert prolific_token.api_token == random_token
