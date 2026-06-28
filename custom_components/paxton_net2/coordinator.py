from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PaxtonNet2Api, PaxtonNet2ApiError, PaxtonNet2AuthenticationError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class PaxtonNet2Coordinator(DataUpdateCoordinator[dict[str, dict]]):
    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: PaxtonNet2Api,
        poll_interval: int,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=timedelta(seconds=max(10, poll_interval)),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, dict]:
        try:
            doors = await self.api.async_get_combined_doors()
        except PaxtonNet2AuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except PaxtonNet2ApiError as err:
            raise UpdateFailed(str(err)) from err
        return {
            str(self.api.get_door_id(door)): door
            for door in doors
            if self.api.get_door_id(door) is not None
        }
