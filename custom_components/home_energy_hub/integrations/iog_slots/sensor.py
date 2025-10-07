"""Sensor entities for IOG-Ohme Slots."""

import logging
from datetime import datetime, timedelta
import math

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

class IogSlotsSensor(SensorEntity):
    """Sensor for IOG-Ohme Slots duration tracking."""

    def __init__(self, config_entry: ConfigEntry, slot_type: str, name: str, unique_id_suffix: str) -> None:
        """Initialize the sensor."""
        self._config_entry = config_entry
        self._slot_type = slot_type
        self._attr_name = name
        self._attr_unique_id = f"iog_slots_{config_entry.entry_id}_{unique_id_suffix}"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "minutes"
        self._attr_should_poll = False
        
        # Get configuration
        self._name_prefix = config_entry.data.get("name_prefix", "IOG")
        self._charge_mode_entity = config_entry.data.get("charge_mode_entity", "select.ohme_home_pro_charge_mode")
        self._power_entity = config_entry.data.get("power_entity", "sensor.ohme_home_pro_power")
        self._charge_mode_value = config_entry.data.get("charge_mode_value", "Smart Charge")
        self._power_threshold = config_entry.data.get("power_threshold", 1500)
        self._update_interval = config_entry.data.get("update_interval", 30)
        
        # State tracking
        self._state = 0.0
        self._last_update = None
        self._is_active_charging = False
        
        # Debug attributes
        self._debug_charge_mode_state = None
        self._debug_power_state = None
        self._debug_power_unit = None
        self._debug_condition_charge_mode = False
        self._debug_condition_power = False
        self._debug_power_threshold_used = None
        self._debug_power_value_used = None
        self._debug_slot_start = None
        self._debug_slot_end = None
        self._debug_in_current_slot = False
        
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
        await super().async_added_to_hass()
        
        # Set up update interval
        self._update_interval = timedelta(seconds=self._update_interval)
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._async_update, self._update_interval
            )
        )
        
        # Initial update
        await self._async_update()

    async def _async_update(self, now=None) -> None:
        """Update the sensor state."""
        try:
            # Get current states
            charge_mode_state = self.hass.states.get(self._charge_mode_entity)
            power_state = self.hass.states.get(self._power_entity)
            
            # Set debug attributes
            self._debug_charge_mode_state = charge_mode_state.state if charge_mode_state else "unavailable"
            self._debug_power_state = power_state.state if power_state else "unavailable"
            self._debug_power_unit = power_state.attributes.get("unit_of_measurement", "unknown") if power_state else "unknown"
            
            # Check if charging is active
            is_active = False
            self._debug_condition_charge_mode = False
            self._debug_condition_power = False
            
            # Make charge mode comparison case-insensitive
            charge_mode_match = (
                charge_mode_state is not None and
                charge_mode_state.state.lower() == self._charge_mode_value.lower()
            )
            
            if charge_mode_match:
                self._debug_condition_charge_mode = True
                if power_state is not None and self._is_numeric(power_state.state):
                    power_value = float(power_state.state)
                    
                    # Check unit of measurement and convert if necessary
                    unit_of_measurement = power_state.attributes.get("unit_of_measurement", "").lower()
                    if unit_of_measurement in ["kw", "kilowatt", "kilowatts"]:
                        # Convert user's watt threshold to kW for comparison
                        power_threshold_kw = self._power_threshold / 1000.0
                        self._debug_condition_power = power_value >= power_threshold_kw
                        self._debug_power_threshold_used = f"{power_threshold_kw} kW"
                        self._debug_power_value_used = f"{power_value} kW"
                        is_active = self._debug_condition_power
                        _LOGGER.debug("Power comparison: %.3f kW >= %.3f kW = %s",
                                     power_value, power_threshold_kw, self._debug_condition_power)
                    else:
                        # Assume watts or same unit as user input
                        self._debug_condition_power = power_value >= self._power_threshold
                        self._debug_power_threshold_used = f"{self._power_threshold} W"
                        self._debug_power_value_used = f"{power_value} W"
                        is_active = self._debug_condition_power
                        _LOGGER.debug("Power comparison: %.1f W >= %.1f W = %s",
                                     power_value, self._power_threshold, self._debug_condition_power)
            
            current_time = dt_util.now()
            
            # Calculate slot boundaries for the current hour
            if self._slot_type == "slot_00":
                start_time = current_time.replace(minute=0, second=0, microsecond=0)
                end_time = current_time.replace(minute=29, second=59, microsecond=999999)
            else:  # slot_30
                start_time = current_time.replace(minute=30, second=0, microsecond=0)
                end_time = current_time.replace(minute=59, second=59, microsecond=999999)
            
            # Check if we're currently in this sensor's slot
            in_current_slot = start_time <= current_time <= end_time
            
            # Debug slot info
            self._debug_slot_start = start_time.isoformat()
            self._debug_slot_end = end_time.isoformat()
            self._debug_in_current_slot = in_current_slot
            
            # Update state based on slot and charging status
            if is_active:
                # Actively charging - count elapsed time from slot start
                elapsed_seconds = (current_time - start_time).total_seconds()
                self._state = round(elapsed_seconds / 60, 2)
                self._is_active_charging = True
                _LOGGER.debug("Slot %s: Active charging, elapsed %.2f minutes", self._slot_type, self._state)
            else:
                # Not actively charging
                self._is_active_charging = False
                
                if in_current_slot:
                    # In slot but not charging - preserve the last recorded state
                    # Only reset to 0 if we don't have a valid previous state
                    if self._state is None or self._state < 0:
                        self._state = 0.0
                    _LOGGER.debug("Slot %s: In slot but not charging, state preserved: %.2f", self._slot_type, self._state)
                else:
                    # Outside of this sensor's slot time - reset to 0
                    self._state = 0.0
                    _LOGGER.debug("Slot %s: Outside slot, reset to 0", self._slot_type)
            
            self._last_update = current_time
            self.async_write_ha_state()
            
        except Exception as err:
            _LOGGER.error("Error updating IOG Slots sensor %s: %s", self.entity_id, err)

    def _is_numeric(self, value: str) -> bool:
        """Check if a string can be converted to float."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "slot_type": self._slot_type,
            "charge_mode_entity": self._charge_mode_entity,
            "power_entity": self._power_entity,
            "charge_mode_value": self._charge_mode_value,
            "power_threshold": self._power_threshold,
            "is_active_charging": self._is_active_charging,
            "last_update": self._last_update.isoformat() if self._last_update else None,
            # Debug attributes
            "debug_charge_mode_state": self._debug_charge_mode_state,
            "debug_power_state": self._debug_power_state,
            "debug_power_unit": self._debug_power_unit,
            "debug_condition_charge_mode": self._debug_condition_charge_mode,
            "debug_condition_power": self._debug_condition_power,
            "debug_power_threshold_used": self._debug_power_threshold_used,
            "debug_power_value_used": self._debug_power_value_used,
            "debug_slot_start": self._debug_slot_start,
            "debug_slot_end": self._debug_slot_end,
            "debug_in_current_slot": self._debug_in_current_slot,
        }