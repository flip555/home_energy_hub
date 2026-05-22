"""Seplos V3 integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import SeplosV3Coordinator
from ...const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Seplos V3 from a config entry."""
    import logging
    from homeassistant.helpers import device_registry as dr
    
    _LOGGER = logging.getLogger(__name__)
    _LOGGER.info("Setting up Seplos V3 integration for entry: %s", entry.entry_id)
    
    coordinator = SeplosV3Coordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    name_prefix = entry.data.get("name_prefix", "Seplos BMS V3")
    
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("home_energy_hub", f"seplos_v3_{entry.entry_id}")},
        manufacturer="Seplos",
        name=f"{name_prefix}",
        model="V3 BMS",
        sw_version="Unknown",
    )
    
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    
    _LOGGER.info("Seplos V3 integration setup complete")
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if await hass.config_entries.async_unload_platforms(entry, ["sensor"]):
        if entry.entry_id in hass.data.get(DOMAIN, {}):
            hass.data[DOMAIN].pop(entry.entry_id)
        return True
    return False
