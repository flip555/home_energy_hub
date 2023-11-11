from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.components.binary_sensor import BinarySensorEntity

import aiohttp
import json
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from ....const import (
    NAME,
    DOMAIN,
    VERSION,
    ATTRIBUTION,
)
import requests

_LOGGER = logging.getLogger(__name__)

async def OctopusEnergyUKAccountData(hass, entry):
    entry_id = entry.entry_id 
    api_update_time = entry.data.get("octopus_api_update_frequency")
    name_prefix = entry.data.get("name_prefix") + " - "
    ha_update_time = entry.data.get("sensor_update_frequency")
    options_flow = entry.data.get("options_flow")
    APIKEY = entry.data.get("api_key")
    ACCOUNT_ID = entry.data.get("account_id")
    sensors = {}
    binary_sensors = {}

    async def async_update_data():
        url = f'https://api.octopus.energy/v1/accounts/{ACCOUNT_ID}/'
        async with aiohttp.ClientSession() as session, session.get(url, auth=aiohttp.BasicAuth(APIKEY, '')) as resp:
            if resp.status == 200:
                data = await resp.json()
                current_time = datetime.utcnow().timestamp()
                hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA" + entry_id] = data
                sensors["number"] = {
                    'state': data["number"],
                    'name': f"{name_prefix}Account Number",
                    'unique_id': f"{name_prefix}Account Number",
                    'unit': None,
                    'icon': "", 
                    'device_class': "",
                    'state_class': "",
                    'attributes': data,
                }

            else:
                _LOGGER.error("Failed to get data from Octopus Energy API, status: %s", resp.status)


        return { 
                'binary_sensors': binary_sensors,
                'sensors': sensors,
            }

    await async_update_data()

    hass.data[DOMAIN]["HOME_ENERGY_HUB_SENSOR_COORDINATOR"+entry_id] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="home_energy_hub_"+entry_id,
        update_method=async_update_data,
        update_interval=timedelta(seconds=ha_update_time),  # Define how often to fetch data
    )
    await hass.data[DOMAIN]["HOME_ENERGY_HUB_SENSOR_COORDINATOR"+entry_id].async_refresh() 