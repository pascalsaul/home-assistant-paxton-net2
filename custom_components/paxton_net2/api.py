from __future__ import annotations

API_SCHEMA_VERSION = 3

import asyncio
import base64
import json
import time
from typing import Any
from urllib.parse import urljoin

from aiohttp import ClientError, ClientResponseError, ClientSession

from .const import DEFAULT_CLOSE_PATH, DEFAULT_CONTROL_PATH, DEFAULT_HOLD_OPEN_PATH, DEFAULT_OPEN_PATH, SERVER_SETTINGS_PATHS


class PaxtonNet2ApiError(Exception):
    pass


class PaxtonNet2AuthenticationError(PaxtonNet2ApiError):
    pass


class PaxtonNet2Api:
    def __init__(
        self,
        session: ClientSession,
        *,
        base_url: str,
        username: str,
        password: str,
        client_id: str,
        verify_ssl: bool,
        token_path: str,
        doors_path: str,
        door_status_path: str,
        door_id_field: str,
        door_name_field: str,
    ) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/") + "/"
        self._username = username
        self._password = password
        self._client_id = client_id
        self._verify_ssl = verify_ssl
        self._token_path = token_path
        self._doors_path = doors_path
        self._door_status_path = door_status_path
        self.door_id_field = door_id_field
        self.door_name_field = door_name_field
        self._access_token: str | None = None
        self._refresh_token: str | None = None
        self._token_valid_until = 0.0
        self._token_lock = asyncio.Lock()

    def _url(self, path: str) -> str:
        return urljoin(self._base_url, path.lstrip("/"))

    @staticmethod
    def _jwt_exp(token: str) -> float | None:
        try:
            parts = token.split(".")
            if len(parts) != 3:
                return None
            payload = parts[1] + "=" * (-len(parts[1]) % 4)
            return float(json.loads(base64.urlsafe_b64decode(payload.encode())).get("exp"))
        except Exception:
            return None

    async def async_authenticate(self, force: bool = False) -> None:
        if not force and self._access_token and time.time() < self._token_valid_until - 60:
            return
        async with self._token_lock:
            if not force and self._access_token and time.time() < self._token_valid_until - 60:
                return
            try:
                token_data = (
                    {
                        "grant_type": "refresh_token",
                        "refresh_token": self._refresh_token,
                        "client_id": self._client_id,
                    }
                    if self._refresh_token and not force
                    else {
                        "username": self._username,
                        "password": self._password,
                        "grant_type": "password",
                        "client_id": self._client_id,
                    }
                )
                async with self._session.post(
                    self._url(self._token_path),
                    data=token_data,
                    headers={"Accept": "application/json"},
                    ssl=self._verify_ssl,
                    timeout=20,
                ) as response:
                    if response.status in (400, 401, 403):
                        raise PaxtonNet2AuthenticationError(
                            f"Token request rejected: HTTP {response.status}"
                        )
                    response.raise_for_status()
                    payload = await response.json()
            except PaxtonNet2AuthenticationError:
                raise
            except (ClientError, ClientResponseError, TimeoutError, ValueError) as err:
                raise PaxtonNet2ApiError(f"Token request failed: {err}") from err

            token = payload.get("access_token") or payload.get("accessToken")
            if not token:
                raise PaxtonNet2AuthenticationError("No access_token in response")
            self._access_token = str(token)
            refresh_token = payload.get("refresh_token") or payload.get("refreshToken")
            if refresh_token:
                self._refresh_token = str(refresh_token)
            expires_in = payload.get("expires_in") or payload.get("expiresIn")
            try:
                self._token_valid_until = time.time() + float(expires_in)
            except (TypeError, ValueError):
                self._token_valid_until = self._jwt_exp(self._access_token) or time.time() + 300

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        retry_auth: bool = True,
    ) -> Any:
        await self.async_authenticate()
        try:
            async with self._session.request(
                method,
                self._url(path),
                headers={
                    "Authorization": f"Bearer {self._access_token}",
                    "Accept": "application/json",
                },
                json=json_body,
                ssl=self._verify_ssl,
                timeout=20,
            ) as response:
                if response.status == 401 and retry_auth:
                    await self.async_authenticate(force=True)
                    return await self._request(
                        method, path, json_body=json_body, retry_auth=False
                    )
                if response.status in (401, 403):
                    raise PaxtonNet2AuthenticationError(
                        f"Net2 rejected request: HTTP {response.status}"
                    )
                response.raise_for_status()
                if response.status == 204 or response.content_length == 0:
                    return None
                if "json" in response.headers.get("Content-Type", "").lower():
                    return await response.json()
                return await response.text()
        except PaxtonNet2AuthenticationError:
            raise
        except (ClientError, ClientResponseError, TimeoutError) as err:
            raise PaxtonNet2ApiError(str(err)) from err

    @staticmethod
    def _extract_list(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [x for x in payload if isinstance(x, dict)]
        if isinstance(payload, dict):
            for key in ("doors", "Doors", "statuses", "Statuses", "items", "Items", "data", "Data", "results"):
                if isinstance(payload.get(key), list):
                    return [x for x in payload[key] if isinstance(x, dict)]
        return []

    def get_door_id(self, item: dict[str, Any]) -> Any:
        for key in (
            self.door_id_field, "Id", "id", "DoorId", "doorId", "DeviceId", "deviceId"
        ):
            if item.get(key) is not None:
                return item[key]
        return None

    def get_door_name(self, item: dict[str, Any]) -> str | None:
        for key in (self.door_name_field, "Name", "name", "DoorName", "doorName"):
            if item.get(key):
                return str(item[key])
        return None

    @staticmethod
    def _relay_open(item: dict[str, Any]) -> bool | None:
        values = [
            item.get("doorRelayOpen"),
            item.get("DoorRelayOpen"),
            item.get("isOpen"),
            item.get("IsOpen"),
        ]
        nested = item.get("status") or item.get("Status")
        if isinstance(nested, dict):
            values.extend([
                nested.get("doorRelayOpen"),
                nested.get("DoorRelayOpen"),
                nested.get("isOpen"),
                nested.get("IsOpen"),
            ])
        for value in values:
            if isinstance(value, bool):
                return value
            if isinstance(value, (int, float)):
                return bool(value)
            if isinstance(value, str):
                v = value.strip().lower()
                if v in {"true", "open", "opened", "held open", "1", "on"}:
                    return True
                if v in {"false", "closed", "close", "0", "off"}:
                    return False
        return None

    async def async_get_combined_doors(self) -> list[dict[str, Any]]:
        doors_payload = await self._request("GET", self._doors_path)
        doors = self._extract_list(doors_payload)
        if not doors and isinstance(doors_payload, dict):
            doors = [doors_payload]

        statuses: list[dict[str, Any]] = []
        if self._door_status_path.strip():
            try:
                status_payload = await self._request("GET", self._door_status_path)
                statuses = self._extract_list(status_payload)
                if not statuses and isinstance(status_payload, dict):
                    statuses = [status_payload]
            except PaxtonNet2ApiError:
                statuses = []

        status_by_id = {}
        for status in statuses:
            door_id = self.get_door_id(status)
            if door_id is not None:
                status_by_id[str(door_id)] = status

        result = []
        for door in doors:
            door_id = self.get_door_id(door)
            if door_id is None:
                continue
            merged = dict(door)
            status = status_by_id.get(str(door_id))
            if status:
                merged["_net2_status"] = status
                relay_open = self._relay_open(status)
                if relay_open is not None:
                    merged["_door_relay_open"] = relay_open
            result.append(merged)

        if not result:
            raise PaxtonNet2ApiError("No usable doors returned")
        return result

    def door_is_open(self, door: dict[str, Any]) -> bool | None:
        value = door.get("_door_relay_open")
        if isinstance(value, bool):
            return value
        return self._relay_open(door)

    async def async_open_once(self, door_id: str | int) -> None:
        """Open a door using its configured Net2 unlock time and door logic."""
        await self._request(
            "POST",
            DEFAULT_OPEN_PATH,
            json_body={"doorId": int(door_id)},
        )

    async def async_set_door(self, door_id: str | int, open_: bool) -> None:
        """Hold a door open, or close/reinstate it."""
        path = DEFAULT_HOLD_OPEN_PATH if open_ else DEFAULT_CLOSE_PATH
        await self._request("POST", path, json_body={"doorId": int(door_id)})

    async def async_control_relay(
        self,
        door_id: str | int,
        relay_id: str,
        relay_action: str,
    ) -> None:
        """Control a specific door relay."""
        await self._request(
            "POST",
            DEFAULT_CONTROL_PATH,
            json_body={
                "doorId": int(door_id),
                "relayFunction": {
                    "relayId": relay_id,
                    "relayAction": relay_action,
                },
                "ledFlash": "NoLed",
            },
        )

    async def async_get_server_settings(self) -> dict[str, Any]:
        """Retrieve available Net2 server metadata endpoints."""
        result: dict[str, Any] = {}
        for key, path in SERVER_SETTINGS_PATHS.items():
            try:
                result[key] = await self._request("GET", path)
            except PaxtonNet2ApiError as err:
                result[key] = {"available": False, "error": str(err)}
        return result
