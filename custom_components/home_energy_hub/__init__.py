from __future__ import annotations
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from .const import DOMAIN, PLATFORMS
import voluptuous as vol
from .modules.global_settings import HomeEnergyHubGlobalSettings
from .modules.bms.seplos.v2 import SeplosV2BMS
from .modules.energy_tariffs.octopus_energy_uk.agile import OctopusEnergyUKAgile
from .modules.energy_tariffs.octopus_energy_uk.flexible import OctopusEnergyUKFlexible
from .modules.energy_tariffs.octopus_energy_uk.tracker import OctopusEnergyUKTracker
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
        elif config_data.get("home_energy_hub_registry") in ["20101"]:
            _LOGGER.debug("Octopus Agile Tariff Region %s Selected..", entry.data.get("current_region"))
            await OctopusEnergyUKAgile(hass, entry)
        elif config_data.get("home_energy_hub_registry") in ["20103"]:
            _LOGGER.debug("Octopus Tracker Tariff Region %s Selected..", entry.data.get("current_region"))
            await OctopusEnergyUKTracker(hass, entry)
        elif config_data.get("home_energy_hub_registry") in ["20102"]:
            _LOGGER.debug("Octopus Flexible Tariff Region %s Selected..", entry.data.get("current_region"))
            await OctopusEnergyUKFlexible(hass, entry)
        elif config_data.get("home_energy_hub_registry") in ["30101"]:
            _LOGGER.debug("Seplos V2 BMS Selected..")
            await SeplosV2BMS(hass, entry)
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

