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

async def OctopusEnergyUKTracker(hass, entry):
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
        url = f"https://octopus.energy/api/v1/tracker/E-1R-SILVER-FLEX-22-11-25-{region}/daily/current/1/1/"
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

        # Get today's date
        today = datetime.now().date()

        # Calculate tomorrow's date
        tomorrow = today + timedelta(days=1)

        for item in data.get("periods"):
            item_date_str = item.get("date")  # This is a string in the format "YYYY-MM-DD"
            item_date = datetime.strptime(item_date_str, "%Y-%m-%d").date()  # Convert string to date

            price = item.get("unit_rate")

            if item_date == today:
                tracker_today = price
            elif item_date == tomorrow:
                tracker_tomorrow = price

        return { 
                'binary_sensors': {},
                'sensors': {
                    'tracker_today': {
                        'state': tracker_today,
                        'name': f"Octopus Tracker - Region {region} - Current Price",
                        'unique_id': f"Octopus Tracker - Region {region} - Current Price",
                        'unit': "p",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    },
                    'tracker_today_gbp': {
                        'state': tracker_today / 100,
                        'name': f"Octopus Tracker - Region {region} - Current GBP Price",
                        'unique_id': f"Octopus Tracker - Region {region} - Current GBP Price",
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