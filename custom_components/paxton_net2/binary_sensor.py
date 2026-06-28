from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import PaxtonNet2ConfigEntry
from .const import DOMAIN
from .coordinator import PaxtonNet2Coordinator


def _nested_status(door: dict[str, Any]) -> dict[str, Any]:
    status = door.get("_net2_status")
    if isinstance(status, dict):
        nested = status.get("status") or status.get("Status")
        if isinstance(nested, dict):
            return nested
        return status
    status = door.get("status") or door.get("Status")
    return status if isinstance(status, dict) else {}


@dataclass(frozen=True, kw_only=True)
class PaxtonStatusDescription:
    key: str
    name: str
    value_fn: Callable[[dict[str, Any]], bool | None]
    device_class: BinarySensorDeviceClass | None = None
    icon_on: str | None = None
    icon_off: str | None = None
    entity_category: EntityCategory | None = None
    enabled_by_default: bool = True


def _bool_value(field: str, *, invert: bool = False):
    def value(door: dict[str, Any]) -> bool | None:
        raw = _nested_status(door).get(field)
        if not isinstance(raw, bool):
            return None
        return not raw if invert else raw
    return value


DESCRIPTIONS = (
    PaxtonStatusDescription(
        key="door_open",
        name="Door open",
        value_fn=_bool_value("doorContactClosed", invert=True),
        device_class=BinarySensorDeviceClass.DOOR,
    ),
    PaxtonStatusDescription(
        key="unlocked",
        name="Unlocked",
        value_fn=_bool_value("doorRelayOpen"),
        device_class=BinarySensorDeviceClass.LOCK,
        icon_on="mdi:lock-open-variant",
        icon_off="mdi:lock",
    ),
    PaxtonStatusDescription(
        key="alarm",
        name="Alarm",
        value_fn=_bool_value("alarmTripped"),
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PaxtonStatusDescription(
        key="tamper",
        name="Tamper",
        value_fn=_bool_value("tamperContactClosed", invert=True),
        device_class=BinarySensorDeviceClass.TAMPER,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    PaxtonStatusDescription(
        key="psu_contact_closed",
        name="PSU contact closed",
        value_fn=_bool_value("psuContactClosed"),
        icon_on="mdi:power-plug",
        icon_off="mdi:power-plug-off",
        entity_category=EntityCategory.DIAGNOSTIC,
        enabled_by_default=False,
    ),
    PaxtonStatusDescription(
        key="intruder_alarm_armed",
        name="Intruder alarm armed",
        value_fn=_bool_value("intruderAlarmArmed"),
        icon_on="mdi:shield-lock",
        icon_off="mdi:shield-off",
        entity_category=EntityCategory.DIAGNOSTIC,
        enabled_by_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PaxtonNet2ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    known: set[tuple[str, str]] = set()

    def add_new() -> None:
        entities: list[PaxtonNet2BinarySensor] = []
        for door_id in coordinator.data:
            for description in DESCRIPTIONS:
                key = (door_id, description.key)
                if key not in known:
                    known.add(key)
                    entities.append(
                        PaxtonNet2BinarySensor(
                            entry, coordinator, door_id, description
                        )
                    )
        if entities:
            async_add_entities(entities)

    add_new()
    entry.async_on_unload(coordinator.async_add_listener(add_new))


class PaxtonNet2BinarySensor(
    CoordinatorEntity[PaxtonNet2Coordinator], BinarySensorEntity
):
    _attr_has_entity_name = True

    def __init__(
        self,
        entry: PaxtonNet2ConfigEntry,
        coordinator: PaxtonNet2Coordinator,
        door_id: str,
        description: PaxtonStatusDescription,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._door_id = door_id
        self._description = description
        self._attr_unique_id = f"{entry.entry_id}_{door_id}_{description.key}"
        self._attr_name = description.name
        self._attr_device_class = description.device_class
        self._attr_entity_category = description.entity_category
        self._attr_entity_registry_enabled_default = description.enabled_by_default

    @property
    def _door(self) -> dict[str, Any]:
        return self.coordinator.data.get(self._door_id, {})

    @property
    def is_on(self) -> bool | None:
        return self._description.value_fn(self._door)

    @property
    def icon(self) -> str | None:
        if self.is_on is True:
            return self._description.icon_on
        if self.is_on is False:
            return self._description.icon_off
        return self._description.icon_off or self._description.icon_on

    @property
    def available(self) -> bool:
        return super().available and bool(self._door) and self.is_on is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"door_id": self._door_id}

    @property
    def device_info(self) -> dict[str, Any]:
        api = self.coordinator.api
        door_name = api.get_door_name(self._door) or f"Door {self._door_id}"
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._door_id}")},
            "name": door_name,
            "manufacturer": "Paxton",
            "model": "Net2 door",
        }
