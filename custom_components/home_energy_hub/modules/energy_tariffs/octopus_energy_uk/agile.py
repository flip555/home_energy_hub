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

async def OctopusUKEnergyUKINIT(hass, entry):
    region = entry.data.get("current_region")
    name_tariff = "None"
    options_flow = entry.data.get("options_flow")
    _LOGGER.debug("region: %s", region)
    _LOGGER.debug("options_flow: %s", options_flow)

    async def async_update_data():
        time_price_list = []  # Initialize an empty list to store times and prices
        if "agile" in options_flow:
            url = f"https://api.octopus.energy/v1/products/AGILE-FLEX-22-11-25/electricity-tariffs/E-1R-AGILE-FLEX-22-11-25-{region}/standard-unit-rates/?page_size=100"
            name_tariff = "Agile"
            async with aiohttp.ClientSession() as session, session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()

                    time_price_list = []
                    future_negative_prices = []
                    now = datetime.now(timezone.utc)
                    cutoff_time = now - timedelta(hours=24)
                    
                    for item in data.get("results", []):
                        time = item.get("valid_from")  # Extract the 'valid_from' time
                        price = item.get("value_inc_vat")  # Extract the 'value_inc_vat' price

                        time_as_datetime = datetime.fromisoformat(time)

                        if time_as_datetime > cutoff_time:  # Remove prices older than 24 hours
                            if time is not None and price is not None:
                                time_price_list.append((time, price))

                                if time_as_datetime > now and price < 0:  # Include future prices that are negative
                                    future_negative_prices.append((time, price))
                    
                    time_price_list.sort()
                    current_price = next_price = previous_price = None

                    for i, (time, price) in enumerate(time_price_list):
                        time_as_datetime = datetime.fromisoformat(time)

                        if time_as_datetime > now:
                            next_price = price
                            break  # exit the loop as we've found the next price
                        
                        previous_price = current_price  # store the last "current" price as "previous" before updating "current"
                        current_price = price  # update the "current" price

                    timestamps = [x[0] for x in time_price_list]
                    prices = [x[1] for x in time_price_list]

                    plunge_timestamps = [x[0] for x in future_negative_prices]
                    plunge_prices = [x[1] for x in future_negative_prices]

                    return { 
                            'binary_sensors': {
                                'agile_current': {
                                    'state': True,
                                    'name': f"Octopusss Agile - Region {region} - Test",
                                    'unique_id': f"Ocstopus Agile - Region {region} - Test",
                                    'icon': "",
                                    'device_class': "",
                                    'attributes': {},
                                },
                            },
                            'sensors': {
                                'agile_current': {
                                    'state': current_price,
                                    'name': f"Octopus Agile - Region {region} - Current Price",
                                    'unique_id': f"Octopus Agile - Region {region} - Current Price",
                                    'unit': "p",
                                    'icon': "",
                                    'device_class': "",
                                    'state_class': "",
                                    'attributes': {},
                                },
                                'agile_current_gbp': {
                                    'state': current_price / 100,
                                    'name': f"Octopus Agile - Region {region} - Current GBP Price",
                                    'unique_id': f"Octopus Agile - Region {region} - Current GBP Price",
                                    'unit': "GBP/kWh",
                                    'icon': "",
                                    'device_class': "",
                                    'state_class': "",
                                    'attributes': {},
                                },
                                'agile_previous': {
                                    'state': previous_price,
                                    'name': f"Octopus Agile - Region {region} - Previous Price",
                                    'unique_id': f"Octopus Agile - Region {region} - Previous Price",
                                    'unit': "p",
                                    'icon': "",
                                    'device_class': "",
                                    'state_class': "",
                                    'attributes': {},
                                },
                                'agile_full_json': {
                                    'state': current_price,
                                    'name': f"Octopus Agile - Region {region} - JSON",
                                    'unique_id': f"Octopus Agile - Region {region} - JSON",
                                    'unit': "p",
                                    'icon': "",
                                    'device_class': "",
                                    'state_class': "",
                                    'attributes': {
                                        'timestamps': timestamps,
                                        'prices': prices
                                    },
                                },
                            },
                        }

                else:
                    _LOGGER.error("Failed to get data from Octopus Energy API, status: %s", resp.status)
                    return None
        else:
            url = ""
            name_tariff = "Error"
        
    await async_update_data()
    entry_id = entry.entry_id 
    _LOGGER.error("entry_id %s", entry_id)

    hass.data[DOMAIN]["HOME_ENERGY_HUB_SENSOR_COORDINATOR"+entry_id] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="home_energy_hub",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),  # Define how often to fetch data
    )
    await hass.data[DOMAIN]["HOME_ENERGY_HUB_SENSOR_COORDINATOR"+entry_id].async_refresh() 