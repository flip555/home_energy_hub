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
from ..const import (
    NAME,
    DOMAIN,
    VERSION,
    ATTRIBUTION,
)

_LOGGER = logging.getLogger(__name__)

async def HomeEnergyHubGlobalSettings(hass, region, entry, async_add_entities):
    name_tariff = "None"
    options_flow = entry.get("options_flow")

    async def async_update_data():
        return { "premium_services": False }

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
    setting_sensors = [
        OctopusSensor(coordinator, f"Global Settings - Premium Services", "premium_services", "", ""),
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
        return self._icon

    @property
    def state(self):
        return self.coordinator.data[self._time_key]

    @property
    def unit_of_measurement(self):
        return self._unit

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = {}
        if self._time_key == 'full_json':
            attributes = self.coordinator.data['full_json']
        if self._time_key == 'future_negative_prices':
            attributes = self.coordinator.data['future_negative_prices']
        return None
