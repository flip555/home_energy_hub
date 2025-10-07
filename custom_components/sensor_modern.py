"""Modern sensor entities for IOG-Ohme Slots using HA 2025.01+ features."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass, RestoreSensor
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

class IogSlotsModernSensor(RestoreSensor):
    """Modern sensor for IOG-Ohme Slots with event-based tracking and persistence."""

    def __init__(self, config_entry: ConfigEntry, slot_type: str, name: str, unique_id_suffix: str) -> None:
        """Initialize the modern sensor."""
        self._config_entry = config_entry
        self._slot_type = slot_type
        self._attr_name = name
        self._attr_unique_id = f"iog_slots_modern_{config_entry.entry_id}_{unique_id_suffix}"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "minutes"
        self._attr_should_poll = False
        
        # Get configuration
        self._name_prefix = config_entry.data.get("name_prefix", "IOG")
        self._charge_mode_entity = config_entry.data.get("charge_mode_entity", "select.ohme_home_pro_charge_mode")
        self._power_entity = config_entry.data.get("power_entity", "sensor.ohme_home_pro_power")
        self._charge_mode_value = config_entry.data.get("charge_mode_value", "smart_charge")
        self._power_threshold = config_entry.data.get("power_threshold", 1500)
        self._update_interval = config_entry.data.get("update_interval", 30)
        
        # State tracking with persistence
        self._state = 0.0
        self._is_active_charging = False
        self._current_session_start: Optional[datetime] = None
        self._accumulated_minutes = 0.0
        self._current_slot_start: Optional[datetime] = None
        self._last_update = None
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={("home_energy_hub", f"iog_slots_{config_entry.entry_id}")},
            name=f"{self._name_prefix} Slots",
            manufacturer="IOG-Ohme",
            model="Charging Slot Tracker",
            sw_version="v2.0",
        )

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        
        # Restore previous state
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state not in (None, "unknown", "unavailable"):
                try:
                    self._state = float(last_state.state)
                    self._accumulated_minutes = self._state
                except (ValueError, TypeError):
                    _LOGGER.warning("Could not restore state for %s", self.entity_id)
            
            # Restore attributes
            if last_state.attributes:
                self._is_active_charging = last_state.attributes.get("is_active_charging", False)
                self._accumulated_minutes = last_state.attributes.get("accumulated_minutes", 0.0)
                
                # Restore session start if we were active
                if self._is_active_charging:
                    session_start_str = last_state.attributes.get("current_session_start")
                    if session_start_str:
                        try:
                            self._current_session_start = dt_util.parse_datetime(session_start_str)
                        except (ValueError, TypeError):
                            self._current_session_start = None
        
        # Set up state change listeners for reactive updates
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._charge_mode_entity, self._power_entity],
                self._async_entity_state_changed
            )
        )
        
        # Set up periodic updates for slot boundary checks
        self._update_interval = timedelta(seconds=self._update_interval)
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._async_update_slot_state, self._update_interval
            )
        )
        
        # Initial update
        await self._async_update_slot_state()

    @callback
    async def _async_entity_state_changed(self, event):
        """Handle state changes of monitored entities."""
        _LOGGER.debug("State change detected for %s", event.data.get("entity_id"))
        await self._async_update_slot_state()

    async def _async_update_slot_state(self, now=None) -> None:
        """Update the sensor state based on current slot and charging status."""
        try:
            current_time = dt_util.now()
            
            # Calculate current slot boundaries
            if self._slot_type == "slot_00":
                slot_start = current_time.replace(minute=0, second=0, microsecond=0)
                slot_end = current_time.replace(minute=29, second=59, microsecond=999999)
            else:  # slot_30
                slot_start = current_time.replace(minute=30, second=0, microsecond=0)
                slot_end = current_time.replace(minute=59, second=59, microsecond=999999)
            
            # Check if we're in a new slot
            if self._current_slot_start != slot_start:
                _LOGGER.debug("New slot detected for %s, resetting accumulated time", self._slot_type)
                self._accumulated_minutes = 0.0
                self._current_slot_start = slot_start
                self._current_session_start = None
                self._is_active_charging = False
            
            # Check current charging status
            is_charging = await self._check_charging_conditions()
            
            # Handle charging state changes
            if is_charging and not self._is_active_charging:
                # Charging just started
                self._current_session_start = current_time
                self._is_active_charging = True
                _LOGGER.debug("Charging started in slot %s", self._slot_type)
            
            elif not is_charging and self._is_active_charging:
                # Charging just stopped - accumulate the session
                if self._current_session_start:
                    session_duration = (current_time - self._current_session_start).total_seconds() / 60.0
                    self._accumulated_minutes += session_duration
                    _LOGGER.debug("Charging stopped in slot %s, added %.2f minutes (total: %.2f)", 
                                 self._slot_type, session_duration, self._accumulated_minutes)
                self._current_session_start = None
                self._is_active_charging = False
            
            # Calculate current state
            if self._is_active_charging and self._current_session_start:
                # Currently charging - add current session to accumulated
                current_session_minutes = (current_time - self._current_session_start).total_seconds() / 60.0
                self._state = self._accumulated_minutes + current_session_minutes
            else:
                # Not currently charging - just show accumulated
                self._state = self._accumulated_minutes
            
            # Ensure we don't exceed slot duration
            max_slot_minutes = 30.0
            if self._state > max_slot_minutes:
                self._state = max_slot_minutes
            
            self._last_update = current_time
            self.async_write_ha_state()
            
        except Exception as err:
            _LOGGER.error("Error updating modern IOG Slots sensor %s: %s", self.entity_id, err)

    async def _check_charging_conditions(self) -> bool:
        """Check if charging conditions are met."""
        charge_mode_state = self.hass.states.get(self._charge_mode_entity)
        power_state = self.hass.states.get(self._power_entity)
        
        # Check charge mode (case-insensitive)
        charge_mode_ok = (
            charge_mode_state is not None and 
            charge_mode_state.state.lower() == self._charge_mode_value.lower()
        )
        
        # Check power threshold
        power_ok = False
        if charge_mode_ok and power_state is not None and self._is_numeric(power_state.state):
            power_value = float(power_state.state)
            unit_of_measurement = power_state.attributes.get("unit_of_measurement", "").lower()
            
            if unit_of_measurement in ["kw", "kilowatt", "kilowatts"]:
                # Convert user's watt threshold to kW for comparison
                power_threshold_kw = self._power_threshold / 1000.0
                power_ok = power_value >= power_threshold_kw
            else:
                # Assume watts or same unit as user input
                power_ok = power_value >= self._power_threshold
        
        return charge_mode_ok and power_ok

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
        return round(self._state, 2)

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
            "accumulated_minutes": round(self._accumulated_minutes, 2),
            "current_session_start": self._current_session_start.isoformat() if self._current_session_start else None,
            "current_slot_start": self._current_slot_start.isoformat() if self._current_slot_start else None,
            "last_update": self._last_update.isoformat() if self._last_update else None,
        }