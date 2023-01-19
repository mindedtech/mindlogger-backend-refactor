from fastapi import Body, Depends

from apps.activities.crud import ReusableItemChoiceCRUD
from apps.activities.domain.reusable_item_choices import (
    PublicReusableItemChoice,
    ReusableItemChoice,
    ReusableItemChoiceCreate,
    ReusableItemChoiceInitializeCreate,
)
from apps.authentication.deps import get_current_user
from apps.shared.domain.response import Response, ResponseMulti
from apps.shared.errors import NoContentError
from apps.users.domain import User


async def item_choice_create(
    user: User = Depends(get_current_user),
    schema: ReusableItemChoiceInitializeCreate = Body(...),
) -> Response[PublicReusableItemChoice]:

    item_template: ReusableItemChoice = await ReusableItemChoiceCRUD().save(
        schema=ReusableItemChoiceCreate(**schema.dict(), user_id=user.id)
    )

    return Response(result=PublicReusableItemChoice(**item_template.dict()))


async def item_choice_delete(id_: int, user: User = Depends(get_current_user)):
    await ReusableItemChoiceCRUD().delete_by_id(id_=id_)
    raise NoContentError


async def item_choice_retrieve(
    user: User = Depends(get_current_user),
) -> ResponseMulti[PublicReusableItemChoice]:
    item_templates: list[
        PublicReusableItemChoice
    ] = await ReusableItemChoiceCRUD().get_item_templates(user.id)

    return ResponseMulti(results=item_templates)