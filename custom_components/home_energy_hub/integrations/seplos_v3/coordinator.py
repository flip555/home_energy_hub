"""Data coordinator for Seplos V3 Modbus RTU."""

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ...const import CONF_CONNECTOR_TYPE, CONF_HOST, CONF_PORT, CONF_SERIAL_PORT, CONF_BAUD_RATE
from .data_parser import build_commands_for_address, extract_data_from_message

_LOGGER = logging.getLogger(__name__)


class SeplosV3Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Seplos V3 Modbus RTU.

    Uses the dedicated V3 Modbus RTU transport (seplos_v3_serial) instead
    of the V2 ASCII-based connector clients.
    """

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.config_entry = entry
        self._connector_type = entry.data.get(CONF_CONNECTOR_TYPE, "usb_serial")
        super().__init__(
            hass, _LOGGER, name="Seplos V3",
            update_interval=timedelta(seconds=entry.data.get("poll_interval", 30))
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data via Seplos V3 Modbus RTU protocol."""
        try:
            battery_addr = int(self.config_entry.data.get("battery_address", "0x01"), 0)
            commands = build_commands_for_address(battery_addr)
            _LOGGER.debug("V3 commands: %s", commands)

            if self._connector_type == "telnet_serial":
                data = await self._send_telnet(commands)
            elif self._connector_type == "usb_serial":
                data = await self._send_serial(commands)
            else:
                raise UpdateFailed(f"Unsupported connector: {self._connector_type}")

            if not data or len(data) < 2:
                _LOGGER.warning("Insufficient V3 data received")
                return {}

            processed = extract_data_from_message(data)
            _LOGGER.debug("V3 data keys: %s", list(processed.keys()))
            return processed

        except Exception as err:
            _LOGGER.error("Seplos V3 update failed: %s", err)
            raise UpdateFailed(f"Seplos V3 update failed: {err}")

    async def _send_serial(self, commands: list[str]) -> list[str]:
        """Send commands via USB-RS485 serial."""
        from ...connectors.seplos_v3_serial import send_serial_commands_async

        port = self.config_entry.data.get(CONF_SERIAL_PORT, "/dev/ttyUSB0")
        baudrate = self.config_entry.data.get(CONF_BAUD_RATE, 19200)
        return await send_serial_commands_async(commands, port=port, baudrate=baudrate)

    async def _send_telnet(self, commands: list[str]) -> list[str]:
        """Send commands via Telnet serial bridge."""
        from ...connectors.seplos_v3_serial import send_telnet_commands_async

        host = self.config_entry.data[CONF_HOST]
        port = self.config_entry.data.get(CONF_PORT, 23)
        return await send_telnet_commands_async(commands, host=host, port=port)
