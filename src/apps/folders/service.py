from apps.applets.crud import AppletsCRUD
from apps.folders.crud import FolderCRUD
from apps.folders.db.schemas import FolderSchema
from apps.folders.domain import Folder, FolderCreate, FolderUpdate
from apps.folders.errors import (
    FolderAccessDenied,
    FolderAlreadyExist,
    FolderIsNotEmpty,
)


class FolderService:
    def __init__(self, user_id: int):
        self._creator_id = user_id

    async def list(self) -> list[Folder]:
        schemas = await FolderCRUD().get_creators_folders(self._creator_id)
        return [Folder.from_orm(schema) for schema in schemas]

    async def create(self, data: FolderCreate) -> Folder:
        await self._validate_create(data.name)
        schema = await FolderCRUD().save(
            FolderSchema(name=data.name, creator_id=self._creator_id)
        )
        return Folder.from_orm(schema)

    async def _validate_create(self, name: str):
        existed_folder = await FolderCRUD().get_creators_folder_by_name(
            self._creator_id, name
        )
        if existed_folder:
            raise FolderAlreadyExist()

    async def update(self, id_: int, data: FolderUpdate) -> Folder:
        await self._validate_update(id_, data.name)
        schema = await FolderCRUD().update_by_id(
            FolderSchema(id=id_, name=data.name, creator_id=self._creator_id)
        )
        return Folder.from_orm(schema)

    async def _validate_update(self, folder_id, new_name: str):
        existed_folder = await FolderCRUD().get_by_id(folder_id)

        if existed_folder.creator_id != self._creator_id:
            raise FolderAccessDenied()

        folder_by_new_name = await FolderCRUD().get_creators_folder_by_name(
            self._creator_id, new_name
        )
        if folder_by_new_name and folder_by_new_name.id != folder_id:
            raise FolderAlreadyExist()

    async def delete_by_id(self, id_: int):
        await self._validate_delete(id_)
        await FolderCRUD().delete_creators_folder_by_id(self._creator_id, id_)

    async def _validate_delete(self, folder_id: int):
        folder = await FolderCRUD().get_by_id(folder_id)

        if folder.creator_id != self._creator_id:
            raise FolderAccessDenied()

        applet_exists_in_folder = await AppletsCRUD().check_folder(folder_id)
        if applet_exists_in_folder:
            raise FolderIsNotEmpty()