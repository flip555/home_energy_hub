"""Data coordinator for Seplos V2."""

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from ...connectors import create_connector_client
from .modbus_processor import parse_seplos_response
from ...const import CONF_INTEGRATION_TYPE

_LOGGER = logging.getLogger(__name__)

class SeplosV2Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Seplos V2."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._client = None
        self.config_entry = entry
        self._integration_type = entry.data[CONF_INTEGRATION_TYPE]
        super().__init__(
            hass, _LOGGER, name="Seplos V2", update_interval=timedelta(seconds=entry.data.get("poll_interval", 30))
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data via Seplos V2 protocol."""
        try:
            self._client = await create_connector_client(
                self.hass, self.config_entry.data, self._integration_type
            )
            
            # Use Seplos V2 protocol to read data
            if hasattr(self._client, 'read_seplos_data'):
                data = await self._client.read_seplos_data(self.config_entry.data)
                if not data:
                    _LOGGER.warning("No data received from Seplos V2 device")
                    return {}
                    
                processed = parse_seplos_response(data, self.config_entry.data)
                await self._client.close()
                return processed
            else:
                # Fallback for other connector types (if any)
                raise UpdateFailed("Seplos V2 protocol not supported by connector")
                
        except Exception as err:
            if self._client:
                await self._client.close()
            _LOGGER.error("Seplos V2 update failed: %s", err)
            raise UpdateFailed(f"Seplos V2 update failed: {err}")