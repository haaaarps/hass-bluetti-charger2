"""Charging switch."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import Charger2ConfigEntry, Charger2Coordinator
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Charger2ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([Charger2ChargingSwitch(entry.runtime_data)])


class Charger2ChargingSwitch(CoordinatorEntity[Charger2Coordinator], SwitchEntity):
    """Charging on/off, read from the low flag pair (01 = on, 10 = off)."""

    _attr_has_entity_name = True
    _attr_translation_key = "charging"
    _attr_icon = "mdi:car-battery"

    def __init__(self, coordinator: Charger2Coordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.address}_charging"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.address)},
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            name="Charger 2",
            manufacturer="Bluetti",
            model="Charger 2",
        )

    @property
    def is_on(self) -> bool | None:
        flags = (self.coordinator.data or {}).get("flags")
        return None if flags is None else (flags & 0b11) == 0b01

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        flags = (self.coordinator.data or {}).get("flags")
        if flags is None:
            return None
        return {
            "flags": f"{flags:04X}",
            "mode": {0b10: "standard", 0b01: "silent"}.get((flags >> 2) & 0b11, "unknown"),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_charging(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_charging(False)
