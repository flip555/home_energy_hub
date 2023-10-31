from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.entity_component import EntityComponent
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

async def OctopusUKEnergyUKINIT(hass, region, entry, async_add_entities):
    name_tariff = "None"
    options_flow = entry.get("options_flow")

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
                        'prices': {
                            'current': current_price,
                            'pound_current': current_price / 100,
                            'next': next_price,
                            'previous': previous_price
                        },
                        'full_json': {
                            'timestamps': timestamps,
                            'prices': prices
                        },
                        'future_negative_prices': {
                            'timestamps': plunge_timestamps,
                            'prices': plunge_prices
                        },
                    }

                else:
                    _LOGGER.error("Failed to get data from Octopus Energy API, status: %s", resp.status)
                    return None

        elif "flexible" in options_flow:
            url = f"https://api.octopus.energy/v1/products/VAR-22-11-01/electricity-tariffs/E-1R-VAR-22-11-01-{region}/standard-unit-rates/"
            name_tariff = "Flexible"
            async with aiohttp.ClientSession() as session, session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", [])
                    
                    direct_debit_price = None
                    non_direct_debit_price = None

                    # Loop through the results to find the current price for each payment method
                    for item in results:
                        if item["valid_to"] is None:
                            if item["payment_method"] == "DIRECT_DEBIT":
                                direct_debit_price = item.get("value_inc_vat")
                            elif item["payment_method"] == "NON_DIRECT_DEBIT":
                                non_direct_debit_price = item.get("value_inc_vat")

                    return {
                        'direct_debit_price': direct_debit_price,
                        'non_direct_debit': non_direct_debit_price,
                        'pound_direct_debit_price': direct_debit_price / 100,
                        'pound_non_direct_debit': non_direct_debit_price / 100
                    }

                else:
                    _LOGGER.error("Failed to get data from the API, status: %s", resp.status)
                    return None

        elif "tracker" in options_flow:
            url = f"https://octopus.energy/api/v1/tracker/E-1R-SILVER-FLEX-22-11-25-{region}/daily/current/1/1/"
            name_tariff = "Tracker"
            async with aiohttp.ClientSession() as session, session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    periods = data.get("periods", [])
                    
                    current_data = {}
                    
                    # Assuming that the most recent data is the first in the list
                    if periods:
                        latest_period = periods[0]
                        if latest_period["date"] == "2023-10-01":  # You can adjust this to whatever date logic you want
                            current_data = {
                                "date": latest_period["date"],
                                "market_index": latest_period["market_index"],
                                "cost": latest_period["cost"],
                                "standing_charge": latest_period["standing_charge"],
                                "unit_rate": latest_period["unit_rate"],
                                "usage": latest_period["usage"],
                                "unit_charge": latest_period["unit_charge"]
                            }

                    return current_data

                else:
                    _LOGGER.error("Failed to get data from the API, status: %s", resp.status)
                    return None
        else:
            url = ""
            name_tariff = "Error"
        

    time_price_list = await async_update_data()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="seplos_bms_sensor",
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),  # Define how often to fetch data
    )
    _LOGGER.debug("async_refresh data generate_sensors called")
    await coordinator.async_refresh() 
    setting_sensors = []
    if "agile" in options_flow:
        name_tariff = "Agile"
        setting_sensors = [
            OctopusSensor(coordinator, f"Octopus {name_tariff} - Region {region} - Current Price", "current", "p", "mdi:currency-gbp"),
            OctopusSensor(coordinator, f"Octopus {name_tariff} - Region {region} - GBP Current Price", "pound_current", "£", "mdi:currency-gbp"),
            OctopusSensor(coordinator, f"Octopus {name_tariff} - Region {region} - Next Price", "next", "p", "mdi:currency-gbp"),
            OctopusSensor(coordinator, f"Octopus {name_tariff} - Region {region} - Previous Price", "previous", "p", "mdi:currency-gbp"),
            OctopusSensor(coordinator, f"Octopus {name_tariff} - Region {region} - JSON", "full_json"),
            OctopusSensor(coordinator, f"Octopus {name_tariff} - Region {region} - Plunge Pricing JSON", "future_negative_prices"),
        ]
    elif "flexible" in options_flow:
        url = f"https://api.octopus.energy/v1/products/VAR-22-11-01/electricity-tariffs/E-1R-VAR-22-11-01-{region}/standard-unit-rates/?page_size=1"
        name_tariff = "Flexible"
        setting_sensors = [
            OctopusSensor(coordinator, f"Octopus {name_tariff} - Region {region} - DD Current Price", "direct_debit_price", "p", "mdi:currency-gbp"),
            OctopusSensor(coordinator, f"Octopus {name_tariff} - Region {region} - DD GBP Current Price", "pound_direct_debit_price", "£", "mdi:currency-gbp"),
            OctopusSensor(coordinator, f"Octopus {name_tariff} - Region {region} - Non-DD Current Price", "non_direct_debit", "p", "mdi:currency-gbp"),
            OctopusSensor(coordinator, f"Octopus {name_tariff} - Region {region} - Non-DD GBP Current Price", "pound_non_direct_debit", "£", "mdi:currency-gbp"),
        ]
    elif "tracker" in options_flow:
        url = f"https://octopus.energy/api/v1/tracker/G-1R-SILVER-FLEX-22-11-25-{region}/daily/current/1/1/"
        name_tariff = "Tracker"
        setting_sensors = [
            OctopusSensor(coordinator, f"Octopus {name_tariff} - Region {region} - Unit Rate", "unit_rate", "p", "mdi:currency-gbp"),
        ]
    else:
        url = ""
        name_tariff = "Error"

    # Combine all sensor lists
    sensors = setting_sensors

    async_add_entities(sensors, True)

class OctopusSensor(CoordinatorEntity):
    def __init__(self, coordinator, name, time_key, unit=None, icon=None):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._name = name
        self._time_key = time_key  # Either 'current', 'next', or 'previous'
        self._unit = unit
        self._icon = icon
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name}"
        
    @property
    def unique_id(self):
        """Return a unique ID for this entity."""
        return f"{self._name}"

    @property
    def icon(self):
        """Return the icon of the sensor."""
        if self._time_key == 'full_json' or self._time_key == "future_negative_prices":
            return None
        else:
            return self._icon

    @property
    def state(self):
        if self._time_key == 'full_json':
            return self.coordinator.data['prices']['current']
        if self._time_key == "future_negative_prices":
            return "OK"
        if self._time_key == "direct_debit_price" or self._time_key == "unit_rate" or self._time_key == "pound_direct_debit_price" or self._time_key == "non_direct_debit" or self._time_key == "pound_non_direct_debit":
            return self.coordinator.data[self._time_key]

        else:
            return self.coordinator.data['prices'][self._time_key]

    @property
    def unit_of_measurement(self):
        """Return the state of the sensor."""
        if self._time_key == 'full_json' or self._time_key == "future_negative_prices":
            return None
        else:
            return self._unit

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = {}
        if self._time_key == 'full_json':
            attributes = self.coordinator.data['full_json']
        if self._time_key == 'future_negative_prices':
            attributes = self.coordinator.data['future_negative_prices']
        return attributes
