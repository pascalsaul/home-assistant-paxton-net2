from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
        entities: list[PaxtonNet2OpenOnceButton] = []
        excluded = entry.runtime_data.excluded_control_door_ids
        for door_id in coordinator.data:
            if door_id in excluded:
                known.add(door_id)
                continue
            if door_id not in known:
                known.add(door_id)
                entities.append(
                    PaxtonNet2OpenOnceButton(entry, coordinator, door_id)
                )
        if entities:
            async_add_entities(entities)

    add_new()
    entry.async_on_unload(coordinator.async_add_listener(add_new))


class PaxtonNet2OpenOnceButton(
    CoordinatorEntity[PaxtonNet2Coordinator], ButtonEntity
):
    """Momentarily open a door using its configured Net2 door logic."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:door-open"

    def __init__(
        self,
        entry: PaxtonNet2ConfigEntry,
        coordinator: PaxtonNet2Coordinator,
        door_id: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._door_id = door_id
        self._attr_unique_id = f"{entry.entry_id}_{door_id}_open_once"

    @property
    def _door(self):
        return self.coordinator.data.get(self._door_id, {})

    @property
    def _is_toggle_door(self) -> bool:
        return self._door_id in self._entry.runtime_data.toggle_door_ids

    @property
    def _relay_id(self) -> str:
        return "Relay2" if self._door_id in self._entry.runtime_data.relay2_door_ids else "Relay1"

    @property
    def name(self) -> str:
        return "Toggle access" if self._is_toggle_door else "Open once"

    @property
    def icon(self) -> str:
        if not self._is_toggle_door:
            return "mdi:door-open"
        return "mdi:lock" if self.coordinator.api.door_is_open(self._door) else "mdi:lock-open-variant"

    @property
    def available(self) -> bool:
        return super().available and bool(self._door)

    @property
    def device_info(self):
        api = self.coordinator.api
        name = api.get_door_name(self._door) or f"Door {self._door_id}"
        return {
            "identifiers": {(DOMAIN, f"{self._entry.entry_id}_{self._door_id}")},
            "name": name,
            "manufacturer": "Paxton",
            "model": "Net2 door",
        }

    async def async_press(self) -> None:
        try:
            if self._is_toggle_door:
                currently_open = self.coordinator.api.door_is_open(self._door)
                await self.coordinator.api.async_set_door(
                    self._door_id,
                    open_=currently_open is not True,
                )
            else:
                await self.coordinator.api.async_open_once(self._door_id)
            await self.coordinator.async_request_refresh()
        except PaxtonNet2ApiError as err:
            raise RuntimeError(
                f"Could not operate door {self._door_id}: {err}"
            ) from err
