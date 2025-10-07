"""Sensor platform for Home Energy Hub."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_INTEGRATION_TYPE, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors based on integration type."""
    integration_type = entry.data.get(CONF_INTEGRATION_TYPE)

    if integration_type == "geo_ihd":
        from homeassistant.helpers import device_registry as dr
        from .integrations.geo_ihd.sensor import GeoIhdSensor

        coordinator = hass.data[DOMAIN][entry.entry_id]
        device_registry = dr.async_get(hass)
        username = entry.data.get("username")

        # Register devices
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={("home_energy_hub", "geo_ihd", entry.entry_id, username, "electric")},
            manufacturer="Geo Home",
            name=f"Geo Home IHD - Electricity",
            model="Geo IHD",
            sw_version="v1.0",
        )
        device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={("home_energy_hub", "geo_ihd", entry.entry_id, username, "gas")},
            manufacturer="Geo Home",
            name=f"Geo Home IHD - Gas",
            model="Geo IHD",
            sw_version="v1.0",
        )

        async_add_entities([GeoIhdSensor(coordinator, key, entry.entry_id, username) for key in coordinator.data.keys()])
    elif integration_type == "seplos_v2":
        from .integrations.seplos_v2.sensor import SeplosV2Sensor

        coordinator = hass.data[DOMAIN][entry.entry_id]
        async_add_entities([SeplosV2Sensor(coordinator, key, entry) for key in coordinator.data.keys()])
    elif integration_type == "iog_slots":
        # IOG-Ohme Slots doesn't use a coordinator, import and call its setup directly
        from .integrations.iog_slots import async_setup_entry as iog_async_setup_entry
        await iog_async_setup_entry(hass, entry, async_add_entities)