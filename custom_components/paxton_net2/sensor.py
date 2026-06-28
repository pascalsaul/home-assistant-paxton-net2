from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import PaxtonNet2ConfigEntry
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class ServerSettingDescription:
    key: str
    name: str
    icon: str


DESCRIPTIONS = (
    ServerSettingDescription(key="version", name="Version", icon="mdi:package-up"),
    ServerSettingDescription(
        key="product_type", name="Product type", icon="mdi:information-outline"
    ),
    ServerSettingDescription(key="features", name="Features", icon="mdi:list-box"),
    ServerSettingDescription(
        key="properties", name="Properties", icon="mdi:tune-variant"
    ),
    ServerSettingDescription(
        key="version_history", name="Version history", icon="mdi:history"
    ),
)


def _extract_scalar(value: Any) -> str | int | float | None:
    if value is None:
        return None
    if isinstance(value, (str, int, float)):
        return value
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, dict):
        for key in (
            "version",
            "Version",
            "productType",
            "ProductType",
            "name",
            "Name",
            "value",
            "Value",
        ):
            candidate = value.get(key)
            if isinstance(candidate, (str, int, float, bool)):
                return candidate
        if value.get("available") is False:
            return "Unavailable"
        return len(value)
    if isinstance(value, list):
        return len(value)
    return str(value)[:255]


def _attributes(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return {"items": value}
    return {"raw_value": value}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PaxtonNet2ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(
        PaxtonNet2ServerSettingSensor(entry, description)
        for description in DESCRIPTIONS
    )


class PaxtonNet2ServerSettingSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: PaxtonNet2ConfigEntry,
        description: ServerSettingDescription,
    ) -> None:
        self._entry = entry
        self._description = description
        self._attr_unique_id = f"{entry.entry_id}_server_{description.key}"
        self._attr_name = description.name
        self._attr_icon = description.icon

    @property
    def _value(self) -> Any:
        return self._entry.runtime_data.server_settings.get(
            self._description.key
        )

    @property
    def native_value(self):
        return _extract_scalar(self._value)

    @property
    def extra_state_attributes(self):
        return _attributes(self._value)

    @property
    def available(self) -> bool:
        value = self._value
        return not (
            isinstance(value, dict) and value.get("available") is False
        )

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_server")},
            "name": "Paxton Net2 Server",
            "manufacturer": "Paxton",
            "model": "Net2",
            "configuration_url": self._entry.data.get("base_url"),
        }
