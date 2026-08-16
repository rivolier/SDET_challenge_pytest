"""
PUT /{env}/users/{email}

Spec: sdet_challenge_api.yml -> operationId: updateUser
"""
import uuid

import pytest


def test_update_user_happy_path_returns_200(api_client, created_user):
    updated_payload = {
        "name": "Updated Name",
        "email": created_user["email"],
        "age": 45,
    }

    response = api_client.update_user(created_user["email"], updated_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Updated Name"
    assert body["age"] == 45


def test_update_nonexistent_user_returns_404(api_client, unique_email, user_payload):
    payload = dict(user_payload, email=unique_email)

    response = api_client.update_user(unique_email, payload)

    assert response.status_code == 404


@pytest.mark.parametrize("missing_field", ["name", "email", "age"])
def test_update_user_missing_required_field_returns_400(api_client, created_user, missing_field):
    payload = {
        "name": created_user["name"],
        "email": created_user["email"],
        "age": created_user["age"],
    }
    del payload[missing_field]

    response = api_client.update_user(created_user["email"], payload)

    assert response.status_code == 400


@pytest.mark.parametrize("age", [0, -1, 151, 30.5, "thirty"])
def test_update_user_invalid_age_returns_400(api_client, created_user, age):
    payload = {"name": created_user["name"], "email": created_user["email"], "age": age}

    response = api_client.update_user(created_user["email"], payload)

    assert response.status_code == 400


def test_update_user_email_in_body_differs_from_path(api_client, created_user, cleanup_emails, auth_token):
    # email is the PK per the spec, but it's also a required field in the update
    # body, and the spec never says what happens if they don't match. Going with
    # 400 here since the path should be the source of truth for which user is
    # being updated - if the API does something else, that's a bug (see BUGS.md).
    new_email = f"renamed.{created_user['email']}"
    cleanup_emails.append(new_email)  # in case it actually gets renamed

    payload = {"name": created_user["name"], "email": new_email, "age": created_user["age"]}
    response = api_client.update_user(created_user["email"], payload)

    assert response.status_code == 400, (
        f"expected 400 when body email differs from path email, got "
        f"{response.status_code}, body={response.text}"
    )


def test_update_user_to_email_that_already_exists_returns_409(
    api_client, created_user, cleanup_emails, auth_token
):
    # generating the second email with uuid instead of pulling from a fixture
    # on purpose - unique_email is cached per-test, and created_user already
    # consumed one instance of it, so asking for it again here just hands back
    # the same value and turns this into a duplicate-email create by accident
    other_payload = {"name": "Another User", "email": f"qa.{uuid.uuid4().hex[:12]}@example.com", "age": 25}
    other_created = api_client.create_user(other_payload)
    assert other_created.status_code == 201
    cleanup_emails.append(other_payload["email"])

    payload = {
        "name": created_user["name"],
        "email": other_payload["email"],
        "age": created_user["age"],
    }
    response = api_client.update_user(created_user["email"], payload)

    assert response.status_code == 409


def test_update_user_wrong_environment_returns_404(api_client, other_env_client, created_user):
    # user only exists in one env, updating through the other env's prefix should 404
    payload = {
        "name": "Should Not Apply",
        "email": created_user["email"],
        "age": created_user["age"],
    }

    response = other_env_client.update_user(created_user["email"], payload)

    assert response.status_code == 404
