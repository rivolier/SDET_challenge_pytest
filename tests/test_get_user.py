"""
GET /{env}/users/{email}

Spec: sdet_challenge_api.yml -> operationId: getUser
"""


def test_get_existing_user_returns_200_with_correct_data(api_client, created_user):
    response = api_client.get_user(created_user["email"])

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == created_user["email"]
    assert body["name"] == created_user["name"]
    assert body["age"] == created_user["age"]


def test_get_nonexistent_user_returns_404(api_client, unique_email):
    response = api_client.get_user(unique_email)

    assert response.status_code == 404
    body = response.json()
    assert "error" in body


def test_get_malformed_email_in_path(api_client):
    # spec says format: email on the path param but doesn't really say what
    # should happen with something clearly invalid - documenting whatever
    # the API actually does here, flag it in BUGS.md if it's neither
    response = api_client.get_user("not-an-email")

    assert response.status_code in (400, 404), (
        f"unexpected status for malformed email in path: {response.status_code}, "
        f"body={response.text}"
    )
