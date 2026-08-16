"""
DELETE /{env}/users/{email}

Spec: sdet_challenge_api.yml -> operationId: deleteUser
Requires the "Authentication" header. This is the only endpoint the
spec documents as requiring auth -- other endpoints are exercised for
auth behavior too, in test_create_user.py / test_update_user.py /
test_get_user.py, to confirm they do NOT require it as documented.
"""


def test_delete_without_token_returns_401(api_client, created_user):
    response = api_client.delete_user(created_user["email"], token="")

    assert response.status_code == 401


def test_delete_with_invalid_token_returns_401(api_client, created_user, auth_token):
    response = api_client.delete_user(created_user["email"], token="not-the-real-token")

    assert response.status_code == 401


def test_delete_existing_user_with_valid_token_returns_204(api_client, user_payload, auth_token):
    api_client.create_user(user_payload)

    response = api_client.delete_user(user_payload["email"], token=auth_token)

    assert response.status_code == 204


def test_delete_nonexistent_user_returns_404(api_client, unique_email, auth_token):
    response = api_client.delete_user(unique_email, token=auth_token)

    assert response.status_code == 404


def test_double_delete_returns_404_on_second_attempt(api_client, user_payload, auth_token):
    api_client.create_user(user_payload)
    email = user_payload["email"]

    first = api_client.delete_user(email, token=auth_token)
    second = api_client.delete_user(email, token=auth_token)

    assert first.status_code == 204
    assert second.status_code == 404


def test_deleted_user_is_not_retrievable(api_client, user_payload, auth_token):
    api_client.create_user(user_payload)
    email = user_payload["email"]

    api_client.delete_user(email, token=auth_token)
    response = api_client.get_user(email)

    assert response.status_code == 404
