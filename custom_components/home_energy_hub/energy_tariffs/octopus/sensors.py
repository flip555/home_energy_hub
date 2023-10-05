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
from ...const import (
    NAME,
    DOMAIN,
    VERSION,
    ATTRIBUTION,
)

_LOGGER = logging.getLogger(__name__)

# Define the generate_sensors function            await OCTOPUS_TARIFFS(hass, region, entry, async_add_entities)

async def generate_sensors(hass, region, entry, async_add_entities):
    async def async_update_data():
        url = "https://api.octopus.energy/v1/products/AGILE-FLEX-22-11-25/electricity-tariffs/E-1R-AGILE-FLEX-22-11-25-J/standard-unit-rates/?page_size=100"
        time_price_list = []  # Initialize an empty list to store times and prices


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

   
    setting_sensors = [
        OctopusSensor(coordinator, "Current Price", "current", "p", "mdi:currency-gbp"),
        OctopusSensor(coordinator, "Next Price", "next", "p", "mdi:currency-gbp"),
        OctopusSensor(coordinator, "Previous Price", "previous", "p", "mdi:currency-gbp"),
        OctopusSensor(coordinator, "JSON", "full_json"),
        OctopusSensor(coordinator, "Plunge Pricing JSON", "future_negative_prices"),
    ]

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
