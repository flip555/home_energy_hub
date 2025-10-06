"""Sensor entities for Seplos V2."""

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from ...const import DOMAIN, SENSOR_UNITS, CONF_BATTERY_ADDRESS, CONF_NAME_PREFIX

class SeplosV2Sensor(CoordinatorEntity, SensorEntity):
    """Sensor for Seplos V2 data."""

    def __init__(self, coordinator, key: str, config_entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._key = key
        self.config_entry = config_entry
        
        # Get configuration
        name_prefix = config_entry.data.get(CONF_NAME_PREFIX, "Seplos BMS HA")
        battery_address = config_entry.data.get(CONF_BATTERY_ADDRESS, "0x00")
        
        # Set name and unique_id to match exact previous format
        sensor_display_name = self._get_sensor_name(key)
        self._attr_name = f"{name_prefix} {battery_address} {sensor_display_name}"
        
        # Convert name prefix to lowercase with underscores for unique_id
        unique_id_prefix = name_prefix.lower().replace(' ', '_')
        # Convert key to snake_case for unique_id (e.g., "balancerActiveCell1" -> "balancer_active_cell_1")
        snake_case_key = self._camel_to_snake(key)
        
        # Determine device type based on whether key ends with "_settings"
        if key.endswith('_settings'):
            # Settings device - use settings identifier and unique_id
            device_identifier = f"seplos_v2_{config_entry.entry_id}_{battery_address}_settings"
            # Remove "_settings" suffix for the actual sensor key in unique_id
            sensor_base_key = key[:-10]  # Remove "_settings" suffix (10 characters)
            snake_case_sensor_key = self._camel_to_snake(sensor_base_key)
            self._attr_unique_id = f"{unique_id_prefix}_{battery_address}_{snake_case_sensor_key}"
        else:
            # BMS device - use original identifier and unique_id
            device_identifier = f"seplos_v2_{config_entry.entry_id}_{battery_address}"
            self._attr_unique_id = f"{unique_id_prefix}_{battery_address}_{snake_case_key}"
            
        # Set device info to link to the pre-registered device with full details
        if key.endswith('_settings'):
            device_name = f"{name_prefix} {battery_address} Settings"
            model = "V2 Settings"
        else:
            device_name = f"{name_prefix} {battery_address} BMS"
            model = "V2 BMS"
            
        self._attr_device_info = DeviceInfo(
            identifiers={("home_energy_hub", device_identifier)},
            name=device_name,
            manufacturer="Seplos",
            model=model,
            sw_version=self.coordinator.data.get("software_version", "Unknown"),
        )
        
        # Set device class and state class based on sensor type
        self._set_sensor_attributes(key)

    def _camel_to_snake(self, name: str) -> str:
        """Convert camelCase to snake_case."""
        import re
        # Insert underscores before capital letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        # Insert underscores between letters and numbers
        s3 = re.sub('([a-zA-Z])([0-9])', r'\1_\2', s2)
        s4 = re.sub('([0-9])([a-zA-Z])', r'\1_\2', s3)
        # Convert to lowercase
        return s4.lower()

    def _get_sensor_name(self, base_key: str) -> str:
        """Get human-readable sensor name."""
        # Remove _settings suffix for display names
        key = base_key[:-9] if base_key.endswith('_settings') else base_key
        
        name_mapping = {
            "cellsCount": "Number of Cells",
            "resCap": "Residual Capacity",
            "capacity": "Capacity",
            "soc": "State of Charge",
            "ratedCapacity": "Rated Capacity",
            "cycles": "Cycles",
            "soh": "State of Health",
            "portVoltage": "Port Voltage",
            "current": "Current",
            "voltage": "Voltage",
            "battery_watts": "Battery Watts",
            "full_charge_watts": "Full Charge Watts",
            "full_charge_amps": "Full Charge Amps",
            "remaining_watts": "Remaining Watts",
            "capacity_watts": "Capacity Watts",
            "highest_cell_voltage": "Highest Cell Voltage",
            "highest_cell_number": "Cell Number of Highest Voltage",
            "lowest_cell_voltage": "Lowest Cell Voltage",
            "lowest_cell_number": "Cell Number of Lowest Voltage",
            "cell_difference": "Cell Voltage Difference",
            "power_temperature": "Power Temperature",
            "environment_temperature": "Environment Temperature",
            "device_name": "Device Name",
            "software_version": "Software Version",
            "manufacturer_name": "Manufacturer Name",
        }
        
        # Handle cell voltage sensors - match old naming format
        if key.startswith("cell_") and key.endswith("_voltage"):
            cell_num = key.split("_")[1]
            return f"Cell Voltage {cell_num}"
            
        # Handle cell temperature sensors
        if key.startswith("cell_temperature_"):
            cell_num = key.split("_")[2]
            return f"Cell Temperature {cell_num}"
            
        # Handle alarm and state sensors - convert from camelCase to proper spacing
        if any(x in key.lower() for x in ["alarm", "state", "active", "equilibrium", "disconnection"]):
            # Convert camelCase to space-separated words
            spaced_name = self._camel_to_snake(key).replace('_', ' ')
            return spaced_name.title()
            
        # Add customNumber to mapping
        if key == "customNumber":
            return "Custom Number"
            
        return name_mapping.get(key, key.replace("_", " ").title())

    def _set_sensor_attributes(self, key: str) -> None:
        """Set sensor attributes based on sensor type."""
        # List of alarm and state sensor keys that return string values
        alarm_state_keys = {
            "currentAlarm", "voltageAlarm", "alarmEvent0", "alarmEvent1", "alarmEvent2",
            "alarmEvent3", "alarmEvent4", "alarmEvent5", "alarmEvent6", "alarmEvent7",
            "onOffState", "equilibriumState0", "equilibriumState1", "systemState",
            "disconnectionState0", "disconnectionState1"
        }
        
        # Skip device class and state class for alarm and state sensors (they return strings)
        if key in alarm_state_keys:
            # These sensors return string values, so no device class or state class
            return
            
        # Set device class for numeric sensors
        if "temperature" in key:
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        elif "voltage" in key and "cell" in key:
            self._attr_device_class = SensorDeviceClass.VOLTAGE
        elif "voltage" in key:
            self._attr_device_class = SensorDeviceClass.VOLTAGE
        elif "current" in key:
            self._attr_device_class = SensorDeviceClass.CURRENT
        elif "power" in key or "watts" in key:
            self._attr_device_class = SensorDeviceClass.POWER
        elif "soc" in key:
            self._attr_device_class = SensorDeviceClass.BATTERY
        elif "capacity" in key and "ah" in key.lower():
            self._attr_device_class = SensorDeviceClass.ENERGY_STORAGE
        
        # Set state class for numeric sensors
        if any(x in key for x in ["voltage", "current", "power", "temperature", "soc", "capacity"]):
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif "cycles" in key:
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self.coordinator.data.get(self._key)
        # Handle cell voltage sensors that now return dict with state and attributes
        if isinstance(data, dict) and 'state' in data:
            return data['state']
        return data

    @property
    def extra_state_attributes(self):
        """Return extra state attributes for the sensor."""
        data = self.coordinator.data.get(self._key)
        # Handle cell voltage sensors that have attributes
        if isinstance(data, dict) and 'attributes' in data:
            return data['attributes']
        return None

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        return SENSOR_UNITS.get(self._key)

import logging

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Seplos V2 sensors from a config entry."""
    _LOGGER.debug("Setting up Seplos V2 sensors for entry: %s", entry.entry_id)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Log all available keys from coordinator for debugging
    _LOGGER.debug("=== SENSOR SETUP DEBUG ===")
    _LOGGER.debug("All coordinator data keys: %s", sorted(list(coordinator.data.keys())))
    
    # Filter out binary sensor keys
    sensor_keys = [key for key in coordinator.data.keys() if not key.startswith('balancerActiveCell')]
    _LOGGER.debug("Filtered sensor keys: %s", sorted(sensor_keys))
    
    # Create sensors for filtered data keys, split into BMS and Settings devices
    sensors = []
    bms_count = 0
    settings_count = 0
    
    # Identify settings keys by "_settings" suffix
    settings_keys = [key for key in sensor_keys if key.endswith('_settings')]
    
    for key in sensor_keys:
        # Pass the original key (with or without _settings) to the sensor
        # The sensor will determine device type based on the key suffix
        if key.endswith('_settings'):
            settings_count += 1
        else:
            bms_count += 1
        
        # Create sensor with the original key (it will handle device assignment)
        sensor = SeplosV2Sensor(coordinator, key, entry)
        sensors.append(sensor)
    
    _LOGGER.info("Created %d BMS sensors and %d Settings sensors", bms_count, settings_count)
    
    async_add_entities(sensors)