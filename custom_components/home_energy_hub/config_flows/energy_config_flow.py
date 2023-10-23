from homeassistant import config_entries
import voluptuous as vol
from ..const import DOMAIN, ENERGY_MENU_OPTIONS, ENERGY_OCTOPUS_REGIONS

class EnergyConfigFlowMethods:
    async def async_step_energy_tariffs(self, user_input=None):
        if user_input is not None:
            # Store user input and transition to the next step
            self.user_input = user_input
            energy_tariffs_option = user_input.get('energy_tariffs')
            energy_tariffs = None
            # Convert the selected option_name to the corresponding key
            for key, option in ENERGY_MENU_OPTIONS.items():
                if option["option_name"] == energy_tariffs_option:
                    energy_tariffs = key
                    break
            if energy_tariffs == "2010":
                return await self.async_step_octopus_step()

        energy_tariffs_option_names = [option["option_name"] for option in ENERGY_MENU_OPTIONS.values()]

        data_schema = vol.Schema({
            vol.Required("energy_tariffs", description="What do you want to add"): vol.In(energy_tariffs_option_names),

        })
        return self.async_show_form(
            step_id="energy_tariffs",
            data_schema=data_schema,
        )

    async def async_step_octopus_step(self, user_input=None):
        if user_input is not None:
            # Store user input and create the configuration entry
            self.user_input.update(user_input)
            title = f"Octopus Energy UK Agile - Region {self.user_input['octopus_region']}"
            return self.async_create_entry(title=title, data=self.user_input)

        energy_tariffs_option_names = [option["option_name"] for option in ENERGY_OCTOPUS_REGIONS.values()]

        data_schema = vol.Schema({
            vol.Required("octopus_region", description="What do you want to add"): vol.In({k: v["option_name"] for k, v in ENERGY_OCTOPUS_REGIONS.items()}),
        })

        return self.async_show_form(
            step_id="octopus_step",
            data_schema=data_schema,
        )

