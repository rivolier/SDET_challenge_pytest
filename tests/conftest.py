import os
import sys
import uuid

import pytest

# so "from client.api_client import UserApiClient" works regardless of
# where pytest gets invoked from
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from client.api_client import UserApiClient  # noqa: E402

# API_ENV picks which prefix (dev/prod) the suite hits. Same suite gets
# reused for both CI jobs by just flipping this instead of duplicating tests.
BASE_URL = os.environ.get("BASE_URL", "http://localhost:3000")
API_ENV = os.environ.get("API_ENV", "dev")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "mysecrettoken")


@pytest.fixture(scope="session")
def environment() -> str:
    return API_ENV


@pytest.fixture(scope="session")
def auth_token() -> str:
    return AUTH_TOKEN


@pytest.fixture(scope="session")
def api_client(environment, auth_token) -> UserApiClient:
    return UserApiClient(base_url=BASE_URL, environment=environment, auth_token=auth_token)


@pytest.fixture
def unique_email() -> str:
    # fresh email per test so parallel runs/re-runs don't collide
    return f"qa.{uuid.uuid4().hex[:12]}@example.com"


@pytest.fixture
def user_payload(unique_email) -> dict:
    return {"name": "QA Test User", "email": unique_email, "age": 30}


@pytest.fixture
def created_user(api_client, user_payload):
    # creates the user and cleans it up after, no matter what the test
    # does to it (updates it, deletes it, leaves it alone)
    response = api_client.create_user(user_payload)
    assert response.status_code == 201, (
        f"setup failed: could not create user for test "
        f"(status={response.status_code}, body={response.text})"
    )
    yield response.json()

    api_client.delete_user(user_payload["email"])


@pytest.fixture(scope="session")
def other_environment() -> str:
    # for cross-env isolation checks - just the opposite of whatever we're running against
    return "prod" if API_ENV == "dev" else "dev"


@pytest.fixture(scope="session")
def other_env_client(other_environment, auth_token) -> UserApiClient:
    return UserApiClient(base_url=BASE_URL, environment=other_environment, auth_token=auth_token)


@pytest.fixture
def cleanup_emails(api_client):
    # for tests that create users with emails we don't know ahead of time
    # (e.g. renaming to a new email mid-test) - just append here and it gets deleted after
    emails_to_delete = []
    yield emails_to_delete
    for email in emails_to_delete:
        api_client.delete_user(email)
