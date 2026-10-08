"""Readings from the Bluetti Charger 2."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import Charger2ConfigEntry, Charger2Coordinator
from .const import DOMAIN

_V = (SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT)
_A = (SensorDeviceClass.CURRENT, UnitOfElectricCurrent.AMPERE)
_W = (SensorDeviceClass.POWER, UnitOfPower.WATT)


@dataclass(frozen=True, kw_only=True)
class Charger2SensorDescription(SensorEntityDescription):
    """``field`` is the library's field name; the charger reports output as negative."""

    field: str
    absolute: bool = False


def _desc(key: str, field: str, kind: tuple, absolute: bool = False) -> Charger2SensorDescription:
    return Charger2SensorDescription(
        key=key,
        translation_key=key,
        field=field,
        absolute=absolute,
        device_class=kind[0],
        native_unit_of_measurement=kind[1],
        state_class=SensorStateClass.MEASUREMENT,
    )


SENSORS = (
    _desc("starter_voltage", "b_alt_v", _V),
    _desc("alternator_current", "b_alt_c", _A),
    _desc("alternator_power", "b_alt_io_p", _W),
    _desc("dc_input_voltage", "dc_input_voltage", _V),
    _desc("dc_input_current", "dc_input_current", _A),
    _desc("dc_input_power", "dc_input_power", _W),
    _desc("output_voltage", "dc_2_o_v", _V),
    _desc("output_current", "dc_2_o_c", _A, absolute=True),
    _desc("output_power", "dc_2_o_p_total", _W, absolute=True),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Charger2ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities(Charger2Sensor(entry.runtime_data, d) for d in SENSORS)


class Charger2Sensor(CoordinatorEntity[Charger2Coordinator], SensorEntity):
    """One reading."""

    _attr_has_entity_name = True
    entity_description: Charger2SensorDescription

    def __init__(self, coordinator: Charger2Coordinator, description: Charger2SensorDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.address)},
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            name="Charger 2",
            manufacturer="Bluetti",
            model="Charger 2",
        )

    @property
    def native_value(self) -> float | None:
        value = (self.coordinator.data or {}).get(self.entity_description.field)
        if value is None:
            return None
        value = float(value)
        return abs(value) if self.entity_description.absolute else value
