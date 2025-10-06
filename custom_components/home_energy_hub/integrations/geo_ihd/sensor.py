"""Sensor entities for GEO IHD."""

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass, RestoreSensor
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

class GeoIhdSensor(CoordinatorEntity, RestoreSensor):
    """Sensor for GEO IHD data."""

    def __init__(self, coordinator, key: str, entry_id: str, username: str) -> None:
        super().__init__(coordinator)
        sensor_info = coordinator.data[key]
        self._key = key
        self._attr_name = sensor_info['name']
        self._attr_unique_id = sensor_info['unique_id']
        self._attr_unit_of_measurement = sensor_info['unit']
        
        # Map string device classes to enum values
        device_class_map = {
            "power": SensorDeviceClass.POWER,
            "energy": SensorDeviceClass.ENERGY,
            "gas": SensorDeviceClass.GAS,
        }
        
        # Map string state classes to enum values
        state_class_map = {
            "measurement": SensorStateClass.MEASUREMENT,
            "total_increasing": SensorStateClass.TOTAL_INCREASING,
        }
        
        if sensor_info['device_class'] and sensor_info['device_class'] in device_class_map:
            self._attr_device_class = device_class_map[sensor_info['device_class']]
        
        if sensor_info['state_class'] and sensor_info['state_class'] in state_class_map:
            self._attr_state_class = state_class_map[sensor_info['state_class']]
            
        self._attr_icon = sensor_info['icon']
        # Set device info
        device_type = "electric" if "electric" in key else "gas"
        self._attr_device_info = DeviceInfo(
            identifiers={("home_energy_hub", "geo_ihd", entry_id, username, device_type)},
        )

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data[self._key]['state']