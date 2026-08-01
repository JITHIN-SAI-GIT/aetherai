import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from mongomock_motor import AsyncMongoMockClient

from main import app
from app.db.mongo import MongoDBManager

@pytest.fixture(autouse=True)
def mock_mongodb():
    client = AsyncMongoMockClient()
    MongoDBManager.client = client
    MongoDBManager.db = client["test_db"]
    yield
    MongoDBManager.client = None
    MongoDBManager.db = None

@pytest.fixture
def client():
    return TestClient(app)
