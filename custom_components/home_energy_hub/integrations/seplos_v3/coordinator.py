"""Data coordinator for Seplos V3."""

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ...connectors import create_connector_client
from .data_parser import build_commands_for_address, extract_data_from_message
from ...const import CONF_INTEGRATION_TYPE

_LOGGER = logging.getLogger(__name__)


class SeplosV3Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Seplos V3 Modbus RTU."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._client = None
        self.config_entry = entry
        self._integration_type = entry.data[CONF_INTEGRATION_TYPE]
        super().__init__(
            hass, _LOGGER, name="Seplos V3",
            update_interval=timedelta(seconds=entry.data.get("poll_interval", 30))
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data via Seplos V3 Modbus RTU protocol."""
        try:
            self._client = await create_connector_client(
                self.hass, self.config_entry.data, self._integration_type
            )

            if not hasattr(self._client, 'send_serial_commands'):
                raise UpdateFailed("Connector does not support sending raw commands")

            # Build V3 Modbus RTU commands (PIA + PIB)
            battery_addr = int(self.config_entry.data.get("battery_address", "0x01"), 0)
            commands = build_commands_for_address(battery_addr)
            _LOGGER.debug("Sending V3 commands: %s", commands)

            try:
                data = await self._client.send_serial_commands(commands)
            except Exception:
                # Fallback: try collect_all mode
                if hasattr(self._client, 'send_serial_commands'):
                    data = await self._client.send_serial_commands(commands)
                else:
                    raise

            await self._client.close()

            if not data or len(data) < 2:
                _LOGGER.warning("Insufficient V3 data received")
                return {}

            processed = extract_data_from_message(data)
            _LOGGER.debug("V3 data: %s", {k: v for k, v in processed.items() if not isinstance(v, (list, dict))})
            return processed

        except Exception as err:
            if self._client:
                try:
                    await self._client.close()
                except Exception:
                    pass
            _LOGGER.error("Seplos V3 update failed: %s", err)
            raise UpdateFailed(f"Seplos V3 update failed: {err}")
