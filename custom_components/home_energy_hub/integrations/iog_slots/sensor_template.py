"""Template-based sensor entities for IOG-Ohme Slots that match original template behavior."""

import logging
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass, RestoreSensor
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util import dt as dt_util

_LOGGER = logging.getLogger(__name__)

class IogSlotsTemplateSensor(RestoreSensor):
    """Sensor for IOG-Ohme Slots that exactly matches template sensor behavior."""

    def __init__(self, config_entry: ConfigEntry, slot_type: str, name: str, unique_id_suffix: str) -> None:
        """Initialize the template sensor."""
        self._config_entry = config_entry
        self._slot_type = slot_type
        self._attr_name = name
        self._attr_unique_id = f"iog_slots_template_{config_entry.entry_id}_{unique_id_suffix}"
        self._attr_device_class = SensorDeviceClass.DURATION
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_native_unit_of_measurement = "min"
        self._attr_should_poll = False
        
        # Get configuration
        self._name_prefix = config_entry.data.get("name_prefix", "IOG")
        self._enable_charge_mode_check = config_entry.data.get("enable_charge_mode_check", True)
        self._charge_mode_entity = config_entry.data.get("charge_mode_entity", "select.ohme_home_pro_charge_mode")
        self._power_entity = config_entry.data.get("power_entity", "sensor.ohme_home_pro_power")
        self._charge_mode_value = config_entry.data.get("charge_mode_value", "smart_charge")
        self._power_threshold = config_entry.data.get("power_threshold", 1500)
        self._activation_threshold = config_entry.data.get("activation_threshold", 30)
        self._update_interval = config_entry.data.get("update_interval", 30)
        
        # State tracking with session accumulation
        self._state = 0.0
        self._last_update = None
        self._current_session_start = None
        self._accumulated_minutes = 0.0
        self._current_slot_start = None
        
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
        
        # Restore previous state and attributes
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state not in (None, "unknown", "unavailable"):
                try:
                    self._state = float(last_state.state)
                except (ValueError, TypeError):
                    _LOGGER.warning("Could not restore state for %s", self.entity_id)
            
            # Restore accumulated minutes and slot info from attributes
            if last_state.attributes:
                self._accumulated_minutes = last_state.attributes.get("accumulated_minutes", 0.0)
                current_slot_start_str = last_state.attributes.get("current_slot_start")
                
                # Restore current slot start if we have it
                if current_slot_start_str:
                    try:
                        self._current_slot_start = dt_util.parse_datetime(current_slot_start_str)
                    except (ValueError, TypeError):
                        self._current_slot_start = None
                
                _LOGGER.debug("Restored state for %s: state=%.2f, accumulated=%.2f, slot_start=%s",
                             self.entity_id, self._state, self._accumulated_minutes, self._current_slot_start)
        
        # Set up update interval to match template behavior
        self._update_interval = timedelta(seconds=self._update_interval)
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._async_update_template, self._update_interval
            )
        )
        
        # Initial update
        await self._async_update_template()

    async def _async_update_template(self, now=None) -> None:
        """Update the sensor state using exact template logic."""
        try:
            current_time = dt_util.now()
            
            # Calculate slot boundaries exactly like the template
            if self._slot_type == "slot_00":
                slot_start = current_time.replace(minute=0, second=0, microsecond=0)
                slot_end = current_time.replace(minute=29, second=59, microsecond=999999)
            else:  # slot_30
                slot_start = current_time.replace(minute=30, second=0, microsecond=0)
                slot_end = current_time.replace(minute=59, second=59, microsecond=999999)
            
            # Check if we're in the current sensor's slot
            in_current_slot = slot_start <= current_time <= slot_end
            
            # Check if we're actively charging (exact template logic)
            is_active_charging = await self._check_charging_conditions()
            
            # Check if we've entered a new slot
            if self._current_slot_start != slot_start:
                _LOGGER.debug("Slot %s: New slot detected, resetting accumulated time", self._slot_type)
                self._accumulated_minutes = 0.0
                self._current_slot_start = slot_start
                self._current_session_start = None
            
            # Apply exact template logic with proper slot isolation and accumulation
            if is_active_charging:
                if in_current_slot:
                    # Actively charging AND in this sensor's slot
                    if self._current_session_start is None:
                        # Starting a new charging session
                        self._current_session_start = current_time
                        _LOGGER.debug("Slot %s: Starting new charging session", self._slot_type)
                    
                    # Calculate current session time and add to accumulated
                    current_session_minutes = (current_time - self._current_session_start).total_seconds() / 60.0
                    self._state = self._accumulated_minutes + current_session_minutes
                    _LOGGER.debug("Slot %s: Active charging, accumulated %.2f minutes (session: %.2f, total: %.2f)",
                                 self._slot_type, current_session_minutes, self._accumulated_minutes, self._state)
                else:
                    # Actively charging but NOT in this sensor's slot - reset to 0
                    self._state = 0.0
                    self._current_session_start = None
                    _LOGGER.debug("Slot %s: Active charging but outside slot, reset to 0", self._slot_type)
            else:
                # Not actively charging
                if self._current_session_start is not None:
                    # Charging just stopped - accumulate the session
                    session_duration = (current_time - self._current_session_start).total_seconds() / 60.0
                    self._accumulated_minutes += session_duration
                    self._current_session_start = None
                    _LOGGER.debug("Slot %s: Charging stopped, added %.2f minutes (total: %.2f)",
                                 self._slot_type, session_duration, self._accumulated_minutes)
                
                if in_current_slot:
                    # Within this sensor's slot but not charging - show accumulated time
                    self._state = self._accumulated_minutes
                    _LOGGER.debug("Slot %s: In slot but not charging, accumulated: %.2f", self._slot_type, self._state)
                else:
                    # Outside this sensor's slot time - reset to 0
                    self._state = 0.0
                    _LOGGER.debug("Slot %s: Outside slot, reset to 0", self._slot_type)
            
            self._last_update = current_time
            self.async_write_ha_state()
            
        except Exception as err:
            _LOGGER.error("Error updating IOG Slots template sensor %s: %s", self.entity_id, err)

    async def _check_charging_conditions(self) -> bool:
        """Check if charging conditions are met (exact template logic)."""
        charge_mode_state = self.hass.states.get(self._charge_mode_entity)
        power_state = self.hass.states.get(self._power_entity)
        
        # Check charge mode (case-insensitive) only if enabled
        if self._enable_charge_mode_check:
            charge_mode_ok = (
                charge_mode_state is not None and
                charge_mode_state.state.lower() == self._charge_mode_value.lower()
            )
            _LOGGER.debug("Slot %s: Charge mode check enabled, result: %s", self._slot_type, charge_mode_ok)
        else:
            charge_mode_ok = True
            _LOGGER.debug("Slot %s: Charge mode check disabled, skipping", self._slot_type)
        
        # Check power threshold
        power_ok = False
        if charge_mode_ok and power_state is not None and self._is_numeric(power_state.state):
            power_value = float(power_state.state)
            unit_of_measurement = power_state.attributes.get("unit_of_measurement", "").lower()
            
            if unit_of_measurement in ["kw", "kilowatt", "kilowatts"]:
                # Convert user's watt threshold to kW for comparison
                power_threshold_kw = self._power_threshold / 1000.0
                power_ok = power_value >= power_threshold_kw
                _LOGGER.debug("Slot %s: Power check (kW): %.2f kW >= %.2f kW = %s",
                             self._slot_type, power_value, power_threshold_kw, power_ok)
            else:
                # Assume watts or same unit as user input
                power_ok = power_value >= self._power_threshold
                _LOGGER.debug("Slot %s: Power check (W): %.2f W >= %.2f W = %s",
                             self._slot_type, power_value, self._power_threshold, power_ok)
        else:
            _LOGGER.debug("Slot %s: Power state unavailable or not numeric", self._slot_type)
        
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
        return self._state

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra state attributes."""
        return {
            "slot_type": self._slot_type,
            "enable_charge_mode_check": self._enable_charge_mode_check,
            "charge_mode_entity": self._charge_mode_entity,
            "power_entity": self._power_entity,
            "charge_mode_value": self._charge_mode_value,
            "power_threshold": self._power_threshold,
            "activation_threshold": self._activation_threshold,
            "last_update": self._last_update.isoformat() if self._last_update else None,
            "accumulated_minutes": round(self._accumulated_minutes, 2),
            "current_slot_start": self._current_slot_start.isoformat() if self._current_slot_start else None,
        }