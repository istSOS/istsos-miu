import json
from app.main import app, get_pool
from fastapi import status
from async_asgi_testclient import TestClient
import asyncpg
import asyncio
from unittest import mock
import uuid

pgpool: asyncpg.Pool | None = None


async def override_get_pool():
    global pgpool
    if not pgpool:
        pgpool = await asyncpg.create_pool(dsn='postgresql://admin:admin@172.17.0.1:55432/istsos_test')
    return pgpool

app.dependency_overrides[get_pool] = override_get_pool


def test_get_contact_types():
    async def inner():
        async with TestClient(app) as client:
            resp = await client.get("/contact_types/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == {
            "contact_types": [
                "owner",
                "manufacturer",
                "operator"
            ]
        }
    asyncio.get_event_loop().run_until_complete(inner())


def test_create_contact():
    async def inner():
        async with TestClient(app) as client:
            contact = {
                "type": "owner",
                "person": "string",
                "telephone": "string",
                "fax": "string",
                "email": "string",
                "web": "string",
                "address": "string",
                "city": "string",
                "admin_area": "string",
                "postal_code": "string",
                "country": "string"
            }
            resp = await client.post("/contacts/", json=contact)
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json() == {
            "id": 1
        }
    asyncio.get_event_loop().run_until_complete(inner())


def test_get_contact():
    async def inner():
        async with TestClient(app) as client:
            resp = await client.get("/contacts/1")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == {
            "id": 1,
            "type": "owner",
            "person": "string",
            "telephone": "string",
            "fax": "string",
            "email": "string",
            "web": "string",
            "address": "string",
            "city": "string",
            "admin_area": "string",
            "postal_code": "string",
            "country": "string",
        }
    asyncio.get_event_loop().run_until_complete(inner())


def test_get_contacts():
    async def inner():
        async with TestClient(app) as client:
            resp = await client.get("/contacts/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == [{
            "id": 1,
            "type": "owner",
            "person": "string",
            "telephone": "string",
            "fax": "string",
            "email": "string",
            "web": "string",
            "address": "string",
            "city": "string",
            "admin_area": "string",
            "postal_code": "string",
            "country": "string",
        }]
    asyncio.get_event_loop().run_until_complete(inner())


def test_update_contact():
    async def inner():
        async with TestClient(app) as client:
            contact = {
                "type": "operator",
                "person": "string",
                "telephone": "string",
                "fax": "string",
                "email": "string",
                "web": "string",
                "address": "string",
                "city": "string",
                "admin_area": "string",
                "postal_code": "string",
                "country": "string"
            }
            resp = await client.put("/contacts/1", json=contact)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
    asyncio.get_event_loop().run_until_complete(inner())


def test_delete_contact():
    async def inner():
        async with TestClient(app) as client:
            resp = await client.delete("/contacts/1")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
    asyncio.get_event_loop().run_until_complete(inner())


def test_create_sensor_type():
    async def inner():
        async with TestClient(app) as client:
            sensorType = {
                "description": "string",
                "metadata": "string"
            }
            resp = await client.post("/sensor_types/", json=sensorType)
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json() == {
            "id": 1
        }
    asyncio.get_event_loop().run_until_complete(inner())


def test_get_sensor_type():
    async def inner():
        async with TestClient(app) as client:
            resp = await client.get("/sensor_types/1")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == {
            "id": 1,
            "description": "string",
            "metadata": "string"
        }
    asyncio.get_event_loop().run_until_complete(inner())


def test_get_sensor_types():
    async def inner():
        async with TestClient(app) as client:
            resp = await client.get("/sensor_types/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == [{
            "id": 1,
            "description": "string",
            "metadata": "string"
        }]
    asyncio.get_event_loop().run_until_complete(inner())


def test_update_sensor_type():
    async def inner():
        async with TestClient(app) as client:
            sensorType = {
                "description": "new_string",
                "metadata": "new_string"
            }
            resp = await client.put("/sensor_types/1", json=sensorType)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
    asyncio.get_event_loop().run_until_complete(inner())


def test_delete_sensor_type():
    async def inner():
        async with TestClient(app) as client:
            resp = await client.delete("/sensor_types/1")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
    asyncio.get_event_loop().run_until_complete(inner())


global ID


def generateID():
    return str(uuid.uuid4())


def test_create_sensor():
    async def inner():
        with mock.patch('uuid.uuid4', return_value='6f35d187-eb31-4a5f-9df8-2cf2111ddbee'):
            ID = generateID()
        async with TestClient(app) as client:
            sensor = {
                "id": ID,
                "name": "string",
                "description": "string",
                "encoding_type": "string",
                "sampling_time_resolution": 0,
                "acquisition_time_resolution": 0,
                "sensor_type": {
                    "description": "string",
                    "metadata": "string"
                },
                "contact": {
                    "type": "owner",
                    "person": "string",
                    "telephone": "string",
                    "fax": "string",
                    "email": "string",
                    "web": "string",
                    "address": "string",
                    "city": "string",
                    "admin_area": "string",
                    "postal_code": "string",
                    "country": "string"
                }
            }
            resp = await client.post("/sensors/", json=sensor)
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json() == {
            "id": ID
        }
    asyncio.get_event_loop().run_until_complete(inner())


def test_get_sensor():
    with mock.patch('uuid.uuid4', return_value='6f35d187-eb31-4a5f-9df8-2cf2111ddbee'):
        ID = generateID()

    async def inner():
        async with TestClient(app) as client:
            resp = await client.get(f"/sensors/{ID}")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == {
            "id": ID,
            "name": "string",
            "description": "string",
            "encoding_type": "string",
            "sampling_time_resolution": "0:00:00",
            "acquisition_time_resolution": "0:00:00",
            "sensor_type_id": 2
        }
    asyncio.get_event_loop().run_until_complete(inner())


def test_get_sensors():
    ID = None
    with mock.patch('uuid.uuid4', return_value='6f35d187-eb31-4a5f-9df8-2cf2111ddbee'):
        ID = generateID()

    async def inner():
        async with TestClient(app) as client:
            resp = await client.get("/sensors/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == [{
            "id": ID,
            "name": "string",
            "description": "string",
            "encoding_type": "string",
            "sampling_time_resolution": "0:00:00",
            "acquisition_time_resolution": "0:00:00",
            "sensor_type_id": 2
        }]
    asyncio.get_event_loop().run_until_complete(inner())


def test_update_sensor():
    ID = None
    with mock.patch('uuid.uuid4', return_value='6f35d187-eb31-4a5f-9df8-2cf2111ddbee'):
        ID = generateID()

    async def inner():
        async with TestClient(app) as client:
            sensor = {
                "name": "string2",
                "description": "string",
                "encoding_type": "string",
                "sampling_time_resolution": 0,
                "acquisition_time_resolution": 0,
                "sensor_type": 2
            }
            resp = await client.put(f"/sensors/{ID}", json=sensor)
        assert resp.status_code == status.HTTP_204_NO_CONTENT
    asyncio.get_event_loop().run_until_complete(inner())


def test_delete_sensor():
    ID = None
    with mock.patch('uuid.uuid4', return_value='6f35d187-eb31-4a5f-9df8-2cf2111ddbee'):
        ID = generateID()

    async def inner():
        async with TestClient(app) as client:
            resp = await client.delete(f"/sensors/{ID}")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
    asyncio.get_event_loop().run_until_complete(inner())
