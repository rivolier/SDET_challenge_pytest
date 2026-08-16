"""
GET /{env}/users

Spec: sdet_challenge_api.yml -> operationId: listUsers
"""


def test_list_users_returns_200_and_array(api_client):
    response = api_client.list_users()

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)


def test_created_user_appears_in_list(api_client, created_user):
    response = api_client.list_users()
    body = response.json()

    emails_in_list = [user["email"] for user in body]
    assert created_user["email"] in emails_in_list


def test_deleted_user_no_longer_appears_in_list(api_client, user_payload, auth_token):
    api_client.create_user(user_payload)
    api_client.delete_user(user_payload["email"], token=auth_token)

    response = api_client.list_users()
    emails_in_list = [user["email"] for user in response.json()]

    assert user_payload["email"] not in emails_in_list
