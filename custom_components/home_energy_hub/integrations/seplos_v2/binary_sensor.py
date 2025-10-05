"""Binary sensor entities for Seplos V2."""

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo

from ...const import CONF_NAME_PREFIX, CONF_BATTERY_ADDRESS


class SeplosV2BinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor for Seplos V2 balancing states."""

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
        self._attr_unique_id = f"{unique_id_prefix}_{battery_address}_{snake_case_key}"
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={("home_energy_hub", f"seplos_v2_{config_entry.entry_id}_{battery_address}")},
            name=f"{name_prefix} {battery_address}",
            manufacturer="Seplos",
            model="V2 BMS",
            sw_version=self.coordinator.data.get("software_version", "Unknown"),
        )

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

    def _get_sensor_name(self, key: str) -> str:
        """Get human readable sensor name from key."""
        name_map = {
            "balancerActiveCell1": "Balancer Active Cell 1",
            "balancerActiveCell2": "Balancer Active Cell 2",
            "balancerActiveCell3": "Balancer Active Cell 3",
            "balancerActiveCell4": "Balancer Active Cell 4",
            "balancerActiveCell5": "Balancer Active Cell 5",
            "balancerActiveCell6": "Balancer Active Cell 6",
            "balancerActiveCell7": "Balancer Active Cell 7",
            "balancerActiveCell8": "Balancer Active Cell 8",
            "balancerActiveCell9": "Balancer Active Cell 9",
            "balancerActiveCell10": "Balancer Active Cell 10",
            "balancerActiveCell11": "Balancer Active Cell 11",
            "balancerActiveCell12": "Balancer Active Cell 12",
            "balancerActiveCell13": "Balancer Active Cell 13",
            "balancerActiveCell14": "Balancer Active Cell 14",
            "balancerActiveCell15": "Balancer Active Cell 15",
            "balancerActiveCell16": "Balancer Active Cell 16",
        }
        
        # If not in mapping, convert from camelCase to proper spacing
        if key not in name_map:
            # Convert camelCase to space-separated words
            spaced_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', key)
            # Handle numbers after words
            spaced_name = re.sub(r'([a-zA-Z])(\d)', r'\1 \2', spaced_name)
            # Handle numbers before words
            spaced_name = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', spaced_name)
            return spaced_name.title()
            
        return name_map.get(key, key.replace("_", " ").title())

    @property
    def is_on(self):
        """Return the state of the binary sensor."""
        return self.coordinator.data.get(self._key, False)

    @property
    def icon(self):
        """Return the icon for the binary sensor."""
        return "mdi:battery"