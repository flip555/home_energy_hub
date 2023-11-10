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
    api_update_time = entry.data.get("octopus_api_update_frequency")
    ha_update_time = entry.data.get("sensor_update_frequency")
    name_tariff = "None"
    options_flow = entry.data.get("options_flow")
    _LOGGER.debug("region: %s", region)
    _LOGGER.debug("options_flow: %s", options_flow)
    entry_id = entry.entry_id 
    _LOGGER.error("entry_id %s", entry_id)

    async def async_update_external_data():
        url = f"https://api.octopus.energy/v1/products/AGILE-FLEX-22-11-25/electricity-tariffs/E-1R-AGILE-FLEX-22-11-25-{region}/standard-unit-rates/?page_size=100"
        async with aiohttp.ClientSession() as session, session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                _LOGGER.debug("Update received from Octopus Energy API")

                # Set the timestamp here after a successful fetch
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

        time_price_list = []  # Initialize an empty list to store times and prices
        if "agile" in options_flow:
            name_tariff = "Agile"
            #data = hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA"+entry_id].data
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
            if (plunge_prices and plunge_timestamps):
                plunge_state = True 
            else:
                plunge_state = False

            _LOGGER.debug("Updating HA Sensor based on Stored data")

            return { 
                    'binary_sensors': {
                        'agile_plunge_json': {
                            'state': plunge_state,
                            'name': f"Octopus Agile - Region {region} - Plunge Pricing",
                            'unique_id': f"Octopus Agile - Region {region} - Plunge Pricing",
                            'icon': "",
                            'device_class': "",
                            'attributes': {
                                'timestamps': plunge_timestamps,
                                'prices': plunge_prices
                            },
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
            url = ""
            name_tariff = "Error"

    await async_update_data()

    hass.data[DOMAIN]["HOME_ENERGY_HUB_SENSOR_COORDINATOR"+entry_id] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="home_energy_hub_"+entry_id,
        update_method=async_update_data,
        update_interval=timedelta(seconds=ha_update_time),  # Define how often to fetch data
    )
    await hass.data[DOMAIN]["HOME_ENERGY_HUB_SENSOR_COORDINATOR"+entry_id].async_refresh() 