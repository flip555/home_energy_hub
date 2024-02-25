from homeassistant import config_entries
import voluptuous as vol
from ...const import DOMAIN

class GeoIHDConfigFlowMethods:

    async def async_step_geo_ihd(self, user_input=None):
        if user_input is not None:
            # Store user input and create the configuration entry
            self.user_input.update(user_input)
            self.user_input["name_prefix"] = f"Geo IHD - {self.user_input['username']} - "
            self.user_input["sensor_update_frequency"] = 30
            title = f"Geo IHD - {self.user_input['username']}"
            return self.async_create_entry(title=title, data=self.user_input)

        data_schema = vol.Schema({
                vol.Required('username'): str,
                vol.Required('password'): str
        })

        return self.async_show_form(
            step_id="geo_ihd",
            data_schema=data_schema,
        )

class GeoIHDOptionsFlowMethods:
    async def async_step_geo_ihd_options(self, user_input=None):
        if user_input is not None:
                # Update the data
                self.config_entry.data = {**self.config_entry.data, **user_input}
                
                # Update the config entry
                self.hass.config_entries.async_update_entry(self.config_entry, data=self.config_entry.data)
                
                return self.async_create_entry(title="", data=user_input)

        sensor_update_frequency = self.config_entry.data.get("sensor_update_frequency", 30)

        return self.async_show_form(
            step_id="geo_ihd_options",
            data_schema=vol.Schema({
                vol.Required("sensor_update_frequency", default=sensor_update_frequency): int,
            })
        )
