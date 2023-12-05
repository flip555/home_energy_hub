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

async def OctopusEnergyUKTariffEngineCosy(hass, entry):
    api_update_time = entry.data.get("octopus_api_update_frequency")
    ha_update_time = entry.data.get("sensor_update_frequency")
    name_tariff = "None"
    options_flow = entry.data.get("options_flow")
    entry_id = entry.entry_id 
    selected_regions = entry.data.get("current_region")
    selected_fuels = {"Electric"}

    async def GET_COSY_ELECTRIC(region, fuel):
        url = f"https://api.octopus.energy/v1/products/COSY-22-12-08/electricity-tariffs/E-1R-COSY-22-12-08-{region}/standard-unit-rates/"
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
                return hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA" + entry_id + "_" + fuel + "_" + region]

    async def GET_STANDING_CHARGE_ELECTRIC(region, fuel):
        url = f"https://api.octopus.energy/v1/products/COSY-22-12-08/electricity-tariffs/E-1R-COSY-22-12-08-{region}/standing-charges/"
        async with aiohttp.ClientSession() as session, session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                _LOGGER.debug("Update received from Octopus Energy API")
                current_time = datetime.utcnow().timestamp()                
                hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA_UPDATE_TIME_STANDING_CHARGE_" + entry_id + "_" + fuel + "_" + region] = current_time
                hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA_STANDING_CHARGE_" + entry_id + "_" + fuel + "_" + region] = data
                return data
            else:
                _LOGGER.error("Failed to get data from Octopus Energy API, status: %s", resp.status)
                return hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA_STANDING_CHARGE_" + entry_id + "_" + fuel + "_" + region]

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
                    if (
                        last_update_time > current_time - timedelta(seconds=api_update_time)
                        and hass.data[DOMAIN].get("HOME_ENERGY_HUB_OCTOPUS_DATA" + entry_id + "_" + fuel + "_" + region) is not None
                    ):
                        # Use existing data
                        data = hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA" + entry_id + "_" + fuel + "_" + region]
                    else:
                        data = await GET_COSY_ELECTRIC(region, fuel)

                else:
                    data = await GET_COSY_ELECTRIC(region, fuel)

                device_registry.async_get_or_create(
                    config_entry_id=entry.entry_id,
                    identifiers={("home_energy_hub", entry.entry_id, "Cosy", region, fuel)},
                    manufacturer="Octopus Energy UK",
                    name="Cosy Region "+region+" - "+fuel,
                    model="Cosy Tariff " + fuel,
                    entry_type=DeviceEntryType.SERVICE,
                )
                _LOGGER.debug("Update received from Octopus Energy API%s", data)
                time_price_list = []
                future_negative_prices = []
                now = datetime.now(timezone.utc)
                cutoff_time = now - timedelta(hours=12)
                for item in data.get("results", []):
                    time = item.get("valid_from")  # Extract the 'valid_from' time
                    price = item.get("value_inc_vat")  # Extract the 'value_inc_vat' price
                    if price <= 0:
                        background_color = 'skyblue' 
                    elif price <= 3:
                        background_color = 'limegreen' 
                    elif price <= 5:
                        background_color = 'springgreen' 
                    elif price <= 7:
                        background_color = 'greenyellow' 
                    elif price <= 10:
                        background_color = 'blanchedalmond' 
                    elif price <= 15:
                        background_color = 'khaki' 
                    elif price <= 20:
                        background_color = 'yellow' 
                    elif price <= 25:
                        background_color = 'gold' 
                    elif price <= 30:
                        background_color = 'orange' 
                    elif price <= 40:
                        background_color = 'hotpink' 
                    else:
                        background_color = 'red' 
                     
                    time_as_datetime = datetime.fromisoformat(time)

                    if time_as_datetime > cutoff_time:  # Remove prices older than 24 hours
                        if time is not None and price is not None:
                            time_price_list.append((time, price, background_color))
                
                time_price_list.sort()
                current_price = next_price = previous_price = None

                for i, (time, price, background_color) in enumerate(time_price_list):
                    time_as_datetime = datetime.fromisoformat(time)

                    if time_as_datetime > now:
                        next_price = price
                        break  # exit the loop as we've found the next price
                    
                    previous_price = current_price  # store the last "current" price as "previous" before updating "current"
                    current_price = price  # update the "current" price
                    current_price_colour = background_color  # update the "current" price

                timestamps = [x[0] for x in time_price_list]
                prices = [x[1] for x in time_price_list]
                colours = [x[2] for x in time_price_list]
 

                _LOGGER.debug("Updating HA Sensor based on Stored data")
                sensors["cosy_current_"+region+fuel] = {
                    'state': current_price,
                    'name': f"Octopus Cosy {fuel} - Region {region} - Current Price",
                    'unique_id': f"Octopus Cosy {fuel} - Region {region} - Current Price",
                    'unit': "p",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                        'timestamps': timestamps,
                        'prices': prices,
                        'colours': colours,
                        'colour': current_price_colour
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Cosy", region, fuel )},
                            )
                }
                sensors["cosy_current_gbp_"+region+fuel] = {
                    'state': current_price / 100,
                    'name': f"Octopus Cosy {fuel} - Region {region} - Current Price GBP",
                    'unique_id': f"Octopus Cosy {fuel} - Region {region} - Current Price GBP",
                    'unit': "GBP/kWh",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Cosy", region, fuel )},
                            )
                }
                sensors["cosy_next_"+region+fuel] = {
                    'state': next_price,
                    'name': f"Octopus Cosy {fuel} - Region {region} - Next Price",
                    'unique_id': f"Octopus Cosy {fuel} - Region {region} - Next Price",
                    'unit': "p",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Cosy", region, fuel )},
                            )
                }
                sensors["cosy_next_gbp_"+region+fuel] = {
                    'state': next_price / 100,
                    'name': f"Octopus Cosy {fuel} - Region {region} - Next Price GBP",
                    'unique_id': f"Octopus Cosy {fuel} - Region {region} - Next Price GBP",
                    'unit': "GBP/kWh",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Cosy", region, fuel )},
                            )
                }


                if "HOME_ENERGY_HUB_OCTOPUS_DATA_UPDATE_TIME_STANDING_CHARGE_" + entry_id + "_" + fuel + "_" + region in hass.data[DOMAIN]:
                    last_update_unix = hass.data[DOMAIN].get("HOME_ENERGY_HUB_OCTOPUS_DATA_UPDATE_TIME_STANDING_CHARGE_" + entry_id + "_" + fuel + "_" + region)
                    last_update_time = datetime.utcfromtimestamp(last_update_unix)
                    current_time = datetime.utcnow()
                    if (
                        last_update_time > current_time - timedelta(seconds=api_update_time)
                        and hass.data[DOMAIN].get("HOME_ENERGY_HUB_OCTOPUS_DATA_STANDING_CHARGE_" + entry_id + "_" + fuel + "_" + region) is not None
                    ):
                        standing_charge_data = hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA_STANDING_CHARGE_" + entry_id + "_" + fuel + "_" + region]
                    else:
                        standing_charge_data = await GET_STANDING_CHARGE_ELECTRIC(region, fuel)
                else:
                    standing_charge_data = await GET_STANDING_CHARGE_ELECTRIC(region, fuel)

                for item in standing_charge_data.get("results", []):
                    if item.get("valid_to") is None:
                        standing_charge = item.get("value_inc_vat")  # Extract the 'value_inc_vat' price

                sensors["cosy_standing_charge_"+region+fuel] = {
                    'state': standing_charge,
                    'name': f"Octopus Cosy {fuel} - Region {region} - Standing Charge",
                    'unique_id': f"Octopus Cosy {fuel} - Region {region} - Standing Charge",
                    'unit': "p",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Cosy", region, fuel )},
                            )
                }
                sensors["cosy_standing_charge_gbp_"+region+fuel] = {
                    'state': standing_charge / 100,
                    'name': f"Octopus Cosy {fuel} - Region {region} - Standing Charge GBP",
                    'unique_id': f"Octopus Cosy {fuel} - Region {region} - Standing Charge GBP",
                    'unit': "GBP",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Cosy", region, fuel )},
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