from homeassistant import config_entries
import voluptuous as vol
from ...const import DOMAIN

class SeplosConfigFlowMethods:
    async def async_step_seplos_bms_v2(self, user_input=None):
        if user_input is not None:
            # Store user input and create the configuration entry
            self.user_input.update(user_input)
            self.user_input["name_prefix"] = f"Seplos BMS HA - {self.user_input['battery_address']} - "
            self.user_input["sensor_update_frequency"] = 5
            title = f"Seplos BMS V2 - {self.user_input['battery_address']} - {self.user_input['usb_port']}"
            return self.async_create_entry(title=title, data=self.user_input)

        data_schema = vol.Schema({
                vol.Required("usb_port", default="/dev/ttyUSB0"): str,
                vol.Required("battery_address", default="0x00"): str,
        })

        return self.async_show_form(
            step_id="seplos_bms_v2",
            data_schema=data_schema,
        )

    async def async_step_seplos_bms_v2_device(self, user_input=None):
        if user_input is not None:
            # Store user input and create the configuration entry
            self.user_input.update(user_input)
            self.user_input["name_prefix"] = f"Seplos BMS HA - {self.user_input['battery_address']} - "
            self.user_input["sensor_update_frequency"] = 5
            title = f"Seplos BMS V2 - {self.user_input['usb_port']}"
            return self.async_create_entry(title=title, data=self.user_input)

        data_schema = vol.Schema({
                vol.Required("usb_port", default="/dev/ttyUSB0"): str,
                vol.Required("battery_address", default="0x00"): str,
        })

        return self.async_show_form(
            step_id="seplos_bms_v2_device",
            data_schema=data_schema,
        )

class SeplosOptionsFlowMethods:
    async def async_step_seplos_options_bms_v2(self, user_input=None):
        if user_input is not None:
                # Update the data
                self.config_entry.data = {**self.config_entry.data, **user_input}
                
                # Update the config entry
                self.hass.config_entries.async_update_entry(self.config_entry, data=self.config_entry.data)
                
                return self.async_create_entry(title="", data=user_input)
        battery_address = self.config_entry.data.get("battery_address","0x00")
        usb_port = self.config_entry.data.get("usb_port", "")
        name_prefix = self.config_entry.data.get("name_prefix", f"Seplos BMS HA - {battery_address} - ")
        sensor_update_frequency = self.config_entry.data.get("sensor_update_frequency", 5)

        return self.async_show_form(
            step_id="seplos_options_bms_v2",
            data_schema=vol.Schema({
                vol.Required("usb_port", default=usb_port): str,
                vol.Required("battery_address", default=battery_address): str,
                vol.Required("sensor_update_frequency", default=sensor_update_frequency): int,
            })
        )
