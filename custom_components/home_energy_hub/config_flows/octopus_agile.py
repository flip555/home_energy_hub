from homeassistant import config_entries
import voluptuous as vol
from ..const import DOMAIN

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

class EnergyConfigFlowMethods:
    async def async_step_energy_tariffs(self, user_input=None):
        if user_input is not None:
            # Store user input and create the configuration entry
            self.user_input = user_input
            title = f"Octopus Energy UK Agile - Region {self.user_input['octopus_region']}"
            return self.async_create_entry(title=title, data=self.user_input)

        energy_tariffs_option_names = [option["option_name"] for option in ENERGY_OCTOPUS_REGIONS.values()]

        data_schema = vol.Schema({
            vol.Required("octopus_region", description="What do you want to add"): vol.In({k: v["option_name"] for k, v in ENERGY_OCTOPUS_REGIONS.items()}),
        })

        return self.async_show_form(
            step_id="energy_tariffs",
            data_schema=data_schema,
        )

