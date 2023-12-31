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

async def OctopusEnergyUKTariffEngineGo(hass, entry):
    api_update_time = entry.data.get("octopus_api_update_frequency")
    ha_update_time = entry.data.get("sensor_update_frequency")
    entry_id = entry.entry_id 
    selected_regions = entry.data.get("current_region")
    selected_fuels = {"Electric"}

    async def GET_GO_ELECTRIC(region, fuel):
        url = f"https://api.octopus.energy/v1/products/GO-VAR-22-10-14/electricity-tariffs/E-1R-GO-VAR-22-10-14-{region}/standard-unit-rates/"
        async with aiohttp.ClientSession() as session, session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                current_time = datetime.utcnow().timestamp()                
                hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA_UPDATE_TIME_" + entry_id + "_" + fuel + "_" + region] = current_time
                hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA" + entry_id + "_" + fuel + "_" + region] = data
                return data
            else:
                _LOGGER.error("Failed to get data from Octopus Energy API, status: %s", resp.status)
                return hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA" + entry_id + "_" + fuel + "_" + region]

    async def GET_STANDING_CHARGE_GO_ELECTRIC(region, fuel):
        url = f"https://api.octopus.energy/v1/products/GO-VAR-22-10-14/electricity-tariffs/E-1R-GO-VAR-22-10-14-{region}/standing-charges/"
        async with aiohttp.ClientSession() as session, session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
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
                        data = hass.data[DOMAIN]["HOME_ENERGY_HUB_OCTOPUS_DATA" + entry_id + "_" + fuel + "_" + region]
                    else:
                        data = await GET_GO_ELECTRIC(region, fuel)
                else:
                    data = await GET_GO_ELECTRIC(region, fuel)

                device_registry.async_get_or_create(
                    config_entry_id=entry.entry_id,
                    identifiers={("home_energy_hub", entry.entry_id, "Go", region, fuel)},
                    manufacturer="Octopus Energy UK",
                    name="Go Region "+region+" - "+fuel,
                    model="Go Tariff " + fuel,
                    entry_type=DeviceEntryType.SERVICE,
                )
                time_price_list = []
                future_negative_prices = []
                now = datetime.now(timezone.utc)
                cutoff_time = now - timedelta(hours=24)

                # Iterate through results
                for item in data.get("results", []):
                    time = item.get("valid_from")
                    valid_to = item.get("valid_to")
                    price = item.get("value_inc_vat")
                    
                    if price is not None and time is not None:
                        time_as_datetime = datetime.fromisoformat(time)
                        valid_to_as_datetime = datetime.fromisoformat(valid_to)
                        
                        if time_as_datetime > cutoff_time or valid_to_as_datetime > cutoff_time :
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
                            time_price_list.append((time, price, background_color))

                time_price_list.sort()

                # Initialize current and next prices
                current_price, next_price = None, None

                for i, (time, price, background_color) in enumerate(time_price_list):
                    if i == 0:
                        current_price = price
                        if price <= 0:
                            current_price_colour = 'skyblue' 
                        elif price <= 3:
                            current_price_colour = 'limegreen' 
                        elif price <= 5:
                            current_price_colour = 'springgreen' 
                        elif price <= 7:
                            current_price_colour = 'greenyellow' 
                        elif price <= 10:
                            current_price_colour = 'blanchedalmond' 
                        elif price <= 15:
                            current_price_colour = 'khaki' 
                        elif price <= 20:
                            current_price_colour = 'yellow' 
                        elif price <= 25:
                            current_price_colour = 'gold' 
                        elif price <= 30:
                            current_price_colour = 'orange' 
                        elif price <= 40:
                            current_price_colour = 'hotpink' 
                        else:
                            current_price_colour = 'red' 
                    elif i == 1:
                        next_price = price

                timestamps = [x[0] for x in time_price_list]
                prices = [x[1] for x in time_price_list]
                colours = [x[2] for x in time_price_list]

                sensors["go_current_"+region+fuel] = {
                    'state': current_price,
                    'name': f"Octopus Go {fuel} - Region {region} - Current Price",
                    'unique_id': f"Octopus Go {fuel} - Region {region} - Current Price",
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
                                identifiers={("home_energy_hub", entry.entry_id, "Go", region, fuel )},
                            )
                }
                sensors["go_current_gbp_"+region+fuel] = {
                    'state': current_price / 100,
                    'name': f"Octopus Go {fuel} - Region {region} - Current Price GBP",
                    'unique_id': f"Octopus Go {fuel} - Region {region} - Current Price GBP",
                    'unit': "GBP/kWh",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Go", region, fuel )},
                            )
                }
                sensors["go_next_"+region+fuel] = {
                    'state': next_price,
                    'name': f"Octopus Go {fuel} - Region {region} - Next Price",
                    'unique_id': f"Octopus Go {fuel} - Region {region} - Next Price",
                    'unit': "p",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Go", region, fuel )},
                            )
                }
                sensors["go_next_gbp_"+region+fuel] = {
                    'state': next_price / 100,
                    'name': f"Octopus Go {fuel} - Region {region} - Next Price GBP",
                    'unique_id': f"Octopus Go {fuel} - Region {region} - Next Price GBP",
                    'unit': "GBP/kWh",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Go", region, fuel )},
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
                        standing_charge_data = await GET_STANDING_CHARGE_GO_ELECTRIC(region, fuel)
                else:
                    standing_charge_data = await GET_STANDING_CHARGE_GO_ELECTRIC(region, fuel)

                for item in standing_charge_data.get("results", []):
                    if item.get("valid_to") is None:
                        standing_charge = item.get("value_inc_vat")  # Extract the 'value_inc_vat' price

                sensors["go_standing_charge_"+region+fuel] = {
                    'state': standing_charge,
                    'name': f"Octopus Go {fuel} - Region {region} - Standing Charge",
                    'unique_id': f"Octopus Go {fuel} - Region {region} - Standing Charge",
                    'unit': "p",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Go", region, fuel )},
                            )
                }
                sensors["go_standing_charge_gbp_"+region+fuel] = {
                    'state': standing_charge / 100,
                    'name': f"Octopus Go {fuel} - Region {region} - Standing Charge GBP",
                    'unique_id': f"Octopus Go {fuel} - Region {region} - Standing Charge GBP",
                    'unit': "GBP",
                    'icon': "",
                    'device_class': "",
                    'state_class': "",
                    'attributes': {
                    },
                    'device_register': DeviceInfo(
                                identifiers={("home_energy_hub", entry.entry_id, "Go", region, fuel )},
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