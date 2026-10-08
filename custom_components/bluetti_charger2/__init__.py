"""Bluetti Charger 2 over Bluetooth: readings and a charging switch."""

from __future__ import annotations

import asyncio
from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, FOLLOW_UP_SECONDS, POLL_SECONDS, WORD_OFF, WORD_ON
from .link import ChargerBusy, async_session

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.SWITCH]

type Charger2ConfigEntry = ConfigEntry[Charger2Coordinator]


class Charger2Coordinator(DataUpdateCoordinator[dict]):
    """Holds the charger's last readings, including ``flags``."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=POLL_SECONDS),
        )
        self.address: str = entry.data[CONF_ADDRESS]
        self._lock = asyncio.Lock()
        self._missed = 0

    async def _async_update_data(self) -> dict:
        try:
            async with self._lock:
                data = await async_session(self.hass, self.address)
        except ChargerBusy as err:
            # The phone app can hold the charger's single connection; keep the
            # last readings through a few misses.
            self._missed += 1
            if self.data is not None and self._missed <= 3:
                return self.data
            raise UpdateFailed(str(err)) from err
        self._missed = 0
        return data

    @callback
    def _async_follow_up(self, _now) -> None:
        self.hass.async_create_task(self.async_request_refresh())

    async def async_set_charging(self, on: bool) -> None:
        """Switch charging by writing the flags word once."""
        async with self._lock:
            current = (await async_session(self.hass, self.address))["flags"]
            target = WORD_ON if on else WORD_OFF
            if current == target:
                return
            if current not in (WORD_ON, WORD_OFF):
                raise HomeAssistantError(
                    f"The Charger 2 is in a state this switch does not handle yet "
                    f"({current:04X}; silent mode?). Use the Bluetti app."
                )
            result = await async_session(self.hass, self.address, write_word=target)
        self._missed = 0
        self.async_set_updated_data(result)
        for delay in FOLLOW_UP_SECONDS:
            self.config_entry.async_on_unload(
                async_call_later(self.hass, delay, self._async_follow_up)
            )
        if result["flags"] != target:
            raise HomeAssistantError(
                f"The Charger 2 did not change state (reads {result['flags']:04X})"
            )


async def async_setup_entry(hass: HomeAssistant, entry: Charger2ConfigEntry) -> bool:
    """Set up the charger control."""
    coordinator = Charger2Coordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: Charger2ConfigEntry) -> bool:
    """Unload the charger control."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
