"""Seplos V2 integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import SeplosV2Coordinator
from ...const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Seplos V2 from a config entry."""
    import logging
    from homeassistant.helpers import device_registry as dr
    
    _LOGGER = logging.getLogger(__name__)
    _LOGGER.info("Setting up Seplos V2 integration for entry: %s", entry.entry_id)
    
    # Create coordinator
    coordinator = SeplosV2Coordinator(hass, entry)
    
    # Perform initial data refresh to ensure we have data before setting up entities
    await coordinator.async_config_entry_first_refresh()
    
    # Store coordinator in hass.data
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Get configuration for device names
    name_prefix = entry.data.get("name_prefix", "Seplos BMS HA")
    battery_address = entry.data.get("battery_address", "0x00")
    
    # Register devices in device registry (like GEO IHD does)
    device_registry = dr.async_get(hass)
    
    # Create BMS device
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("home_energy_hub", f"seplos_v2_{entry.entry_id}_{battery_address}")},
        manufacturer="Seplos",
        name=f"{name_prefix} {battery_address} BMS",
        model="V2 BMS",
        sw_version=coordinator.data.get("software_version", "Unknown"),
    )
    
    # Create Settings device
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("home_energy_hub", f"seplos_v2_{entry.entry_id}_{battery_address}_settings")},
        manufacturer="Seplos",
        name=f"{name_prefix} {battery_address} Settings",
        model="V2 Settings",
        sw_version=coordinator.data.get("software_version", "Unknown"),
    )
    
    # Set up sensors and binary sensors
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "binary_sensor"])
    
    _LOGGER.info("Seplos V2 integration setup complete - created BMS and Settings devices")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if await hass.config_entries.async_unload_platforms(entry, ["sensor", "binary_sensor"]):
        hass.data[DOMAIN].pop(entry.entry_id)
        return True
    return False