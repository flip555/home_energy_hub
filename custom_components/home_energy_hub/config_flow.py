"""Central config flow router (single DOMAIN)."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN, CONF_INTEGRATION_TYPE, INTEGRATION_TYPES, INTEGRATION_CATEGORIES,
    CONF_CONNECTOR_TYPE, CONNECTOR_TYPES, CONF_HOST, CONF_PORT, CONF_SERIAL_PORT, CONF_BAUD_RATE,
    CONF_BATTERY_ADDRESS, CONF_PACK_MODE, CONF_NAME_PREFIX, CONF_POLL_INTERVAL
)

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class HomeEnergyHubFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Home Energy Hub (all under one domain)."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """First step: Select category."""
        if user_input is not None:
            self._category = user_input["category"]
            return await self.async_step_select_integration()

        # Create category options with human-readable names
        categories = {
            category_id: category_name 
            for category_id, category_name in INTEGRATION_CATEGORIES.items()
        }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("category"): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": cat_id, "label": cat_name} for cat_id, cat_name in categories.items()],
                        translation_key="category"
                    )
                )
            }),
        )

    async def async_step_select_integration(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Select integration within category."""
        if user_input is not None:
            self._integration_type = user_input[CONF_INTEGRATION_TYPE]
            method_name = f"async_step_config_{self._integration_type}"
            return await getattr(self, method_name)()

        # Get integrations for the selected category
        category_integrations = {
            integration_id: integration_data["name"]
            for integration_id, integration_data in INTEGRATION_TYPES.items()
            if integration_data["category"] == self._category
        }

        return self.async_show_form(
            step_id="select_integration",
            data_schema=vol.Schema({
                vol.Required(CONF_INTEGRATION_TYPE): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": int_id, "label": int_name} for int_id, int_name in category_integrations.items()],
                        translation_key="integration_type"
                    )
                )
            }),
        )

    # Dynamic steps: Add one per integration (e.g., for seplos_v2)
    async def async_step_config_seplos_v2(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Seplos BMS V2 config step."""
        errors = {}
        
        if user_input is not None:
            # Store the current state
            current_step = user_input.get("_current_step", "connector")
            
            if current_step == "connector":
                # User selected connector type, now show full config
                connector_type = user_input[CONF_CONNECTOR_TYPE]
                schema = self._get_seplos_v2_schema(connector_type, include_hidden=False)
                return self.async_show_form(
                    step_id="config_seplos_v2",
                    data_schema=schema,
                    description_placeholders={
                        "integration_name": INTEGRATION_TYPES["seplos_v2"]["name"],
                        "connector_type": CONNECTOR_TYPES[connector_type]
                    }
                )
            
            elif current_step == "config":
                # User submitted full configuration
                try:
                    # Validate connection
                    from .connectors import create_connector_client
                    client = await create_connector_client(self.hass, user_input, self._integration_type)
                    await client.close()  # Test connect
                    
                    # Create entry with all data
                    await self.async_set_unique_id(f"{self._integration_type}_{user_input.get(CONF_SERIAL_PORT, user_input.get(CONF_HOST))}_{user_input[CONF_BATTERY_ADDRESS]}")
                    return self.async_create_entry(
                        title=f"{INTEGRATION_TYPES[self._integration_type]['name']} {user_input[CONF_BATTERY_ADDRESS]} via {CONNECTOR_TYPES[user_input[CONF_CONNECTOR_TYPE]]}",
                        data={**user_input, CONF_INTEGRATION_TYPE: self._integration_type},
                    )
                    
                except Exception as err:
                    errors["base"] = str(err)
                    connector_type = user_input[CONF_CONNECTOR_TYPE]
                    schema = self._get_seplos_v2_schema(connector_type, include_hidden=True)
                    return self.async_show_form(
                        step_id="config_seplos_v2",
                        data_schema=schema,
                        errors=errors,
                        description_placeholders={
                            "integration_name": INTEGRATION_TYPES["seplos_v2"]["name"],
                            "connector_type": CONNECTOR_TYPES[connector_type]
                        }
                    )

        # First time - show connector type selection
        return self.async_show_form(
            step_id="config_seplos_v2",
            data_schema=vol.Schema({
                vol.Required(CONF_CONNECTOR_TYPE): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[{"value": conn_type, "label": conn_name} for conn_type, conn_name in CONNECTOR_TYPES.items()],
                        translation_key="connector_type"
                    )
                ),
            }),
            description_placeholders={
                "integration_name": INTEGRATION_TYPES["seplos_v2"]["name"]
            }
        )

    def _get_seplos_v2_schema(self, connector_type: str, include_hidden: bool = False) -> vol.Schema:
        """Dynamic schema for Seplos V2 with connector-specific and Seplos parameters."""
        from .const import (
            CONF_SERIAL_PORT, CONF_BAUD_RATE, DEFAULT_BAUD_RATE,
            CONF_BATTERY_ADDRESS, BATTERY_ADDRESSES, CONF_PACK_MODE,
            PACK_MODES, CONF_NAME_PREFIX, CONF_POLL_INTERVAL
        )
        
        base_schema = {}
        
        if connector_type == "usb_serial":
            base_schema.update({
                vol.Required(CONF_SERIAL_PORT, default="/dev/ttyUSB1"): str,
                vol.Optional(CONF_BAUD_RATE, default=DEFAULT_BAUD_RATE): int,
            })
        elif connector_type == "telnet_serial":
            base_schema.update({
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=23): int,
            })
        
        # Add Seplos V2 specific parameters
        base_schema.update({
            vol.Required(CONF_BATTERY_ADDRESS, default="0x00"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[{"value": addr, "label": label} for addr, label in BATTERY_ADDRESSES.items()],
                    translation_key="battery_address"
                )
            ),
            vol.Required(CONF_PACK_MODE, default="single"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[{"value": mode, "label": label} for mode, label in PACK_MODES.items()],
                    translation_key="pack_mode"
                )
            ),
            vol.Optional(CONF_NAME_PREFIX, default="Seplos BMS HA "): str,
            vol.Optional(CONF_POLL_INTERVAL, default=10): selector.NumberSelector(
                selector.NumberSelectorConfig(min=5, max=300, mode="box")
            ),
        })
        
        # Add hidden fields for step tracking if needed
        if include_hidden:
            base_schema.update({
                vol.Required(CONF_CONNECTOR_TYPE, default=connector_type): str,
                vol.Required("_current_step", default="config"): str,
            })
        
        return vol.Schema(base_schema)

    def _get_connector_schema(self, connector_type: str) -> vol.Schema:
        """Dynamic schema per connector."""
        if connector_type == "usb_serial":
            from .const import CONF_SERIAL_PORT, CONF_BAUD_RATE
            return vol.Schema({
                vol.Required(CONF_SERIAL_PORT): str,
                vol.Optional(CONF_BAUD_RATE): int,
            })
        raise ValueError(f"Unknown connector: {connector_type}")

    async def async_step_config_geo_ihd(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Geo Home IHD config step (HTTP-based)."""
        if user_input is not None:
            # Validate HTTP connection
            # Placeholder: Implement HTTP test
            # For now, assume valid
            await self.async_set_unique_id(f"geo_ihd_{user_input['username']}")
            return self.async_create_entry(
                title=f"{INTEGRATION_TYPES['geo_ihd']['name']} - {user_input['username']}",
                data={**user_input, CONF_INTEGRATION_TYPE: "geo_ihd"},
            )

        schema = vol.Schema({
            vol.Required("username"): selector.TextSelector(
                selector.TextSelectorConfig(type="email")
            ),
            vol.Required("password"): selector.TextSelector(
                selector.TextSelectorConfig(type="password")
            ),
            vol.Optional(CONF_HOST, default="https://api.geotogether.com"): selector.TextSelector(
                selector.TextSelectorConfig(type="url")
            ),
            vol.Optional(CONF_PORT, default=443): selector.NumberSelector(
                selector.NumberSelectorConfig(min=1, max=65535, mode="box")
            ),
            vol.Optional("sensor_update_frequency", default=30): selector.NumberSelector(
                selector.NumberSelectorConfig(min=10, max=3600, mode="box")
            ),
        })
        return self.async_show_form(
            step_id="config_geo_ihd",
            data_schema=schema,
            description_placeholders={
                "integration_name": INTEGRATION_TYPES["geo_ihd"]["name"]
            }
        )

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        return HomeEnergyHubOptionsFlowHandler(config_entry)


class HomeEnergyHubOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Home Energy Hub."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            # Update the config entry data and title if username changed
            new_data = self._config_entry.data.copy()
            new_data.update(user_input)
            
            integration_type = self._config_entry.data.get(CONF_INTEGRATION_TYPE)
            if integration_type == "geo_ihd" and "username" in user_input:
                # Update title if username changed
                new_title = f"{INTEGRATION_TYPES['geo_ihd']['name']} - {user_input['username']}"
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data=new_data,
                    title=new_title
                )
            else:
                self.hass.config_entries.async_update_entry(self._config_entry, data=new_data)
                
            return self.async_create_entry(title="", data=user_input)

        integration_type = self._config_entry.data.get(CONF_INTEGRATION_TYPE)
        if integration_type == "geo_ihd":
            schema = vol.Schema({
                vol.Required("username", default=self._config_entry.data.get("username")): str,
                vol.Required("password", default=self._config_entry.data.get("password")): str,
                vol.Optional("sensor_update_frequency", default=self._config_entry.data.get("sensor_update_frequency", 30)): int,
            })
        elif integration_type == "seplos_v2":
            # Add options for seplos if needed
            schema = vol.Schema({
                vol.Optional("poll_interval", default=self._config_entry.data.get("poll_interval", 30)): int,
            })
        else:
            schema = vol.Schema({})

        return self.async_show_form(step_id="init", data_schema=schema)