"""Home Energy Hub custom component."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Home Energy Hub from a config entry."""
    # Migration from old entries
    if "home_energy_hub_registry" in entry.data:
        registry = entry.data["home_energy_hub_registry"]
        if registry == "70100":
            # Migrate Geohome IHD
            new_data = {
                "integration_type": "geo_ihd",
                "username": entry.data.get("username", ""),
                "password": entry.data.get("password", ""),
                "host": "https://api.geotogether.com",
                "port": 443,
                "sensor_update_frequency": entry.data.get("sensor_update_frequency", 30),
            }
            hass.config_entries.async_update_entry(entry, data=new_data)
        elif registry in ["30101", "30110"]:
            # Migrate Seplos V2 (placeholder)
            new_data = {
                "integration_type": "seplos_v2",
                "connector_type": "usb_serial",
                "serial_port": entry.data.get("serial_port", "/dev/ttyUSB0"),
                "baud_rate": entry.data.get("baud_rate", 9600),
            }
            hass.config_entries.async_update_entry(entry, data=new_data)

    integration_type = entry.data.get("integration_type")

    # Set up coordinator
    if integration_type == "geo_ihd":
        from .integrations.geo_ihd.coordinator import GeoIhdCoordinator
        coordinator = GeoIhdCoordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
    elif integration_type == "seplos_v2":
        from .integrations.seplos_v2.coordinator import SeplosV2Coordinator
        coordinator = SeplosV2Coordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
    else:
        return False

    # Store coordinator
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove coordinator
    hass.data[DOMAIN].pop(entry.entry_id, None)

    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])