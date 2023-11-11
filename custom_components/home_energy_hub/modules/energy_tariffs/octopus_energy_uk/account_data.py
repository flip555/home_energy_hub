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
    name_prefix = entry.data.get("name_prefix")
    ha_update_time = entry.data.get("sensor_update_frequency")
    options_flow = entry.data.get("options_flow")
    APIKEY = entry.data.get("api_key")
    ACCOUNT_ID = entry.data.get("account_id")
    sensors = {}
    binary_sensors = {}

    async def async_update_data():
        url = f'https://api.octopus.energy/v1/accounts/{ACCOUNT_ID}/'
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, auth=aiohttp.BasicAuth(APIKEY, '')) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    current_time = datetime.utcnow().timestamp()
                    hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA" + entry_id] = data
# data = {'number': 'A-022DD767', 'properties': [{'id': 5659170, 'moved_in_at': '2023-06-05T00:00:00+01:00', 'moved_out_at': None, 'address_line_1': '1 WATER TOWER VIEW ST. MARYS ROAD', 'address_line_2': '', 'address_line_3': '', 'town': 'NEW ROMNEY', 'county': '', 'postcode': 'TN28 8JB', 'electricity_meter_points': [{'mpan': '1900091521990', 'profile_class': 1, 'consumption_standard': 6669, 'meters': [{'serial_number': 'Z17QU18663', 'registers': [{'identifier': '1', 'rate': 'STANDARD', 'is_settlement_register': True}]}, {'serial_number': '23E5069436', 'registers': [{'identifier': '1', 'rate': 'STANDARD', 'is_settlement_register': True}]}], 'agreements': [{'tariff_code': 'E-1R-VAR-22-11-01-J', 'valid_from': '2023-06-07T00:00:00+01:00', 'valid_to': '2023-08-19T00:00:00+01:00'}, {'tariff_code': 'E-1R-AGILE-FLEX-22-11-25-J', 'valid_from': '2023-08-19T00:00:00+01:00', 'valid_to': '2023-11-02T00:00:00Z'}, {'tariff_code': 'E-1R-VAR-22-11-01-J', 'valid_from': '2023-11-02T00:00:00Z', 'valid_to': '2023-11-03T00:00:00Z'}, {'tariff_code': 'E-1R-AGILE-FLEX-22-11-25-J', 'valid_from': '2023-11-03T00:00:00Z', 'valid_to': None}], 'is_export': False}], 'gas_meter_points': [{'mprn': '9358822602', 'consumption_standard': 10293, 'meters': [{'serial_number': 'E6E09693632323'}, {'serial_number': 'E6S11037831756'}], 'agreements': [{'tariff_code': 'G-1R-VAR-22-11-01-J', 'valid_from': '2023-06-07T00:00:00+01:00', 'valid_to': '2023-08-26T00:00:00+01:00'}, {'tariff_code': 'G-1R-SILVER-FLEX-22-11-25-J', 'valid_from': '2023-08-26T00:00:00+01:00', 'valid_to': None}]}]}]}

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