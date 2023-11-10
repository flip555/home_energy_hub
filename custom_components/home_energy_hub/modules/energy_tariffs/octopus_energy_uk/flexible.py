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

_LOGGER = logging.getLogger(__name__)

async def OctopusEnergyUKFlexible(hass, entry):
    region = entry.data.get("current_region")
    api_update_time = entry.data.get("octopus_api_update_frequency")
    ha_update_time = entry.data.get("sensor_update_frequency")
    name_tariff = "None"
    options_flow = entry.data.get("options_flow")
    _LOGGER.debug("region: %s", region)
    _LOGGER.debug("options_flow: %s", options_flow)
    entry_id = entry.entry_id 
    _LOGGER.error("entry_id %s", entry_id)

    async def async_update_external_data():
        url = f"https://api.octopus.energy/v1/products/VAR-22-11-01/electricity-tariffs/E-1R-VAR-22-11-01-{region}/standard-unit-rates/"
        async with aiohttp.ClientSession() as session, session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                current_time = datetime.utcnow().timestamp()                
                hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA_UPDATE_TIME_" + entry_id] = current_time
                hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA"+entry_id] = data

                return data
            else:
                _LOGGER.error("Failed to get data from Octopus Energy API, status: %s", resp.status)
                return None

    async def async_update_data():
        # Check if the timestamp is set
        if "HOME_ENERGY_HUB_OCTOPUS_DATA_UPDATE_TIME_"+entry_id in hass.data[DOMAIN]:
            last_update_unix = hass.data[DOMAIN].get("HOME_ENERGY_HUB_OCTOPUS_DATA_UPDATE_TIME_" + entry_id)
            last_update_time = datetime.utcfromtimestamp(last_update_unix)
            current_time = datetime.utcnow()

            if last_update_time > current_time - timedelta(seconds=api_update_time):
                # Use existing data
                data = hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA"+entry_id]
            else:
                # Fetch new data
                data = await async_update_external_data()
        else:
            # If the timestamp isn't set, fetch new data
            data = await async_update_external_data()

        for item in data.get("results", []):
            time = item.get("valid_from") 
            price = item.get("value_inc_vat") 
            payment_method = item.get("payment_method") 
            if payment_method == "DIRECT_DEBIT":
                dd_current = price
            else:
                nondd_current = price
        return { 
                'binary_sensors': {},
                'sensors': {
                    'flexible_dd_current': {
                        'state': dd_current,
                        'name': f"Octopus Flexible DD - Region {region} - Current Price",
                        'unique_id': f"Octopus Flexible DD - Region {region} - Current Price",
                        'unit': "p",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    },
                    'flexible_dd_current_gbp': {
                        'state': dd_current / 100,
                        'name': f"Octopus Flexible DD - Region {region} - Current GBP Price",
                        'unique_id': f"Octopus Flexible DD - Region {region} - Current GBP Price",
                        'unit': "GBP/kWh",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    },
                    'flexible_nondd_current': {
                        'state': nondd_current,
                        'name': f"Octopus Flexible NONDD - Region {region} - Current Price",
                        'unique_id': f"Octopus Flexible NONDD - Region {region} - Current Price",
                        'unit': "p",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    },
                    'flexible_nondd_current_gbp': {
                        'state': nondd_current / 100,
                        'name': f"Octopus Flexible NONDD - Region {region} - Current GBP Price",
                        'unique_id': f"Octopus Flexible NONDD - Region {region} - Current GBP Price",
                        'unit': "GBP/kWh",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    },
                },
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