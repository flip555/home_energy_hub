"""Sensor entities for Seplos V3."""

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from ...const import DOMAIN, CONF_NAME_PREFIX
import logging


# V3 sensor definitions: (key, display_name, unit, device_class, state_class)
V3_SENSORS = [
    ("pack_voltage", "Pack Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    ("current", "Current", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    ("remaining_capacity", "Remaining Capacity", "Ah", None, SensorStateClass.MEASUREMENT),
    ("total_capacity", "Total Capacity", "Ah", None, SensorStateClass.MEASUREMENT),
    ("total_discharge_capacity", "Total Discharge Capacity", "Ah", None, SensorStateClass.TOTAL_INCREASING),
    ("soc", "State of Charge", "%", SensorDeviceClass.BATTERY, SensorStateClass.MEASUREMENT),
    ("soh", "State of Health", "%", None, SensorStateClass.MEASUREMENT),
    ("cycle", "Cycle Count", None, None, SensorStateClass.TOTAL_INCREASING),
    ("avg_cell_voltage", "Average Cell Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    ("avg_cell_temperature", "Average Cell Temperature", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    ("max_cell_voltage", "Max Cell Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    ("min_cell_voltage", "Min Cell Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT),
    ("max_cell_temperature", "Max Cell Temperature", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    ("min_cell_temperature", "Min Cell Temperature", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT),
    ("max_discharge_current", "Max Discharge Current", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
    ("max_charge_current", "Max Charge Current", "A", SensorDeviceClass.CURRENT, SensorStateClass.MEASUREMENT),
]

# Cell voltage sensors (16 cells)
for i in range(1, 17):
    V3_SENSORS.append((f"cell{i}_voltage", f"Cell {i} Voltage", "V", SensorDeviceClass.VOLTAGE, SensorStateClass.MEASUREMENT))

# Cell temperature sensors (4 sensors)
for i in range(1, 5):
    V3_SENSORS.append((f"cell_temperature_{i}", f"Cell Temperature {i}", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT))

# Environment & power temperature
V3_SENSORS.append(("environment_temperature", "Environment Temperature", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT))
V3_SENSORS.append(("power_temperature", "Power Temperature", "°C", SensorDeviceClass.TEMPERATURE, SensorStateClass.MEASUREMENT))


class SeplosV3Sensor(CoordinatorEntity, SensorEntity):
    """Sensor for Seplos V3 data."""

    def __init__(self, coordinator, key: str, config_entry: ConfigEntry, sensor_def: tuple) -> None:
        super().__init__(coordinator)
        self._key = key
        self.config_entry = config_entry

        name_prefix = config_entry.data.get(CONF_NAME_PREFIX, "Seplos BMS V3")
        battery_address = config_entry.data.get("battery_address", "0x00")
        sensor_display_name = sensor_def[1]

        self._attr_name = f"{name_prefix} {battery_address} {sensor_display_name}"
        self._attr_unique_id = f"seplos_v3_{config_entry.entry_id}_{key}"
        self._attr_native_unit_of_measurement = sensor_def[2]
        self._attr_device_class = sensor_def[3]
        self._attr_state_class = sensor_def[4]

        self._attr_device_info = DeviceInfo(
            identifiers={("home_energy_hub", f"seplos_v3_{config_entry.entry_id}")},
            name=f"{name_prefix}",
            manufacturer="Seplos",
            model="V3 BMS",
            sw_version="Unknown",
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.coordinator.data.get(self._key)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Seplos V3 sensors from a config entry."""
    _LOGGER = logging.getLogger(__name__)
    _LOGGER.debug("Setting up Seplos V3 sensors for entry: %s", entry.entry_id)
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensor_defs = {s[0]: s for s in V3_SENSORS}
    sensors = [SeplosV3Sensor(coordinator, key, entry, sensor_defs[key]) for key in coordinator.data if key in sensor_defs]

    _LOGGER.info("Created %d V3 sensors", len(sensors))
    async_add_entities(sensors)
