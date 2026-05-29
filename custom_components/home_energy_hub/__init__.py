"""Home Energy Hub custom component."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate config entry from old version to new version."""
    _LOGGER.info("Migrating config entry %s from version %s to %s",
                 config_entry.entry_id, config_entry.version, config_entry.version + 1)

    if config_entry.version == 1:
        integration_type = config_entry.data.get("integration_type")

        if integration_type in ("seplos_v2", "seplos_v3"):
            battery_address = config_entry.data.get("battery_address", "0x00")
            name_prefix = config_entry.data.get("name_prefix", "Seplos BMS HA")

            # --- Migrate device registry identifiers ---
            device_registry = dr.async_get(hass)

            old_bms_id = ("home_energy_hub", f"seplos_v2_{config_entry.entry_id}_{battery_address}")
            old_settings_id = ("home_energy_hub", f"seplos_v2_{config_entry.entry_id}_{battery_address}_settings")
            new_bms_id = ("home_energy_hub", f"seplos_v2_{config_entry.entry_id}")
            new_settings_id = ("home_energy_hub", f"seplos_v2_{config_entry.entry_id}_settings")

            for device in list(device_registry.devices.values()):
                if old_bms_id in device.identifiers:
                    _LOGGER.info("Migrating BMS device %s: identifiers %s -> %s",
                                 device.id, old_bms_id, new_bms_id)
                    device_registry.async_update_device(
                        device.id,
                        new_identifiers={new_bms_id},
                        name=f"{name_prefix}",
                        model="V2 BMS",
                    )
                elif old_settings_id in device.identifiers:
                    _LOGGER.info("Migrating Settings device %s: identifiers %s -> %s",
                                 device.id, old_settings_id, new_settings_id)
                    device_registry.async_update_device(
                        device.id,
                        new_identifiers={new_settings_id},
                        name=f"{name_prefix} Settings",
                        model="V2 Settings",
                    )

            # --- Build reverse map for settings sensor keys ---
            # v2.0.0-alpha used key[:-10] instead of key[:-9] to strip the
            # _settings suffix, truncating all 55 settings keys by 1 character.
            # This reverses that so the migrated unique_id matches what the
            # sensor code generates.
            _SETTINGS_KEYS = [
                "monomer_high_voltage_alarm", "monomer_overvoltage_protection",
                "monomer_overvoltage_recovery", "monomer_undervoltage_protection",
                "monomer_undervoltage_recovery", "equalization_opening_voltage",
                "battery_low_voltage_forbidden_charging",
                "total_voltage_overvoltage_protection", "total_voltage_undervoltage_protection",
                "total_pressure_undervoltage_recovery", "charging_overvoltage_protection",
                "charging_overvoltage_recovery", "charging_high_temperature_warning",
                "charging_high_temperature_recovery", "charging_low_temperature_warning",
                "charging_low_temperature_recovery", "charging_over_temperature_protection",
                "charging_over_temperature_recovery", "charging_under_temperature_protection",
                "charging_under_temperature_recovery", "discharge_high_temperature_warning",
                "discharge_high_temperature_recovery", "discharge_low_temperature_warning",
                "discharge_low_temperature_recovery", "discharge_over_temperature_protection",
                "discharge_over_temperature_recovery", "discharge_under_temperature_protection",
                "discharge_under_temperature_recovery", "cell_low_temperature_heating",
                "ambient_high_temperature_alarm", "ambient_high_temperature_recovery",
                "ambient_low_temperature_alarm", "ambient_low_temperature_recovery",
                "environment_over_temperature_protection",
                "environment_over_temperature_recovery",
                "environment_under_temperature_protection",
                "environment_under_temperature_recovery",
                "power_high_temperature_alarm", "power_high_temperature_recovery",
                "power_over_temperature_protection", "power_over_temperature_recovery",
                "charging_overcurrent_warning", "charging_overcurrent_recovery",
                "discharge_overcurrent_warning", "discharge_overcurrent_recovery",
                "charge_overcurrent_protection", "discharge_overcurrent_protection",
                "transient_overcurrent_protection", "charge_overcurrent_delay",
                "discharge_overcurrent_delay", "transient_overcurrent_delay",
                "overcurrent_delay_recovery", "overcurrent_recovery_times",
                "charge_current_limit_delay", "soc_ah",
            ]
            _settings_reverse_map = {}
            for key in _SETTINGS_KEYS:
                truncated = f"{key}_settings"[:-10]
                _settings_reverse_map[truncated] = key

            # --- Migrate entity registry unique_ids ---
            entity_registry = er.async_get(hass)

            # Old unique_id format: {name_prefix_lower}_{battery_address}_{snake_case_key}
            old_prefix = f"{name_prefix.lower().replace(' ', '_')}_{battery_address}_"

            for entity in list(entity_registry.entities.values()):
                if entity.config_entry_id != config_entry.entry_id:
                    continue
                if entity.unique_id and entity.unique_id.startswith(old_prefix):
                    snake_case_key = entity.unique_id[len(old_prefix):]

                    # Undo the [:-10] truncation bug for settings keys
                    corrected_key = _settings_reverse_map.get(snake_case_key, snake_case_key)

                    new_unique_id = f"seplos_v2_{config_entry.entry_id}_{corrected_key}"

                    _LOGGER.info("Migrating entity %s: unique_id %s -> %s",
                                 entity.entity_id, entity.unique_id, new_unique_id)
                    entity_registry.async_update_entity(
                        entity.entity_id,
                        new_unique_id=new_unique_id,
                    )

    _LOGGER.info("Migration to version 2 complete for entry %s", config_entry.entry_id)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Home Energy Hub from a config entry."""
    # Migration from old entries (pre-config-flow backward compat)
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
    elif integration_type == "seplos_v3":
        from .integrations.seplos_v3.coordinator import SeplosV3Coordinator
        coordinator = SeplosV3Coordinator(hass, entry)
        await coordinator.async_config_entry_first_refresh()
    else:
        return False

    # Store coordinator (only for integrations that use one)
    if coordinator is not None:
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove coordinator
    hass.data[DOMAIN].pop(entry.entry_id, None)

    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])
