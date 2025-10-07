"""Binary sensor for IOG-Ohme Slots activation tracking."""

import logging
from datetime import datetime, timedelta

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

class IogSlotsActivationBinarySensor(BinarySensorEntity):
    """Binary sensor for IOG-Ohme Slots activation state."""

    def __init__(self, config_entry: ConfigEntry, slot_00_sensor, slot_30_sensor) -> None:
        """Initialize the activation binary sensor."""
        self._config_entry = config_entry
        self._slot_00_sensor = slot_00_sensor
        self._slot_30_sensor = slot_30_sensor
        
        self._attr_name = f"{config_entry.data.get('name_prefix', 'IOG')} Cheap Slot Activation"
        self._attr_unique_id = f"iog_slots_activation_{config_entry.entry_id}"
        self._attr_device_class = BinarySensorDeviceClass.RUNNING
        self._attr_should_poll = False
        
        # Get configuration
        self._name_prefix = config_entry.data.get("name_prefix", "IOG")
        self._activation_threshold = config_entry.data.get("activation_threshold", 30)
        
        # State tracking
        self._is_active = False
        self._current_slot = None
        self._current_duration = 0.0
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={("home_energy_hub", f"iog_slots_{config_entry.entry_id}")},
            name=f"{self._name_prefix} Slots",
            manufacturer="IOG-Ohme",
            model="Charging Slot Tracker",
            sw_version="v1.0",
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        # Set up update interval
        update_interval = self._config_entry.data.get("update_interval", 30)
        self._update_interval = timedelta(seconds=update_interval)
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._async_update_activation, self._update_interval
            )
        )
        
        # Initial update
        await self._async_update_activation()

    async def _async_update_activation(self, now=None) -> None:
        """Update the activation state based on current slot and duration."""
        try:
            current_time = dt_util.now()
            
            # Determine current slot
            if current_time.minute < 30:
                current_slot = "slot_00"
                slot_start = current_time.replace(minute=0, second=0, microsecond=0)
                slot_end = current_time.replace(minute=29, second=59, microsecond=999999)
            else:
                current_slot = "slot_30"
                slot_start = current_time.replace(minute=30, second=0, microsecond=0)
                slot_end = current_time.replace(minute=59, second=59, microsecond=999999)
            
            # Check if we're in the current slot
            in_current_slot = slot_start <= current_time <= slot_end
            
            # Get duration from the appropriate sensor
            if current_slot == "slot_00":
                current_duration = self._slot_00_sensor.state
            else:
                current_duration = self._slot_30_sensor.state
            
            # Convert duration to float if it's a string
            if isinstance(current_duration, str):
                try:
                    current_duration = float(current_duration)
                except (ValueError, TypeError):
                    current_duration = 0.0
            
            # Update state
            self._current_slot = current_slot
            self._current_duration = current_duration
            
            # Check activation condition
            if in_current_slot and current_duration >= self._activation_threshold:
                self._is_active = True
                _LOGGER.debug("Slot activation: %s reached %.2f min (threshold: %.2f min)", 
                             current_slot, current_duration, self._activation_threshold)
            else:
                self._is_active = False
                _LOGGER.debug("Slot activation: %s at %.2f min (threshold: %.2f min) - not active", 
                             current_slot, current_duration, self._activation_threshold)
            
            self.async_write_ha_state()
            
        except Exception as err:
            _LOGGER.error("Error updating IOG Slots activation sensor %s: %s", self.entity_id, err)

    @property
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        return self._is_active

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "current_slot": self._current_slot,
            "current_duration": round(self._current_duration, 2),
            "activation_threshold": self._activation_threshold,
        }