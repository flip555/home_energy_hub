import asyncio
import logging
from datetime import timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant import config_entries  # Add this import
from .const import (
    NAME,
    DOMAIN,
    VERSION,
    ATTRIBUTION,
)
# ---------------------------------------------
# ------------- CONFIG IMPORTS START ----------
# ---------------------------------------------
# Add your module imports here. 
# If you're adding a new module, import it in this section.
from .modules.global_settings import HomeEnergyHubGlobalSettings
from .modules.energy_tariffs.octopus_energy_uk.init import OctopusUKEnergyUKINIT
# Example: 
# from .config_flows.category.file import YourMethodName
# ---------------------------------------------
# ---------------------------------------------

_LOGGER = logging.getLogger(__name__)
coordinator = None  # Define coordinator at a higher scope

async def HomeEnergyHubINIT(hass, config_entry):
    pass

async def async_setup_entry(hass: HomeAssistantType, config_entry: config_entries.ConfigEntry, async_add_entities: AddEntitiesCallback):
    try:

        # Check the disclaimer value and proceed accordingly
        if config_entry.data.get("home_enery_hub_first_run") == 1:
            _LOGGER.debug("Home Energy Hub Global Settings Loading...")
            await HomeEnergyHubGlobalSettings(hass, "C", config_entry.data, async_add_entities)

        elif config_entry.data.get("home_energy_hub_registry") in ["20101","20102","20103"]:
            _LOGGER.debug("Octopus Tariffs Selected, Routing Now.. Region: %s", config_entry.data.get("current_region"))
            await OctopusUKEnergyUKINIT(hass, config_entry.data.get("current_region"), config_entry.data, async_add_entities)
        else:
            _LOGGER.error("Error Setting up Entry")

    except Exception as e:
        _LOGGER.error("Error setting up Home Energy Hub: %s", e)
