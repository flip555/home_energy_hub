"""IOG-Ohme Slots integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .sensor import IogSlotsSensor
from .binary_sensor import IogSlotsActivationBinarySensor

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up IOG-Ohme Slots sensors."""
    device_registry = dr.async_get(hass)
    
    # Get configuration
    name_prefix = entry.data.get("name_prefix", "IOG")
    
    # Register device
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("home_energy_hub", f"iog_slots_{entry.entry_id}")},
        manufacturer="IOG-Ohme",
        name=f"{name_prefix} Slots",
        model="Charging Slot Tracker",
        sw_version="v1.0",
    )
    
    # Create sensors using the fixed implementation
    slot_00_sensor = IogSlotsSensor(entry, "slot_00", f"{name_prefix} Active Charging Duration Slot 00", "iog_active_charging_duration_slot_00")
    slot_30_sensor = IogSlotsSensor(entry, "slot_30", f"{name_prefix} Active Charging Duration Slot 30", "iog_active_charging_duration_slot_30")
    
    # Create binary sensor for activation tracking
    activation_sensor = IogSlotsActivationBinarySensor(entry, slot_00_sensor, slot_30_sensor)
    
    # Add all entities
    async_add_entities([slot_00_sensor, slot_30_sensor, activation_sensor])