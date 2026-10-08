"""One short encrypted Bluetooth session with the charger."""

from __future__ import annotations

import asyncio
import logging

from bleak.exc import BleakError
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from bluetti_bt_lib.base_devices import BaseDeviceV2
from bluetti_bt_lib.devices.charger2 import CHARGER2
from bluetti_bt_lib.bluetooth.device_reader import DeviceReader, DeviceReaderConfig
from bluetti_bt_lib.registers import ReadableRegisters, WriteableRegister

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import (
    CONNECT_ATTEMPTS,
    CONNECT_RETRY_SECONDS,
    HANDSHAKE_SECONDS,
    NOTIFY_UUID,
    READ_BLOCKS,
    REG_FLAGS,
)

_LOGGER = logging.getLogger(__name__)


class ChargerBusy(HomeAssistantError):
    """The charger could not be reached (usually another connection holds it)."""


async def async_session(
    hass: HomeAssistant, address: str, write_word: int | None = None
) -> dict:
    """Read the charger, optionally writing the flags word first.

    Returns the decoded readings plus ``flags`` (the raw settings word). This
    integration must be the only one talking to the charger: two encrypted
    sessions on its single connection corrupt each other.
    A write is sent exactly once and is never retried here.
    """
    client = None
    last_error: Exception | None = None
    for attempt in range(CONNECT_ATTEMPTS):
        ble_device = bluetooth.async_ble_device_from_address(hass, address, connectable=True)
        if ble_device is not None:
            try:
                client = await establish_connection(
                    BleakClientWithServiceCache, ble_device, "Charger 2", max_attempts=2
                )
                break
            except (BleakError, TimeoutError) as err:
                last_error = err
        await asyncio.sleep(CONNECT_RETRY_SECONDS)
    if client is None:
        raise ChargerBusy(
            "Could not connect to the Charger 2. Is the Bluetti app open on a phone nearby?"
            + (f" ({last_error})" if last_error else "")
        )

    reader = DeviceReader(
        address,
        BaseDeviceV2(),
        hass.loop.create_future,
        DeviceReaderConfig(timeout=60, use_encryption=True),
        asyncio.Lock(),
        ble_client=client,
    )
    reader.client = client  # the handshake answers through this
    try:
        await client.start_notify(NOTIFY_UUID, reader._notification_handler)  # noqa: SLF001
        for _ in range(HANDSHAKE_SECONDS * 2):
            if reader.encryption.is_ready_for_commands:
                break
            await asyncio.sleep(0.5)
        else:
            raise ChargerBusy("The Charger 2 did not complete the encrypted handshake")

        charger = CHARGER2()

        async def read_all() -> dict:
            data: dict = {}
            for start, words in READ_BLOCKS:
                request = ReadableRegisters(start, words)
                body = request.parse_response(
                    await reader._async_send_command(request)  # noqa: SLF001
                )
                if len(body) < words * 2:
                    raise ChargerBusy("The Charger 2 did not answer the read")
                data.update(charger.parse(start, body))
                if start <= REG_FLAGS < start + words:
                    offset = (REG_FLAGS - start) * 2
                    data["flags"] = int.from_bytes(body[offset : offset + 2], "big")
            return data

        if write_word is not None:
            command = WriteableRegister(REG_FLAGS, write_word)
            response = await reader._async_send_command(command)  # noqa: SLF001
            if response and command.is_exception_response(response):
                raise HomeAssistantError(
                    f"The Charger 2 rejected the command (code {response[2]:#04x})"
                )
            _LOGGER.debug("Charger 2 write %04X answered %s", write_word, bytes(response).hex())
            await asyncio.sleep(2)
        return await read_all()
    except (BleakError, TimeoutError) as err:
        raise ChargerBusy(f"Lost the connection to the Charger 2: {err}") from err
    finally:
        try:
            await client.stop_notify(NOTIFY_UUID)
        except Exception:  # noqa: BLE001
            pass
        try:
            await client.disconnect()
        except Exception:  # noqa: BLE001
            pass
