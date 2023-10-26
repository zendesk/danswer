import time
from typing import Any

import requests


class ZendeskApiClientRequestFailedError(ConnectionError):
    def __init__(self, status: int, error: str) -> None:
        super().__init__(
            "Zendesk API Client request failed with status {status}: {error}".format(
                status=status, error=error
            )
        )


class ZendeskApiClient:
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
    ) -> None:
        # TODO: support OAuth token auth as well
        self.base_url = base_url
        self.username = username
        self.password = password

    def get(self, endpoint: str, params: dict[str, str]) -> dict[str, Any]:
        url: str = self._build_url(endpoint)
        headers = {"Accept": "application/json"}
        response = requests.get(
            url, headers=headers, auth=(self.username, self.password), params=params
        )

        try:
            json = response.json()
        except Exception:
            json = {}

        # handle rate limiting
        if response.status_code == 429:
            seconds_to_wait = int(response.headers["Retry-After"])
            time.sleep(seconds_to_wait)
            return self.get(endpoint, params)

        # handle errors
        if response.status_code >= 300:
            error = response.reason
            response_error = json.get("error", "")
            if response_error:
                error = response_error
            raise ZendeskApiClientRequestFailedError(response.status_code, error)

        return json

    def _build_url(self, endpoint: str) -> str:
        return self.base_url.rstrip("/") + "/" + endpoint.lstrip("/")
