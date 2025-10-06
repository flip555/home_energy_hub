"""Connector factory for transport abstraction."""

import logging
from typing import Any, Dict

from homeassistant.core import HomeAssistant

from ..const import CONF_CONNECTOR_TYPE
from . import usb_serial, telnet_serial

_LOGGER = logging.getLogger(__name__)

CONNECTOR_MODULES = {
    "usb_serial": usb_serial,
    "telnet_serial": telnet_serial,
}

async def create_connector_client(
    hass: HomeAssistant, config: Dict[str, Any], integration_type: str
) -> Any:
    """Factory: Create client based on connector_type."""
    connector_type = config[CONF_CONNECTOR_TYPE]
    module = CONNECTOR_MODULES.get(connector_type)

    if not module:
        raise ValueError(f"Unknown connector: {connector_type}")

    return await module.create_client(hass, config, integration_type)