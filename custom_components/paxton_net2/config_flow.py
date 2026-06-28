from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .api import PaxtonNet2Api, PaxtonNet2ApiError, PaxtonNet2AuthenticationError
from .const import *


CONNECTION_KEYS = (
    CONF_BASE_URL,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_CLIENT_ID,
    CONF_VERIFY_SSL,
    CONF_TOKEN_PATH,
    CONF_DOORS_PATH,
    CONF_DOOR_STATUS_PATH,
    CONF_DOOR_ID_FIELD,
    CONF_DOOR_NAME_FIELD,
)


def connection_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema({
        vol.Required(CONF_BASE_URL, default=d.get(CONF_BASE_URL, "https://NET2-SERVER:8443")): str,
        vol.Required(CONF_USERNAME, default=d.get(CONF_USERNAME, "")): str,
        vol.Required(CONF_PASSWORD, default=d.get(CONF_PASSWORD, "")): str,
        vol.Required(CONF_CLIENT_ID, default=d.get(CONF_CLIENT_ID, "")): str,
        vol.Required(CONF_VERIFY_SSL, default=d.get(CONF_VERIFY_SSL, False)): bool,
        vol.Required(CONF_TOKEN_PATH, default=d.get(CONF_TOKEN_PATH, DEFAULT_TOKEN_PATH)): str,
        vol.Required(CONF_DOORS_PATH, default=d.get(CONF_DOORS_PATH, DEFAULT_DOORS_PATH)): str,
        vol.Required(
            CONF_DOOR_STATUS_PATH,
            default=d.get(CONF_DOOR_STATUS_PATH, DEFAULT_DOOR_STATUS_PATH),
        ): str,
        vol.Required(CONF_DOOR_ID_FIELD, default=d.get(CONF_DOOR_ID_FIELD, DEFAULT_DOOR_ID_FIELD)): str,
        vol.Required(CONF_DOOR_NAME_FIELD, default=d.get(CONF_DOOR_NAME_FIELD, DEFAULT_DOOR_NAME_FIELD)): str,
    })


def _selected_ids(value: Any) -> list[str]:
    """Normalize legacy comma-separated values and new selector lists."""
    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value]
    normalized = str(value).replace(";", ",").replace("\n", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def options_schema(
    defaults: dict[str, Any] | None = None,
    door_options: list[SelectOptionDict] | None = None,
) -> vol.Schema:
    d = defaults or {}
    choices = door_options or []

    def door_selector() -> SelectSelector:
        return SelectSelector(
            SelectSelectorConfig(
                options=choices,
                multiple=True,
                mode=SelectSelectorMode.DROPDOWN,
            )
        )

    return vol.Schema({
        vol.Required(
            CONF_POLL_INTERVAL,
            default=d.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL),
        ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
        vol.Optional(
            CONF_TOGGLE_DOOR_IDS,
            default=_selected_ids(d.get(CONF_TOGGLE_DOOR_IDS)),
        ): door_selector(),
        vol.Optional(
            CONF_RELAY2_DOOR_IDS,
            default=_selected_ids(d.get(CONF_RELAY2_DOOR_IDS)),
        ): door_selector(),
        vol.Optional(
            CONF_EXCLUDED_CONTROL_DOOR_IDS,
            default=_selected_ids(d.get(CONF_EXCLUDED_CONTROL_DOOR_IDS)),
        ): door_selector(),
    })


async def _validate_input(hass, data: dict[str, Any]) -> None:
    api = PaxtonNet2Api(
        async_get_clientsession(hass),
        base_url=data[CONF_BASE_URL],
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        client_id=data[CONF_CLIENT_ID],
        verify_ssl=data[CONF_VERIFY_SSL],
        token_path=data[CONF_TOKEN_PATH],
        doors_path=data[CONF_DOORS_PATH],
        door_status_path=data[CONF_DOOR_STATUS_PATH],
        door_id_field=data[CONF_DOOR_ID_FIELD],
        door_name_field=data[CONF_DOOR_NAME_FIELD],
    )
    await api.async_get_combined_doors()


class PaxtonNet2ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 4

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return PaxtonNet2OptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_BASE_URL].rstrip("/").lower())
            self._abort_if_unique_id_configured()
            full_data = {
                **user_input,
                CONF_POLL_INTERVAL: DEFAULT_POLL_INTERVAL,
            }
            try:
                await _validate_input(self.hass, full_data)
            except PaxtonNet2AuthenticationError:
                errors["base"] = "invalid_auth"
            except PaxtonNet2ApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            if not errors:
                return self.async_create_entry(title="Paxton Net2", data=full_data)
        return self.async_show_form(
            step_id="user",
            data_schema=connection_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input=None):
        entry = self._get_reconfigure_entry()
        current = {**entry.data, **entry.options}
        errors = {}

        if user_input is not None:
            candidate = {
                **entry.data,
                **entry.options,
                **user_input,
            }
            try:
                await _validate_input(self.hass, candidate)
            except PaxtonNet2AuthenticationError:
                errors["base"] = "invalid_auth"
            except PaxtonNet2ApiError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        key: user_input[key]
                        for key in CONNECTION_KEYS
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=connection_schema(user_input or current),
            errors=errors,
        )


class PaxtonNet2OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {
            **self._config_entry.data,
            **self._config_entry.options,
        }

        coordinator = getattr(self._config_entry.runtime_data, "coordinator", None)
        door_options: list[SelectOptionDict] = []
        if coordinator is not None:
            api = coordinator.api
            for door_id, door in sorted(
                coordinator.data.items(),
                key=lambda item: (api.get_door_name(item[1]) or "").lower(),
            ):
                name = api.get_door_name(door) or f"Door {door_id}"
                door_options.append(
                    SelectOptionDict(
                        value=str(door_id),
                        label=f"{name} — {door_id}",
                    )
                )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema(current, door_options),
        )
