from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, MAIN_MENU_OPTIONS
from .config_flows.bms_config_flow import BMSConfigFlowMethods
from .config_flows.energy_config_flow import EnergyConfigFlowMethods

class BMSConnectorConfigFlow(config_entries.ConfigFlow, BMSConfigFlowMethods, EnergyConfigFlowMethods, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # If the user checks the box, proceed to the next step
            return await self.async_step_main_menu()

        data_schema = vol.Schema({
            vol.Optional("anon_reporting_confirm", description="I confirm"): bool,
        })
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    async def async_step_main_menu(self, user_input=None):
        if user_input is not None:
            # Store user input and transition to the next step
            self.user_input = user_input
            main_menu_selection_option = user_input.get('main_menu_selection')
            main_menu_selection = None

            # Convert the selected option_name to the corresponding key
            for key, option in MAIN_MENU_OPTIONS.items():
                if option["option_name"] == main_menu_selection_option:
                    main_menu_selection = key
                    break
            if main_menu_selection == "1000":
                return await self.async_step_bms_type()
            elif main_menu_selection == "2000":
                return await self.async_step_energy_tariffs()
            else:
                return await self.async_step_main_menu()

        main_menu_option_names = [option["option_name"] for option in MAIN_MENU_OPTIONS.values()]

        data_schema = vol.Schema({
            vol.Required("main_menu_selection", description="What do you want to add"): vol.In(main_menu_option_names),
        })

        return self.async_show_form(
            step_id="main_menu",
            data_schema=data_schema,
        )

