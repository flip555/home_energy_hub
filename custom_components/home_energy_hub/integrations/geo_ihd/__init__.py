"""GEO IHD integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .coordinator import GeoIhdCoordinator
from .sensor import GeoIhdSensor

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up GEO IHD sensors."""
    device_registry = dr.async_get(hass)
    username = entry.data.get("username")
    coordinator = GeoIhdCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    # Register devices
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("home_energy_hub", entry.entry_id, username, "electric")},
        manufacturer="Geo Home",
        name=f"Geo Home IHD - Electricity",
        model="Geo IHD",
        sw_version="v1.0",
    )
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={("home_energy_hub", entry.entry_id, username, "gas")},
        manufacturer="Geo Home",
        name=f"Geo Home IHD - Gas",
        model="Geo IHD",
        sw_version="v1.0",
    )

    async_add_entities([GeoIhdSensor(coordinator, key, entry.entry_id, username) for key in coordinator.data.keys()])