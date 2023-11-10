from __future__ import annotations
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN, PLATFORMS
import voluptuous as vol
from .modules.global_settings import HomeEnergyHubGlobalSettings
from .modules.energy_tariffs.octopus_energy_uk.agile import OctopusUKEnergyUKINIT
import logging
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass, config):
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    
    # Use options if they exist, otherwise default to entry data
    config_data = entry.data
    hass.data[DOMAIN][entry.entry_id] = config_data
    # Logical Checks and coordinators should be set here!
    try:
        # Check the disclaimer value and proceed accordingly
        if config_data.get("home_enery_hub_first_run") == 1:
            _LOGGER.debug("Home Energy Hub Global Settings Loading...")
            await HomeEnergyHubGlobalSettings(hass, entry)
        elif config_data.get("home_energy_hub_registry") in ["20101","20102","20103"]:
            _LOGGER.debug("Octopus Tariffs Selected, Routing Now.. Region: %s", entry.data.get("current_region"))
            await OctopusUKEnergyUKINIT(hass, entry)
        else:
            _LOGGER.error("Error Setting up Entry")

    except Exception as e:
        _LOGGER.error("Error setting up Home Energy Hub: %s", e)

    #await HomeEnergyHubINIT(hass, entry)


    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unloaded := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

