from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import PaxtonNet2ConfigEntry
from .api import PaxtonNet2ApiError
from .const import DOMAIN
from .coordinator import PaxtonNet2Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PaxtonNet2ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data.coordinator
    known: set[str] = set()

    def add_new() -> None:
        entities = []
        excluded = entry.runtime_data.excluded_control_door_ids
        for door_id in coordinator.data:
            if door_id in excluded:
                known.add(door_id)
                continue
            if door_id not in known:
                known.add(door_id)
                entities.append(PaxtonNet2DoorSwitch(entry, coordinator, door_id))
        if entities:
            async_add_entities(entities)

    add_new()
    entry.async_on_unload(coordinator.async_add_listener(add_new))


class PaxtonNet2DoorSwitch(CoordinatorEntity[PaxtonNet2Coordinator], SwitchEntity):
    _attr_has_entity_name = True
    _attr_name = "Hold open"
    
    def __init__(self, entry, coordinator, door_id: str) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._door_id = door_id
        self._attr_unique_id = f"{entry.entry_id}_{door_id}_held_open"

    @property
    def _door(self):
        return self.coordinator.data.get(self._door_id, {})

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.api.door_is_open(self._door)

    @property
    def available(self) -> bool:
        return super().available and bool(self._door)

    @property
    def icon(self) -> str:
        return "mdi:lock-open-variant" if self.is_on else "mdi:lock"

    @property
    def extra_state_attributes(self):
        attributes = {
            k: v for k, v in self._door.items()
            if not k.startswith("_")
            and (isinstance(v, (str, int, float, bool)) or v is None)
        }
        status_wrapper = self._door.get("_net2_status")
        if isinstance(status_wrapper, dict):
            status = status_wrapper.get("status") or status_wrapper.get("Status")
            if not isinstance(status, dict):
                status = status_wrapper
            for key, value in status.items():
                if isinstance(value, (str, int, float, bool)) or value is None:
                    attributes[key] = value
        return attributes

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._door_id}")},
            "name": self.name,
            "manufacturer": "Paxton",
            "model": "Net2 door",
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        try:
            await self.coordinator.api.async_set_door(self._door_id, True)
            await self.coordinator.async_request_refresh()
        except PaxtonNet2ApiError as err:
            raise RuntimeError(f"Could not hold open {self.name}: {err}") from err

    async def async_turn_off(self, **kwargs: Any) -> None:
        try:
            await self.coordinator.api.async_set_door(self._door_id, False)
            await self.coordinator.async_request_refresh()
        except PaxtonNet2ApiError as err:
            raise RuntimeError(f"Could not close {self.name}: {err}") from err
