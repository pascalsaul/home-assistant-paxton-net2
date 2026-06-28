from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import API_SCHEMA_VERSION, PaxtonNet2Api
from .const import *
from .coordinator import PaxtonNet2Coordinator

EXPECTED_API_SCHEMA_VERSION = 3


def _parse_id_set(value) -> set[str]:
    """Parse both legacy comma-separated IDs and selector lists."""
    if not value:
        return set()
    if isinstance(value, (list, tuple, set)):
        return {str(item).strip() for item in value if str(item).strip()}
    normalized = str(value).replace(";", ",").replace("\n", ",")
    return {item.strip() for item in normalized.split(",") if item.strip()}


@dataclass
class PaxtonNet2RuntimeData:
    api: PaxtonNet2Api
    coordinator: PaxtonNet2Coordinator
    server_settings: dict
    toggle_door_ids: set[str]
    relay2_door_ids: set[str]
    excluded_control_door_ids: set[str]


type PaxtonNet2ConfigEntry = ConfigEntry[PaxtonNet2RuntimeData]


async def _async_reload_entry(hass: HomeAssistant, entry: PaxtonNet2ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: PaxtonNet2ConfigEntry) -> bool:
    if API_SCHEMA_VERSION != EXPECTED_API_SCHEMA_VERSION:
        raise RuntimeError(
            "Paxton Net2 integration files are inconsistent. "
            f"Expected API schema {EXPECTED_API_SCHEMA_VERSION}, "
            f"loaded {API_SCHEMA_VERSION}. Remove the complete "
            "/config/custom_components/paxton_net2 directory and reinstall."
        )

    settings = {**entry.data, **entry.options}

    api = PaxtonNet2Api(
        async_get_clientsession(hass),
        base_url=settings[CONF_BASE_URL],
        username=settings[CONF_USERNAME],
        password=settings[CONF_PASSWORD],
        client_id=settings[CONF_CLIENT_ID],
        verify_ssl=settings[CONF_VERIFY_SSL],
        token_path=settings[CONF_TOKEN_PATH],
        doors_path=settings[CONF_DOORS_PATH],
        door_status_path=settings[CONF_DOOR_STATUS_PATH],
        door_id_field=settings[CONF_DOOR_ID_FIELD],
        door_name_field=settings[CONF_DOOR_NAME_FIELD],
    )
    coordinator = PaxtonNet2Coordinator(
        hass, entry, api, settings[CONF_POLL_INTERVAL]
    )
    await coordinator.async_config_entry_first_refresh()
    server_settings = await api.async_get_server_settings()
    entry.runtime_data = PaxtonNet2RuntimeData(
        api,
        coordinator,
        server_settings,
        _parse_id_set(settings.get(CONF_TOGGLE_DOOR_IDS)),
        _parse_id_set(settings.get(CONF_RELAY2_DOOR_IDS)),
        _parse_id_set(settings.get(CONF_EXCLUDED_CONTROL_DOOR_IDS)),
    )
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PaxtonNet2ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
