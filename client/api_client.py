"""
Thin HTTP client for the User Management API.

Keeps test files free of raw `requests` calls and URL-building logic.
Each method returns the raw `requests.Response` so tests keep full
control over which assertions they want to make (status code, body,
headers, etc).
"""
from __future__ import annotations

import requests


class UserApiClient:
    def __init__(self, base_url: str, environment: str, auth_token: str | None = None):
        """
        base_url: e.g. "http://localhost:3000"
        environment: "dev" or "prod" (used as URL prefix)
        auth_token: token sent on the Authentication header when required
        """
        self.base_url = base_url.rstrip("/")
        self.environment = environment
        self.auth_token = auth_token

    def _url(self, path: str = "") -> str:
        path = path.lstrip("/")
        return f"{self.base_url}/{self.environment}/users{('/' + path) if path else ''}"

    # ---- endpoints -------------------------------------------------

    def list_users(self) -> requests.Response:
        return requests.get(self._url())

    def create_user(self, payload: dict) -> requests.Response:
        return requests.post(self._url(), json=payload)

    def get_user(self, email: str) -> requests.Response:
        return requests.get(self._url(email))

    def update_user(self, email: str, payload: dict) -> requests.Response:
        return requests.put(self._url(email), json=payload)

    def delete_user(self, email: str, token: str | None = None) -> requests.Response:
        """
        token overrides self.auth_token for this call, so tests can
        exercise "no token" / "invalid token" scenarios explicitly.
        """
        headers = {}
        effective_token = token if token is not None else self.auth_token
        if effective_token:
            headers["Authentication"] = effective_token
        return requests.delete(self._url(email), headers=headers)
