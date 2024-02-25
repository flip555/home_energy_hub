from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.components.binary_sensor import BinarySensorEntity
from functools import partial
from homeassistant.helpers import device_registry as dr

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


async def GeoHomeIHD(hass, entry):
    GEO_BASE_URL = 'https://api.geotogether.com'
    device_registry = dr.async_get(hass)
    entry_id = entry.entry_id
    ha_update_time = entry.data.get("sensor_update_frequency")
    username = entry.data.get("username")
    password = entry.data.get("password")
    sensors = {}
    binary_sensors = {}

    async def make_request(url, method='GET', params={}, headers={}, json_body=None):
        func = partial(requests.request, method, GEO_BASE_URL + url, params=params, headers=headers, json=json_body)
        response = await hass.async_add_executor_job(func)
        response.raise_for_status()
        return response.json()

    async def login():
        headers = {'Content-Type': 'application/json'}
        body = {'identity': username, 'password': password}
        response = await make_request('/usersservice/v2/login', 'POST', headers=headers, json_body=body)
        return response['accessToken']

    async def get_device_data(access_token):
        headers = {'Authorization': f"Bearer {access_token}"}
        return await make_request('/api/userapi/v2/user/detail-systems?systemDetails=true', 'GET', headers=headers)

    async def get_periodic_meter_data(access_token, system_id):
        headers = {'Authorization': f"Bearer {access_token}"}
        return await make_request(f"/api/userapi/system/smets2-periodic-data/{system_id}", 'GET', headers=headers)

    async def get_live_meter_data(access_token, system_id):
        headers = {'Authorization': f"Bearer {access_token}"}
        return await make_request(f"/api/userapi/system/smets2-live-data/{system_id}", 'GET', headers=headers)


    # Assuming 'hass' and 'entry' are defined in your scope
    # Define a function to check cache validity
    def is_cache_valid(cache_key, expiration_delta):
        cache_entry = hass.data[DOMAIN].get(cache_key, {})
        timestamp = cache_entry.get('timestamp')
        if not timestamp:
            return False
        return datetime.now() - timestamp < expiration_delta

    # Define a function to update the cache
    def update_cache(cache_key, data):
        hass.data[DOMAIN][cache_key] = {
            'timestamp': datetime.now(),
            'data': data
        }

    # Define a function to get cached data
    def get_cached_data(cache_key):
        return hass.data[DOMAIN].get(cache_key, {}).get('data')

    async def get_consolidated_data():
        cache_key_token = f"HOME_ENERGY_HUB_SENSOR_COORDINATOR{entry_id}GEOHOME_CACHE_TOKEN"
        cache_key_system_id = f"HOME_ENERGY_HUB_SENSOR_COORDINATOR{entry_id}GEOHOME_CACHE_SYSTEM_ID"
        cache_key_periodic_data = f"HOME_ENERGY_HUB_SENSOR_COORDINATOR{entry_id}GEOHOME_CACHE_PERIODIC_DATA"
        cache_key_live_data = f"HOME_ENERGY_HUB_SENSOR_COORDINATOR{entry_id}GEOHOME_CACHE_LIVE_DATA"
        cache_key_device_data = f"HOME_ENERGY_HUB_SENSOR_COORDINATOR{entry_id}GEOHOME_CACHE_DEVICE_DATA"
        
        try:
            if not is_cache_valid(cache_key_token, timedelta(hours=1)):
                token = await login()
                update_cache(cache_key_token, token)
            else:
                token = get_cached_data(cache_key_token)

            if not is_cache_valid(cache_key_system_id, timedelta(hours=1)):
                system_id = (await get_device_data(token))["systemRoles"][0]["systemId"]
                update_cache(cache_key_system_id, system_id)
            else:
                system_id = get_cached_data(cache_key_system_id)

            if not is_cache_valid(cache_key_periodic_data, timedelta(minutes=10)):
                periodic_meter_data = await get_periodic_meter_data(token, system_id)
                update_cache(cache_key_periodic_data, periodic_meter_data)
            else:
                periodic_meter_data = get_cached_data(cache_key_periodic_data)

            if not is_cache_valid(cache_key_live_data, timedelta(seconds=30)):
                live_meter_data = await get_live_meter_data(token, system_id)
                update_cache(cache_key_live_data, live_meter_data)
            else:
                live_meter_data = get_cached_data(cache_key_live_data)

            if not is_cache_valid(cache_key_device_data, timedelta(hours=1)):
                device_data = await get_device_data(token)
                update_cache(cache_key_device_data, device_data)
            else:
                device_data = get_cached_data(cache_key_device_data)

            consolidated_data = {
                'PeriodicMeterData': periodic_meter_data,
                'LiveMeterData': live_meter_data,
                'DeviceData': device_data
            }

            return consolidated_data

        except Exception as e:
            # Invalidate cache in case of failure to ensure fresh login/system ID retrieval on next attempt
            for key in [cache_key_token, cache_key_system_id, cache_key_periodic_data, cache_key_live_data, cache_key_device_data]:
                hass.data[DOMAIN].pop(key, None)
            raise e


        except Exception as e:
            # Invalidate cache in case of failure to ensure fresh login/system ID retrieval on next attempt
            for key in [cache_key_token, cache_key_system_id, cache_key_periodic_data, cache_key_live_data, cache_key_device_data]:
                hass.data[DOMAIN].pop(key, None)
            raise e

    async def async_update_data():
        data = await get_consolidated_data()
        sensors = {
            'electricity_total_consumption': {
                'state': data['PeriodicMeterData']['totalConsumptionList'][0]['totalConsumption'],
                'name': "Geo IHD - Electricity Total Consumption",
                'unique_id': "geo_ihd_electricity_total_consumption",
                'unit': "kWh",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "electric")},
                        )      
            },
            'gas_total_consumption': {
                'state': data['PeriodicMeterData']['totalConsumptionList'][1]['totalConsumption'],
                'name': "Geo IHD - Gas Total Consumption",
                'unique_id': "geo_ihd_gas_total_consumption",
                'unit': "kWh",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "gas")},
                        )      
            },
            'electricity_supply_status': {
                'state': data['PeriodicMeterData']['supplyStatusList'][0]['supplyStatus'],
                'name': "Geo IHD - Electricity Supply Status",
                'unique_id': "geo_ihd_electricity_supply_status",
                'unit': "",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "electric")},
                        )      
            },
            'gas_supply_status': {
                'state': data['PeriodicMeterData']['supplyStatusList'][1]['supplyStatus'],
                'name': "Geo IHD - Gas Supply Status",
                'unique_id': "geo_ihd_gas_supply_status",
                'unit': "",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "gas")},
                        )      
            },
            'electricity_bill_to_date': {
                'state': data['PeriodicMeterData']['billToDateList'][0]['billToDate'],
                'name': "Geo IHD - Electricity Bill To Date",
                'unique_id': "geo_ihd_electricity_bill_to_date",
                'unit': "p",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "electric")},
                        )      
            },
            'gas_bill_to_date': {
                'state': data['PeriodicMeterData']['billToDateList'][1]['billToDate'],
                'name': "Geo IHD - Gas Bill To Date",
                'unique_id': "geo_ihd_gas_bill_to_date",
                'unit': "p",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "gas")},
                        )      
            },
            'electricity_active_tariff_price': {
                'state': data['PeriodicMeterData']['activeTariffList'][0]['activeTariffPrice'],
                'name': "Geo IHD - Electricity Active Tariff Price",
                'unique_id': "geo_ihd_electricity_active_tariff_price",
                'unit': "p/kWh",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "electric")},
                        )      
            },
            'gas_active_tariff_price': {
                'state': data['PeriodicMeterData']['activeTariffList'][1]['activeTariffPrice'],
                'name': "Geo IHD - Gas Active Tariff Price",
                'unique_id': "geo_ihd_gas_active_tariff_price",
                'unit': "p/kWh",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "gas")},
                        )      
            },
            'electricity_cost_day': {
                'state': data['PeriodicMeterData']['currentCostsElec'][0]['costAmount'],
                'name': "Geo IHD - Electricity Cost (Day)",
                'unique_id': "geo_ihd_electricity_cost_day",
                'unit': "p",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "electric")},
                        )      
            },
            'electricity_cost_week': {
                'state': data['PeriodicMeterData']['currentCostsElec'][1]['costAmount'],
                'name': "Geo IHD - Electricity Cost (Week)",
                'unique_id': "geo_ihd_electricity_cost_week",
                'unit': "p",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "electric")},
                        )      
            },
            'electricity_cost_month': {
                'state': data['PeriodicMeterData']['currentCostsElec'][2]['costAmount'],
                'name': "Geo IHD - Electricity Cost (Month)",
                'unique_id': "geo_ihd_electricity_cost_month",
                'unit': "p",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "electric")},
                        )      
            },
            'gas_cost_day': {
                'state': data['PeriodicMeterData']['currentCostsGas'][0]['costAmount'],
                'name': "Geo IHD - Gas Cost (Day)",
                'unique_id': "geo_ihd_gas_cost_day",
                'unit': "p",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "gas")},
                        )      
            },
            'gas_cost_week': {
                'state': data['PeriodicMeterData']['currentCostsGas'][1]['costAmount'],
                'name': "Geo IHD - Gas Cost (Week)",
                'unique_id': "geo_ihd_gas_cost_week",
                'unit': "p",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "gas")},
                        )      
            },
            'gas_cost_month': {
                'state': data['PeriodicMeterData']['currentCostsGas'][2]['costAmount'],
                'name': "Geo IHD - Gas Cost (Month)",
                'unique_id': "geo_ihd_gas_cost_month",
                'unit': "p",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "gas")},
                        )      
            },
            'live_electricity_usage': {
                'state': data['LiveMeterData']['power'][0]['watts'],
                'name': "Geo IHD - Live Electricity Usage",
                'unique_id': "geo_ihd_live_electricity_usage",
                'unit': "W",
                'icon': "",
                'device_class': "power",
                'state_class': "measurement",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "electric")},
                        )      
            },
            'live_gas_usage': {
                'state': data['LiveMeterData']['power'][1]['watts'],
                'name': "Geo IHD - Live Gas Usage",
                'unique_id': "geo_ihd_live_gas_usage",
                'unit': "W",
                'icon': "",
                'device_class': "power",
                'state_class': "measurement",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "gas")},
                        )      
            },
            'electricity_zigbee_status': {
                'state': data['LiveMeterData']['zigbeeStatus']['electricityClusterStatus'],
                'name': "Geo IHD - Electricity Zigbee Status",
                'unique_id': "geo_ihd_electricity_zigbee_status",
                'unit': "",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "electric")},
                        )      
            },
            'gas_zigbee_status': {
                'state': data['LiveMeterData']['zigbeeStatus']['gasClusterStatus'],
                'name': "Geo IHD - Gas Zigbee Status",
                'unique_id': "geo_ihd_gas_zigbee_status",
                'unit': "",
                'icon': "",
                'device_class': "",
                'state_class': "",
                'attributes': {},
                'device_register': DeviceInfo(
                            identifiers={("bms_connector", entry.entry_id, username, "gas")},
                        )            
            },
        }

        # Set default values
        default_device_type = 'Unknown Device'
        default_version = 'v0.0'

        # Attempt to extract device type and version information if available
        device_type = default_device_type
        version_major = '0'
        version_minor = '0'

        if 'DeviceData' in data and 'systemDetails' in data['DeviceData']:
            for systemDetail in data['DeviceData']['systemDetails']:
                if 'devices' in systemDetail and len(systemDetail['devices']) > 0:
                    first_device = systemDetail['devices'][0]
                    device_type = first_device.get('deviceType', default_device_type)
                    version_major = first_device.get('versionNumber', {}).get('major', version_major)
                    version_minor = first_device.get('versionNumber', {}).get('minor', version_minor)
                    break  # Assuming we only need the first device from the first systemDetail that contains devices

        version = f"v{version_major}.{version_minor}"

        # Proceed to create the device_register entry with the extracted or default information
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={("bms_connector", entry.entry_id, username, "electric")},
            manufacturer="Geo Home",
            name=f"Geo Home IHD - Electricity",
            model=device_type,
            sw_version=version,
        )
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={("bms_connector", entry.entry_id, username, "gas")},
            manufacturer="Geo Home",
            name=f"Geo Home IHD - Gas",
            model=device_type,
            sw_version=version,
        )

        


        # Process your data and populate sensors and binary_sensors as needed
        return {
            'binary_sensors': binary_sensors,
            'sensors': sensors,
        }

    # Populate sensors and binary sensors based on the consolidated data
    # This is a placeholder for where you would process the data returned from async_update_data
    await async_update_data()

    hass.data[DOMAIN]["HOME_ENERGY_HUB_SENSOR_COORDINATOR"+entry_id] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="home_energy_hub_"+entry_id,
        update_method=async_update_data,
        update_interval=timedelta(seconds=ha_update_time),  # Define how often to fetch data
    )
    await hass.data[DOMAIN]["HOME_ENERGY_HUB_SENSOR_COORDINATOR"+entry_id].async_refresh() 