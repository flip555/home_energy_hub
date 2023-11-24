from __future__ import annotations
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er, config_validation as cv

from .const import DOMAIN, PLATFORMS
import voluptuous as vol
from .modules.global_settings import HomeEnergyHubGlobalSettings
from .modules.bms.seplos.v2old import SeplosV2BMS
from .modules.bms.seplos.v2 import SeplosV2BMSDevice
from .modules.energy_tariffs.octopus_energy_uk.agile import OctopusEnergyUKAgile
from .modules.energy_tariffs.octopus_energy_uk.flexible import OctopusEnergyUKFlexible
from .modules.energy_tariffs.octopus_energy_uk.tracker import OctopusEnergyUKTracker
from .modules.energy_tariffs.octopus_energy_uk.account_data import OctopusEnergyUKAccountData
from .modules.energy_tariffs.octopus_energy_uk.tariff_engine_agile import OctopusEnergyUKTariffEngineAgile
from .modules.energy_tariffs.octopus_energy_uk.tariff_engine_tracker import OctopusEnergyUKTariffEngineTracker
from .modules.energy_tariffs.octopus_energy_uk.tariff_engine_flexible import OctopusEnergyUKTariffEngineFlexible
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
            #await OctopusEnergyUKAgile(hass, entry)
            await OctopusEnergyUKTariffEngineAgile(hass, entry)

        elif config_data.get("home_energy_hub_registry") in ["20103"]:
            _LOGGER.debug("Octopus Tracker Tariff Region %s Selected..", entry.data.get("current_region"))
            await OctopusEnergyUKTracker(hass, entry)
        elif config_data.get("home_energy_hub_registry") in ["20102"]:
            _LOGGER.debug("Octopus Flexible Tariff Region %s Selected..", entry.data.get("current_region"))
            await OctopusEnergyUKFlexible(hass, entry)
        elif config_data.get("home_energy_hub_registry") in ["20190"]:
            _LOGGER.debug("Octopus Account Data Selected.. %s", entry.data.get("api_key"))
            await OctopusEnergyUKAccountData(hass, entry)
        elif config_data.get("home_energy_hub_registry") in ["20191"]:
            for region in entry.data.get("current_region"):
                _LOGGER.debug("Octopus Tariff Engine.. %s", region)
            await OctopusEnergyUKTariffEngineAgile(hass, entry)
        elif config_data.get("home_energy_hub_registry") in ["20192"]:
            for region in entry.data.get("current_region"):
                _LOGGER.debug("Octopus Tariff Engine.. %s", region)
            await OctopusEnergyUKTariffEngineTracker(hass, entry)
        elif config_data.get("home_energy_hub_registry") in ["20193"]:
            for region in entry.data.get("current_region"):
                _LOGGER.debug("Octopus Tariff Engine.. %s", region)
            await OctopusEnergyUKTariffEngineFlexible(hass, entry)
        elif config_data.get("home_energy_hub_registry") in ["30101"]:
            _LOGGER.debug("Seplos V2 BMS Selected..")
            await SeplosV2BMS(hass, entry)
        elif config_data.get("home_energy_hub_registry") in ["30110"]:
            _LOGGER.debug("Seplos V2 BMS Device Selected..")
            await SeplosV2BMSDevice(hass, entry)
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
    if entry.data.get("home_energy_hub_registry") in ["20191"] or entry.data.get("home_energy_hub_registry") in ["20101"]:
        tariff_name = "Agile"
        old_regions = set(hass.data[DOMAIN][entry.entry_id].get("current_region", []))
        new_regions = set(entry.data.get("current_region", []))

        # Identify removed regions
        removed_regions = old_regions - new_regions

        # Remove entities for each removed region
        for region in removed_regions:
            for regione in region:

            # Find and remove entities associated with the region
                await remove_device_and_entities_for_region(hass, entry, regione, tariff_name)

        # Unload and setup entry again
        await async_unload_entry(hass, entry)
        await async_setup_entry(hass, entry)

        # Update stored data with the new configuration
        hass.data[DOMAIN][entry.entry_id] = entry.data
    elif entry.data.get("home_energy_hub_registry") in ["20192"]:
        tariff_name = "Tracker"
        old_regions = set(hass.data[DOMAIN][entry.entry_id].get("current_region", []))
        new_regions = set(entry.data.get("current_region", []))

        # Identify removed regions
        removed_regions = old_regions - new_regions

        # Remove entities for each removed region
        for region in removed_regions:
            for regione in region:

            # Find and remove entities associated with the region
                await remove_device_and_entities_for_region(hass, entry, regione, tariff_name)

        # Unload and setup entry again
        await async_unload_entry(hass, entry)
        await async_setup_entry(hass, entry)

        # Update stored data with the new configuration
        hass.data[DOMAIN][entry.entry_id] = entry.data
    elif entry.data.get("home_energy_hub_registry") in ["20193"]:
        tariff_name = "Flexible"
        old_regions = set(hass.data[DOMAIN][entry.entry_id].get("current_region", []))
        new_regions = set(entry.data.get("current_region", []))

        # Identify removed regions
        removed_regions = old_regions - new_regions

        # Remove entities for each removed region
        for region in removed_regions:
            for regione in region:

            # Find and remove entities associated with the region
                await remove_device_and_entities_for_region(hass, entry, regione, tariff_name)

        # Unload and setup entry again
        await async_unload_entry(hass, entry)
        await async_setup_entry(hass, entry)

        # Update stored data with the new configuration
        hass.data[DOMAIN][entry.entry_id] = entry.data
    else:
        await async_unload_entry(hass, entry)
        await async_setup_entry(hass, entry)

async def remove_device_and_entities_for_region(hass: HomeAssistant, entry: ConfigEntry, region: str, tariff_name: str):
    device_registry = dr.async_get(hass)
    entity_registry =  er.async_get(hass)

    target_device_name = f"{tariff_name} Region {region}"

    # Find the device by name
    target_device = next((device for device in device_registry.devices.values() if device.name == target_device_name), None)

    if target_device:
        # Remove the device
        device_registry.async_remove_device(target_device.id)

        # Find and remove all entities associated with this device
        associated_entities = [entity_id for entity_id, entity in entity_registry.entities.items() if entity.device_id == target_device.id]
        for entity_id in associated_entities:
            entity_registry.async_remove(entity_id)

