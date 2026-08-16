"""
POST /{env}/users

Spec: sdet_challenge_api.yml -> operationId: createUser
"""
import pytest


def test_create_user_happy_path_returns_201(api_client, user_payload, auth_token):
    response = api_client.create_user(user_payload)

    try:
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == user_payload["name"]
        assert body["email"] == user_payload["email"]
        assert body["age"] == user_payload["age"]
    finally:
        api_client.delete_user(user_payload["email"], token=auth_token)


@pytest.mark.parametrize("missing_field", ["name", "email", "age"])
def test_create_user_missing_required_field_returns_400(api_client, user_payload, missing_field):
    del user_payload[missing_field]

    response = api_client.create_user(user_payload)

    assert response.status_code == 400
    assert "error" in response.json()


@pytest.mark.parametrize(
    "age",
    [0, -5, 151, 1000, 30.5, "30", None],
    ids=["zero", "negative", "above-max", "way-above-max", "decimal", "string", "null"],
)
def test_create_user_invalid_age_returns_400(api_client, user_payload, age):
    user_payload["age"] = age

    response = api_client.create_user(user_payload)

    assert response.status_code == 400, (
        f"age={age!r} should be rejected per spec (minimum: 1, maximum: 150, "
        f"type: integer), got {response.status_code}"
    )


@pytest.mark.parametrize("age", [1, 150], ids=["min-boundary", "max-boundary"])
def test_create_user_age_boundary_values_are_accepted(api_client, user_payload, age, auth_token):
    user_payload["age"] = age

    response = api_client.create_user(user_payload)

    try:
        assert response.status_code == 201
    finally:
        api_client.delete_user(user_payload["email"], token=auth_token)


@pytest.mark.parametrize(
    "invalid_email",
    ["not-an-email", "missing-at-sign.com", "@no-local-part.com", "spaces in@email.com", ""],
)
def test_create_user_invalid_email_returns_400(api_client, user_payload, invalid_email, auth_token):
    user_payload["email"] = invalid_email

    response = api_client.create_user(user_payload)

    try:
        assert response.status_code == 400, (
            f"email={invalid_email!r} should fail format validation, got {response.status_code}"
        )
    finally:
        # API currently accepts these and creates the user anyway (see BUGS.md #1),
        # so clean up if that happens or it'll leak into other tests
        if response.status_code == 201:
            api_client.delete_user(invalid_email, token=auth_token)


def test_create_user_duplicate_email_same_environment_returns_409(api_client, user_payload, auth_token):
    first = api_client.create_user(user_payload)
    assert first.status_code == 201

    try:
        second = api_client.create_user(user_payload)
        assert second.status_code == 409
        assert "error" in second.json()
    finally:
        api_client.delete_user(user_payload["email"], token=auth_token)


def test_create_user_duplicate_email_different_case(api_client, user_payload, auth_token):
    # spec doesn't say if uniqueness is case-sensitive, so just documenting
    # whatever happens here rather than asserting one specific outcome
    first = api_client.create_user(user_payload)
    assert first.status_code == 201

    uppercased_payload = dict(user_payload, email=user_payload["email"].upper())
    try:
        second = api_client.create_user(uppercased_payload)
        assert second.status_code in (201, 409), (
            f"unexpected status for case-variant duplicate email: {second.status_code}"
        )
    finally:
        api_client.delete_user(user_payload["email"], token=auth_token)
        api_client.delete_user(uppercased_payload["email"], token=auth_token)


def test_create_user_same_email_different_environments_both_succeed(
    api_client, other_env_client, user_payload, auth_token
):
    # dev and prod are separate DBs per the spec, so the same email should
    # work fine in both independently
    first = api_client.create_user(user_payload)
    try:
        assert first.status_code == 201

        second = other_env_client.create_user(user_payload)
        try:
            assert second.status_code == 201
        finally:
            other_env_client.delete_user(user_payload["email"], token=auth_token)
    finally:
        api_client.delete_user(user_payload["email"], token=auth_token)


def test_create_user_extra_undocumented_field_in_body(api_client, user_payload, auth_token):
    # not really a bug either way, just curious what happens with a field
    # that's not in the schema - ignored, reflected back, or rejected?
    user_payload["role"] = "admin"

    response = api_client.create_user(user_payload)

    try:
        assert response.status_code in (201, 400)
    finally:
        api_client.delete_user(user_payload["email"], token=auth_token)
