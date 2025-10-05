"""Binary sensor platform for Seplos V2."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ...const import DOMAIN
from .binary_sensor import SeplosV2BinarySensor


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Seplos V2 binary sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Wait for initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Filter binary sensor keys
    binary_sensor_keys = [key for key in coordinator.data.keys() if key.startswith('balancerActiveCell')]
    
    # Create binary sensor entities
    entities = [SeplosV2BinarySensor(coordinator, key, entry) for key in binary_sensor_keys]
    async_add_entities(entities)