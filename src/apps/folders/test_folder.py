from apps.shared.test import BaseTest
from infrastructure.database import transaction


class TestFolder(BaseTest):
    fixtures = [
        "users/fixtures/users.json",
        "folders/fixtures/folders.json",
        "folders/fixtures/folders_applet.json",
    ]
    login_url = "/auth/login"
    list_url = "/folders"
    detail_url = "/folders/{id}"

    @transaction.rollback
    async def test_folder_list(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )

        response = await self.client.get(self.list_url)

        assert response.status_code == 200, response.json()
        assert len(response.json()["result"]) == 2
        assert response.json()["result"][0]["id"] == 2
        assert response.json()["result"][1]["id"] == 1

    @transaction.rollback
    async def test_create_folder(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )
        data = dict(name="Daily applets")

        response = await self.client.post(self.list_url, data)

        assert response.status_code == 201, response.json()
        assert response.json()["result"]["name"] == data["name"]
        assert response.json()["result"]["id"] == 5

    @transaction.rollback
    async def test_create_folder_with_already_exists(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )
        data = dict(name="Morning applets")

        response = await self.client.post(self.list_url, data)

        assert response.status_code == 422, response.json()
        assert (
            response.json()["result"][0]["message"]["en"]
            == "Folder already exists."
        )

    @transaction.rollback
    async def test_update_folder_name(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )
        data = dict(name="Daily applets")

        response = await self.client.put(self.detail_url.format(id=1), data)

        assert response.status_code == 200, response.json()
        assert response.json()["result"]["name"] == data["name"]

    @transaction.rollback
    async def test_update_folder_with_same_name_success(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )
        data = dict(name="Morning applets")

        response = await self.client.put(self.detail_url.format(id=1), data)

        assert response.status_code == 200, response.json()
        assert response.json()["result"]["name"] == data["name"]

    @transaction.rollback
    async def test_update_folder_name_with_already_exists(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )
        data = dict(name="Night applets")

        response = await self.client.put(self.detail_url.format(id=1), data)

        assert response.status_code == 422, response.json()
        assert (
            response.json()["result"][0]["message"]["en"]
            == "Folder already exists."
        )

    @transaction.rollback
    async def test_delete_folder(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )

        response = await self.client.delete(self.detail_url.format(id=1))
        assert response.status_code == 204, response.json()

    @transaction.rollback
    async def test_delete_not_belonging_folder(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )

        response = await self.client.delete(self.detail_url.format(id=3))

        assert response.status_code == 422, response.json()
        assert (
            response.json()["result"][0]["message"]["en"] == "Access denied."
        )

    @transaction.rollback
    async def test_delete_not_empty_folder(self):
        await self.client.login(
            self.login_url, "tom@mindlogger.com", "Test1234!"
        )

        response = await self.client.delete(self.detail_url.format(id=2))
        assert response.status_code == 422, response.json()
        assert (
            response.json()["result"][0]["message"]["en"]
            == "Folder has applets, move applets from folder to delete it."
        )