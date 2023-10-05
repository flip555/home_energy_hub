from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.entity_component import EntityComponent

import asyncio
import logging
from datetime import timedelta
from ...const import (
    NAME,
    DOMAIN,
    VERSION,
    ATTRIBUTION,
)

_LOGGER = logging.getLogger(__name__)

# Define the generate_sensors function
async def generate_sensors(hass, bms_type, port, config_battery_address, sensor_prefix, entry, async_add_entities):
    async def async_update_data():
        #Need to generate these, they're all for 0x00 atm .... 42H, 44H, 47H, 51H
        V2_COMMAND_ARRAY = {
            "0x00": ["~20004642E00200FD37\r", "~20004644E00200FD35\r", "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
            "0x01": ["~20004642E00215FD31\r", "~20004644E00200FD35\r", "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
            "0x02": ["~20004642E00200FD37\r", "~20004644E00200FD35\r", "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
            "0x03": ["~20004642E00200FD37\r", "~20004644E00200FD35\r", "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
        }
        _LOGGER.debug("BATTERY PACK SELECTED: %s", config_battery_address)
        commands = V2_COMMAND_ARRAY[config_battery_address]

        telemetry_data_str = await hass.async_add_executor_job(send_serial_command, commands, port)
        battery_address, telemetry, alarms, system_details, protection_settings = extract_data_from_message(telemetry_data_str, True, True, True)
        if battery_address != config_battery_address: 
            _LOGGER.debug("Battery Pack: %s was not found. %s found instead. Skipping", config_battery_address, battery_address)
            pass
        else:
            return battery_address, telemetry, alarms, system_details, protection_settings

    battery_address, telemetry, alarms, system_details, protection_settings = await async_update_data()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="seplos_bms_sensor",
        update_method=async_update_data,
        update_interval=timedelta(seconds=5),  # Define how often to fetch data
    )
    _LOGGER.debug("async_refresh data generate_sensors called")
    await coordinator.async_refresh() 

   
    setting_sensors = [
        SeplosBMSSensorBase(coordinator, port, "soc_ah", "SOC", "Ah", "mdi:gauge", battery_address=battery_address, sensor_prefix=sensor_prefix),
    ]

    # Combine all sensor lists
    sensors = setting_sensors

    async_add_entities(sensors, True)

class SeplosBMSSensorBase(CoordinatorEntity):
    def interpret_alarm(self, event, value):
        flags = ALARM_MAPPINGS.get(event, [])

        if not flags:
            return f"Unknown event: {event}"

        # For other alarm events, interpret them as bit flags
        triggered_alarms = [flag for idx, flag in enumerate(flags) if value is not None and value & (1 << idx)]
        #return ', '.join(str(triggered_alarms)) if triggered_alarms else "No Alarm"

        return ', '.join(str(alarm) for alarm in triggered_alarms) if triggered_alarms else "No Alarm"

    def __init__(self, coordinator, port, attribute, name, unit=None, icon=None, battery_address=None, sensor_prefix=None):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._port = port
        self._attribute = attribute
        self._name = name
        self._unit = unit
        self._icon = icon
        self._battery_address = battery_address
        self._sensor_prefix = sensor_prefix

    @property
    def name(self):
        """Return the name of the sensor."""
        prefix = f"{self._sensor_prefix} - {self._battery_address} -"
        return f"{prefix} {self._name}"
        
    @property
    def unique_id(self):
        """Return a unique ID for this entity."""
        prefix = f"{self._sensor_prefix}_{self._battery_address}_"
        return f"{prefix}{self._name}"

    @property
    def state(self):
        """Return the state of the sensor."""
        if not self._attribute:  # Check if attribute is None or empty
            return super().state

        base_attribute = self._attribute.split('[')[0] if '[' in self._attribute else self._attribute

        value = None
        if isinstance(self.coordinator.data, tuple):
            battery_address_data, telemetry_data, alarms_data, system_details_data, protection_settings_data = self.coordinator.data
            value = self.get_value(telemetry_data) or self.get_value(alarms_data) or self.get_value(system_details_data) or self.get_value(protection_settings_data)
        else:
            value = self.get_value(self.coordinator.data)
            
        # Interpret the value for alarm sensors
        if base_attribute in ALARM_ATTRIBUTES:
            interpreted_value = str(self.interpret_alarm(base_attribute, value))
            _LOGGER.debug("Interpreted value for %s: %s", base_attribute, interpreted_value)
            return interpreted_value   
        if value is None or value == '':
            if base_attribute == 'current':
                _LOGGER.debug("Current seems to be None, setting to 0.00 to fix HA reporting as unknown")
                return 0.00
            else:
                _LOGGER.warning("No data found in telemetry or alarms for %s", self._name)
                return None
                


        _LOGGER.debug("Sensor state for %s: %s", self._name, value)
        return value


    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        if self._attribute in ALARM_ATTRIBUTES:
            return None  # No unit for alarms
        if self._attribute in SYSTEM_ATTRIBUTES:
            return None  # No unit for alarms
        return self._unit

    def get_value(self, telemetry_data):
        """Retrieve the value based on the attribute."""
        # If the attribute name contains a bracket, it's trying to access a list
        if '[' in self._attribute and ']' in self._attribute:
            attr, index = self._attribute.split('[')
            index = int(index.rstrip(']'))
            # Check if the attribute exists in telemetry_data
            if hasattr(telemetry_data, attr):
                list_data = getattr(telemetry_data, attr)
                if index < len(list_data):
                    value = list_data[index]
                    return value
        else:
            value = getattr(telemetry_data, self._attribute, None)
            return value

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon