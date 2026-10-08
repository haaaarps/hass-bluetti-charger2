"""Config flow for the Bluetti Charger 2 control integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import async_discovered_service_info
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import DOMAIN, NAME_PREFIX


class Charger2ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Pick the charger by Bluetooth address."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            address = user_input[CONF_ADDRESS].upper()
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title="Charger 2 control", data={CONF_ADDRESS: address}
            )
        found = [
            info.address
            for info in async_discovered_service_info(self.hass, connectable=True)
            if (info.name or "").upper().startswith(NAME_PREFIX)
        ]
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_ADDRESS, default=found[0] if found else vol.UNDEFINED): str}
            ),
        )
