"""
Behavior not tied to a single documented operation: invalid
environment prefixes, unsupported HTTP verbs. Not explicitly covered
by the spec, but worth checking since the app only advertises "dev"
and "prod" as valid environments.
"""
import requests


def test_invalid_environment_prefix(user_payload):
    # only dev/prod are documented - hitting anything else shouldn't
    # silently succeed or leak data somewhere weird
    response = requests.get("http://localhost:3000/staging/users")

    assert response.status_code in (404, 400), (
        f"unexpected status for undocumented environment prefix: {response.status_code}"
    )


def test_unsupported_http_verb_on_collection(environment):
    response = requests.patch(f"http://localhost:3000/{environment}/users")

    assert response.status_code in (404, 405)


def test_create_user_with_wrong_content_type(environment, user_payload):
    response = requests.post(
        f"http://localhost:3000/{environment}/users",
        data=str(user_payload),
        headers={"Content-Type": "text/plain"},
    )

    assert response.status_code == 400
