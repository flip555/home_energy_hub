from homeassistant.helpers.entity import Entity
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers import device_registry as dr
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

async def OctopusEnergyUKTariffEngineTracker(hass, entry):
    api_update_time = entry.data.get("octopus_api_update_frequency")
    ha_update_time = entry.data.get("sensor_update_frequency")
    name_tariff = "None"
    options_flow = entry.data.get("options_flow")
    entry_id = entry.entry_id 
    selected_regions = entry.data.get("current_region")
    selected_fuels = entry.data.get("fuel")

    async def GET_TRACKER_ELECTRIC(region, fuel):
        url = f"https://api.octopus.energy/v1/products/SILVER-FLEX-22-11-25/electricity-tariffs/E-1R-SILVER-FLEX-22-11-25-{region}/standard-unit-rates/"
        async with aiohttp.ClientSession() as session, session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                _LOGGER.debug("Update received from Octopus Energy API")
                current_time = datetime.utcnow().timestamp()                
                hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA_UPDATE_TIME_" + entry_id + "_" + fuel + "_" + region] = current_time
                hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA" + entry_id + "_" + fuel + "_" + region] = data
                return data
            else:
                _LOGGER.error("Failed to get data from Octopus Energy API, status: %s", resp.status)
                return None

    async def GET_TRACKER_GAS(region, fuel):
        url = f"https://api.octopus.energy/v1/products/SILVER-FLEX-22-11-25/gas-tariffs/G-1R-SILVER-FLEX-22-11-25-{region}/standard-unit-rates/"
        async with aiohttp.ClientSession() as session, session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                _LOGGER.debug("Update received from Octopus Energy API")
                current_time = datetime.utcnow().timestamp()                
                hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA_UPDATE_TIME_" + entry_id + "_" + fuel + "_" + region] = current_time
                hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA" + entry_id + "_" + fuel + "_" + region] = data
                return data
            else:
                _LOGGER.error("Failed to get data from Octopus Energy API, status: %s", resp.status)
                return None

    async def async_update_data():
        sensors = {}
        binary_sensors = {}
        device_registry = dr.async_get(hass)

        for fuel in selected_fuels:
            for region in selected_regions:
                # Check if the timestamp is set
                if "HOME_ENERGY_HUB_OCTOPUS_DATA_UPDATE_TIME_" + entry_id + "_" + fuel + "_" + region in hass.data[DOMAIN]:
                    last_update_unix = hass.data[DOMAIN].get("HOME_ENERGY_HUB_OCTOPUS_DATA_UPDATE_TIME_" + entry_id + "_" + fuel + "_" + region)
                    last_update_time = datetime.utcfromtimestamp(last_update_unix)
                    current_time = datetime.utcnow()

                    if last_update_time > current_time - timedelta(seconds=api_update_time):
                        # Use existing data
                        data = hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA" + entry_id + "_" + fuel + "_" + region]
                    else:
                        # Fetch new data
                        if fuel == "Gas":
                            data = await GET_TRACKER_GAS(region, fuel)
                        elif fuel == "Electric":
                            data = await GET_TRACKER_ELECTRIC(region, fuel)

                else:
                    # If the timestamp isn't set, fetch new data
                    if fuel == "Gas":
                        data = await GET_TRACKER_GAS(region, fuel)
                    elif fuel == "Electric":
                        data = await GET_TRACKER_ELECTRIC(region, fuel)

                device_registry.async_get_or_create(
                    config_entry_id=entry.entry_id,
                    identifiers={("home_energy_hub", entry.entry_id, "Tracker", region, fuel)},
                    manufacturer="Octopus Energy UK",
                    name="Tracker Region "+region+" - "+fuel,
                    model="Tracker Tariff " + fuel,
                    entry_type=DeviceEntryType.SERVICE,
                )

                _LOGGER.debug("Update received from Octopus Energy API%s", data)# Get today's date
                today = datetime.now().date()

                # Calculate tomorrow's date
                tomorrow = today + timedelta(days=1)

                tracker_today = None
                tracker_tomorrow = None

                for item in data.get("results", []):
                    item_date_str = item.get("valid_from")  # Use the "valid_from" key for the date
                    item_date = datetime.strptime(item_date_str, "%Y-%m-%dT%H:%M:%SZ").date()  # Convert string to date

                    price = item.get("value_inc_vat")
                    # Assuming standing_charge is not present in the provided JSON structure
                    tracker_standing_charge_today = None

                    if item_date == today:
                        tracker_today = price
                    elif item_date == tomorrow:
                        tracker_tomorrow = price

                _LOGGER.debug("Updating HA Sensor based on Stored data")
                sensors["tracker_tomorrow_"+region+fuel] = {
                    'state': tracker_tomorrow,
                    'name': f"Octopus Tracker {fuel} - Region {region} - Tomorrows Price",
                    'unique_id': f"Octopus Tracker {fuel} - Region {region} - Tomorrows Price",
                    'unit': "p",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Tracker", region, fuel )},
                            )
                }
                sensors["tracker_today_"+region+fuel] = {
                    'state': tracker_today,
                    'name': f"Octopus Tracker {fuel} - Region {region} - Current Price",
                    'unique_id': f"Octopus Tracker {fuel} - Region {region} - Current Price",
                    'unit': "p",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Tracker", region, fuel )},
                            )
                }
                sensors["tracker_today_gbp_"+region+fuel] = {
                    'state': tracker_today / 100,
                    'name': f"Octopus Tracker {fuel} - Region {region} - Current Price GBP",
                    'unique_id': f"Octopus Tracker {fuel} - Region {region} - Current Price GBP",
                    'unit': "GBP/kWh",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Tracker", region, fuel )},
                            )
                }
                
                sensors["tracker_standing_chargetoday_"+region+fuel] = {
                    'state': tracker_standing_charge_today,
                    'name': f"Octopus Tracker {fuel} - Region {region} - Standing Charge",
                    'unique_id': f"Octopus Tracker {fuel} - Region {region} - Standing Charge",
                    'unit': "p",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Tracker", region, fuel )},
                            )
                }

        return {
                'binary_sensors': binary_sensors,
                'sensors': sensors
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