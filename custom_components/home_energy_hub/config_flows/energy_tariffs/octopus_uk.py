from homeassistant import config_entries
import voluptuous as vol
from ...const import DOMAIN
import homeassistant.helpers.config_validation as cv

ENERGY_OCTOPUS_REGIONS = {
    "A": {"option_name": "Eastern England"},
    "B": {"option_name": "East Midlands"},
    "C": {"option_name": "London"},
    "D": {"option_name": "Merseyside and Northern Wales"},
    "E": {"option_name": "West Midlands"},
    "F": {"option_name": "North Eastern England"},
    "G": {"option_name": "North Western England"},
    "H": {"option_name": "Southern England"},
    "J": {"option_name": "South Eastern England"},
    "K": {"option_name": "Southern Wales"},
    "L": {"option_name": "South Western England"},
    "M": {"option_name": "Yorkshire"},
    "N": {"option_name": "Southern Scotland"},
    "P": {"option_name": "Northern Scotland"},
}

class OctopusUKEnergyConfigFlowMethods:
    async def async_step_octopus_agile_tariffs(self, user_input=None):
        if user_input is not None:
            # Store user input and create the configuration entry
            self.user_input.update(user_input)
            self.user_input["name_prefix"] = f"Octopus Energy Agile - Region {self.user_input['current_region']}"
            self.user_input["octopus_api_update_frequency"] = 600
            self.user_input["sensor_update_frequency"] = 5

            title = f"Octopus Energy UK Agile - Region {self.user_input['current_region']}"
            return self.async_create_entry(title=title, data=self.user_input)

        energy_tariffs_option_names = [option["option_name"] for option in ENERGY_OCTOPUS_REGIONS.values()]

        data_schema = vol.Schema({
            vol.Required("current_region"): vol.In({k: v["option_name"] for k, v in ENERGY_OCTOPUS_REGIONS.items()}),
        })

        return self.async_show_form(
            step_id="octopus_agile_tariffs",
            data_schema=data_schema,
        )


    async def async_step_octopus_flexible_tariffs(self, user_input=None):
        if user_input is not None:
            # Store user input and create the configuration entry
            self.user_input.update(user_input)
            self.user_input["name_prefix"] = f"Octopus Energy Flexible - Region {self.user_input['current_region']}"
            self.user_input["octopus_api_update_frequency"] = (60 * 60)
            self.user_input["sensor_update_frequency"] = (60 * 30)

            title = f"Octopus Energy UK Flexible - Region {self.user_input['current_region']}"
            return self.async_create_entry(title=title, data=self.user_input)

        energy_tariffs_option_names = [option["option_name"] for option in ENERGY_OCTOPUS_REGIONS.values()]

        data_schema = vol.Schema({
            vol.Required("current_region"): vol.In({k: v["option_name"] for k, v in ENERGY_OCTOPUS_REGIONS.items()}),
        })

        return self.async_show_form(
            step_id="octopus_flexible_tariffs",
            data_schema=data_schema,
        )

    async def async_step_octopus_tracker_tariffs(self, user_input=None):
            if user_input is not None:
                # Store user input and create the configuration entry
                self.user_input.update(user_input)
                self.user_input["name_prefix"] = f"Octopus Energy Tracker - Region {self.user_input['current_region']}"
                self.user_input["octopus_api_update_frequency"] = (60 * 60)
                self.user_input["sensor_update_frequency"] = (60 * 30)

                title = f"Octopus Energy UK Tracker - Region {self.user_input['current_region']}"
                return self.async_create_entry(title=title, data=self.user_input)

            energy_tariffs_option_names = [option["option_name"] for option in ENERGY_OCTOPUS_REGIONS.values()]

            data_schema = vol.Schema({
                vol.Required("current_region"): vol.In({k: v["option_name"] for k, v in ENERGY_OCTOPUS_REGIONS.items()}),
            })

            return self.async_show_form(
                step_id="octopus_tracker_tariffs",
                data_schema=data_schema,
            )

    async def async_step_octopus_account_data(self, user_input=None):
            if user_input is not None:
                # Store user input and create the configuration entry
                self.user_input.update(user_input)
                self.user_input["name_prefix"] = f"Octopus Energy Account Data - {self.user_input['account_id']}"
                self.user_input["octopus_api_update_frequency"] = (60 * 1)
                self.user_input["sensor_update_frequency"] = (60 * 0.5)

                title = f"Octopus Energy UK Account Data - {self.user_input['account_id']}"
                return self.async_create_entry(title=title, data=self.user_input)

            data_schema = vol.Schema({
                vol.Required("account_id", default="A-"): str,
                vol.Required("api_key", default=""): str,
            })

            return self.async_show_form(
                step_id="octopus_account_data",
                data_schema=data_schema,
            )

    async def async_step_octopus_tariff_engine_agile(self, user_input=None):
        if user_input is not None:
            # Store user input and create the configuration entry
            self.user_input.update(user_input)
            self.user_input["name_prefix"] = f"Octopus Energy Agile - Region {', '.join(self.user_input['current_region'])}"
            self.user_input["octopus_api_update_frequency"] = 600
            self.user_input["sensor_update_frequency"] = 5
            self.user_input["regions"] = self.user_input['current_region']

            title = f"Octopus Energy UK Agile Tariff"
            return self.async_create_entry(title=title, data=self.user_input)

        energy_tariffs_option_names = {k: v["option_name"] for k, v in ENERGY_OCTOPUS_REGIONS.items()}

        data_schema = vol.Schema({
            vol.Optional("current_region"): cv.multi_select(energy_tariffs_option_names),
        })

        return self.async_show_form(
            step_id="octopus_tariff_engine_agile",
            data_schema=data_schema,
        )

    async def async_step_octopus_tariff_engine_cosy(self, user_input=None):
        if user_input is not None:
            # Store user input and create the configuration entry
            self.user_input.update(user_input)
            self.user_input["name_prefix"] = f"Octopus Energy Cosy - Region {', '.join(self.user_input['current_region'])}"
            self.user_input["octopus_api_update_frequency"] = 600
            self.user_input["sensor_update_frequency"] = 5
            self.user_input["regions"] = self.user_input['current_region']

            title = f"Octopus Energy UK Cosy Tariff"
            return self.async_create_entry(title=title, data=self.user_input)

        energy_tariffs_option_names = {k: v["option_name"] for k, v in ENERGY_OCTOPUS_REGIONS.items()}

        data_schema = vol.Schema({
            vol.Optional("current_region"): cv.multi_select(energy_tariffs_option_names),
        })

        return self.async_show_form(
            step_id="octopus_tariff_engine_cosy",
            data_schema=data_schema,
        )

    async def async_step_octopus_tariff_engine_tracker(self, user_input=None):
        if user_input is not None:
            # Store user input and create the configuration entry
            self.user_input.update(user_input)
            self.user_input["name_prefix"] = f"Octopus Energy Tracker - Region {', '.join(self.user_input['current_region'])}"
            self.user_input["octopus_api_update_frequency"] = (60 * 60)
            self.user_input["sensor_update_frequency"] = (60 * 30)
            self.user_input["regions"] = self.user_input['current_region']

            title = f"Octopus Energy UK Tracker Tariff"
            return self.async_create_entry(title=title, data=self.user_input)

        energy_tariffs_option_names = {k: v["option_name"] for k, v in ENERGY_OCTOPUS_REGIONS.items()}

        data_schema = vol.Schema({
            vol.Optional("fuel", default={"Gas","Electric"}): cv.multi_select({"Gas","Electric"}),
            vol.Optional("current_region"): cv.multi_select(energy_tariffs_option_names),
        })

        return self.async_show_form(
            step_id="octopus_tariff_engine_tracker",
            data_schema=data_schema,
        )

    async def async_step_octopus_tariff_engine_flexible(self, user_input=None):
        if user_input is not None:
            # Store user input and create the configuration entry
            self.user_input.update(user_input)
            self.user_input["name_prefix"] = f"Octopus Energy Flexible - Region {', '.join(self.user_input['current_region'])}"
            self.user_input["octopus_api_update_frequency"] = (60 * 60)
            self.user_input["sensor_update_frequency"] = (60 * 30)
            self.user_input["regions"] = self.user_input['current_region']

            title = f"Octopus Energy UK Flexible Tariff"
            return self.async_create_entry(title=title, data=self.user_input)

        energy_tariffs_option_names = {k: v["option_name"] for k, v in ENERGY_OCTOPUS_REGIONS.items()}

        data_schema = vol.Schema({
            vol.Optional("fuel", default={"Electric"}): cv.multi_select({"Electric"}),
            vol.Optional("current_region"): cv.multi_select(energy_tariffs_option_names),
        })

        return self.async_show_form(
            step_id="octopus_tariff_engine_flexible",
            data_schema=data_schema,
        )

class OctopusUKEnergyOptionsFlowMethods:
    async def async_step_octopus_options_tariff_engine_agile(self, user_input=None):
        if user_input is not None:
                # Update the data
                self.config_entry.data = {**self.config_entry.data, **user_input}
                
                # Update the config entry
                self.hass.config_entries.async_update_entry(self.config_entry, data=self.config_entry.data)
                
                return self.async_create_entry(title="", data=user_input)

        current_region = self.config_entry.data.get("current_region", "")
        name_prefix = self.config_entry.data.get("name_prefix", f"Octopus Energy Agile - Region {current_region}")
        octopus_api_update_frequency = self.config_entry.data.get("octopus_api_update_frequency", 600)
        sensor_update_frequency = self.config_entry.data.get("sensor_update_frequency", 1)
        energy_tariffs_option_names = {k: v["option_name"] for k, v in ENERGY_OCTOPUS_REGIONS.items()}

        return self.async_show_form(
            step_id="octopus_options_tariff_engine_agile",
            data_schema=vol.Schema({
                vol.Optional("current_region", default=current_region): cv.multi_select(energy_tariffs_option_names),
                vol.Required("octopus_api_update_frequency", default=octopus_api_update_frequency): int,
                vol.Required("sensor_update_frequency", default=sensor_update_frequency): int,
            })
        )

    async def async_step_octopus_options_tariff_engine_cosy(self, user_input=None):
        if user_input is not None:
                # Update the data
                self.config_entry.data = {**self.config_entry.data, **user_input}
                
                # Update the config entry
                self.hass.config_entries.async_update_entry(self.config_entry, data=self.config_entry.data)
                
                return self.async_create_entry(title="", data=user_input)

        current_region = self.config_entry.data.get("current_region", "")
        name_prefix = self.config_entry.data.get("name_prefix", f"Octopus Energy Cosy - Region {current_region}")
        octopus_api_update_frequency = self.config_entry.data.get("octopus_api_update_frequency", 600)
        sensor_update_frequency = self.config_entry.data.get("sensor_update_frequency", 1)
        energy_tariffs_option_names = {k: v["option_name"] for k, v in ENERGY_OCTOPUS_REGIONS.items()}

        return self.async_show_form(
            step_id="octopus_options_tariff_engine_cosy",
            data_schema=vol.Schema({
                vol.Optional("current_region", default=current_region): cv.multi_select(energy_tariffs_option_names),
                vol.Required("octopus_api_update_frequency", default=octopus_api_update_frequency): int,
                vol.Required("sensor_update_frequency", default=sensor_update_frequency): int,
            })
        )

    async def async_step_octopus_options_tariff_engine_tracker(self, user_input=None):
        if user_input is not None:
                # Update the data
                self.config_entry.data = {**self.config_entry.data, **user_input}
                
                # Update the config entry
                self.hass.config_entries.async_update_entry(self.config_entry, data=self.config_entry.data)
                
                return self.async_create_entry(title="", data=user_input)

        current_region = self.config_entry.data.get("current_region", "")
        fuel = self.config_entry.data.get("fuel", {"Gas","Electric"})
        name_prefix = self.config_entry.data.get("name_prefix", f"Octopus Energy Tracker - Region {current_region}")
        octopus_api_update_frequency = self.config_entry.data.get("octopus_api_update_frequency", 600)
        sensor_update_frequency = self.config_entry.data.get("sensor_update_frequency", 1)
        energy_tariffs_option_names = {k: v["option_name"] for k, v in ENERGY_OCTOPUS_REGIONS.items()}

        return self.async_show_form(
            step_id="octopus_options_tariff_engine_tracker",
            data_schema=vol.Schema({
                vol.Optional("fuel", default=fuel): cv.multi_select({"Gas","Electric"}),
                vol.Optional("current_region", default=current_region): cv.multi_select(energy_tariffs_option_names),
                vol.Required("octopus_api_update_frequency", default=octopus_api_update_frequency): int,
                vol.Required("sensor_update_frequency", default=sensor_update_frequency): int,
            })
        )

    async def async_step_octopus_options_tariff_engine_flexible(self, user_input=None):
        if user_input is not None:
                # Update the data
                self.config_entry.data = {**self.config_entry.data, **user_input}
                
                # Update the config entry
                self.hass.config_entries.async_update_entry(self.config_entry, data=self.config_entry.data)
                
                return self.async_create_entry(title="", data=user_input)

        current_region = self.config_entry.data.get("current_region", "")
        name_prefix = self.config_entry.data.get("name_prefix", f"Octopus Energy Flexible - Region {current_region}")
        octopus_api_update_frequency = self.config_entry.data.get("octopus_api_update_frequency", 600)
        sensor_update_frequency = self.config_entry.data.get("sensor_update_frequency", 1)
        energy_tariffs_option_names = {k: v["option_name"] for k, v in ENERGY_OCTOPUS_REGIONS.items()}
        fuel = self.config_entry.data.get("fuel", {"Electric"})

        return self.async_show_form(
            step_id="octopus_options_tariff_engine_flexible",
            data_schema=vol.Schema({
                vol.Optional("fuel", default=fuel): cv.multi_select({"Electric"}),
                vol.Optional("current_region", default=current_region): cv.multi_select(energy_tariffs_option_names),
                vol.Required("octopus_api_update_frequency", default=octopus_api_update_frequency): int,
                vol.Required("sensor_update_frequency", default=sensor_update_frequency): int,
            })
        )

    async def async_step_octopus_options_agile_tariffs(self, user_input=None):
        if user_input is not None:
                # Update the data
                self.config_entry.data = {**self.config_entry.data, **user_input}
                
                # Update the config entry
                self.hass.config_entries.async_update_entry(self.config_entry, data=self.config_entry.data)
                
                return self.async_create_entry(title="", data=user_input)

        current_region = self.config_entry.data.get("current_region", "")
        name_prefix = self.config_entry.data.get("name_prefix", f"Octopus Energy Agile - Region {current_region}")
        octopus_api_update_frequency = self.config_entry.data.get("octopus_api_update_frequency", 600)
        sensor_update_frequency = self.config_entry.data.get("sensor_update_frequency", 1)

        return self.async_show_form(
            step_id="octopus_options_agile_tariffs",
            data_schema=vol.Schema({
                vol.Required("octopus_api_update_frequency", default=octopus_api_update_frequency): int,
                vol.Required("sensor_update_frequency", default=sensor_update_frequency): int,
            })
        )

    async def async_step_octopus_options_flexible_tariffs(self, user_input=None):
        if user_input is not None:
                # Update the data
                self.config_entry.data = {**self.config_entry.data, **user_input}
                
                # Update the config entry
                self.hass.config_entries.async_update_entry(self.config_entry, data=self.config_entry.data)
                
                return self.async_create_entry(title="", data=user_input)

        current_region = self.config_entry.data.get("current_region", "")
        name_prefix = self.config_entry.data.get("name_prefix", f"Octopus Energy Flexible - Region {current_region}")
        octopus_api_update_frequency = self.config_entry.data.get("octopus_api_update_frequency", (60 * 60))
        sensor_update_frequency = self.config_entry.data.get("sensor_update_frequency", (60 * 60))

        return self.async_show_form(
            step_id="octopus_options_flexible_tariffs",
            data_schema=vol.Schema({
                vol.Required("octopus_api_update_frequency", default=octopus_api_update_frequency): int,
                vol.Required("sensor_update_frequency", default=sensor_update_frequency): int,
            })
        )

    async def async_step_octopus_options_tracker_tariffs(self, user_input=None):
        if user_input is not None:
                # Update the data
                self.config_entry.data = {**self.config_entry.data, **user_input}
                
                # Update the config entry
                self.hass.config_entries.async_update_entry(self.config_entry, data=self.config_entry.data)
                
                return self.async_create_entry(title="", data=user_input)

        current_region = self.config_entry.data.get("current_region", "")
        name_prefix = self.config_entry.data.get("name_prefix", f"Octopus Energy Tracker - Region {current_region}")
        octopus_api_update_frequency = self.config_entry.data.get("octopus_api_update_frequency", (60 * 60))
        sensor_update_frequency = self.config_entry.data.get("sensor_update_frequency", (60 * 60))

        return self.async_show_form(
            step_id="octopus_options_tracker_tariffs",
            data_schema=vol.Schema({
                vol.Required("octopus_api_update_frequency", default=octopus_api_update_frequency): int,
                vol.Required("sensor_update_frequency", default=sensor_update_frequency): int,
            })
        )

    async def async_step_octopus_options_account_data(self, user_input=None):
        if user_input is not None:
                # Update the data
                self.config_entry.data = {**self.config_entry.data, **user_input}
                
                # Update the config entry
                self.hass.config_entries.async_update_entry(self.config_entry, data=self.config_entry.data)
                
                return self.async_create_entry(title="", data=user_input)

        account_id = self.config_entry.data.get("account_id", "")
        api_key = self.config_entry.data.get("api_key", "")
        octopus_api_update_frequency = self.config_entry.data.get("octopus_api_update_frequency", (60 * 1))
        sensor_update_frequency = self.config_entry.data.get("sensor_update_frequency", (60 * 0.5))

        return self.async_show_form(
            step_id="octopus_options_account_data",
            data_schema=vol.Schema({
                vol.Required("account_id", default=account_id): str,
                vol.Required("api_key", default=api_key): str,
                vol.Required("octopus_api_update_frequency", default=octopus_api_update_frequency): int,
                vol.Required("sensor_update_frequency", default=sensor_update_frequency): int,
            })
        )