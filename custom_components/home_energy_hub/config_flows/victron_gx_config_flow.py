from homeassistant import config_entries
import voluptuous as vol
from ..const import DOMAIN, VICTRON_MENU_OPTIONS
from pymodbus.client.tcp import ModbusTcpClient
import logging
_LOGGER = logging.getLogger(__name__)
def decode_registers_to_string(registers):
    """Decode Modbus registers to an ASCII string."""
    data = []
    for register in registers:
        data.append(register >> 8)  # High byte
        data.append(register & 0xFF)  # Low byte
    return bytes(data).decode('ascii', errors='ignore').strip()

class VictronGXConfigFlowMethods:

    async def async_step_victron_gx(self, user_input=None):
        if user_input is not None:
            # Store user input and transition to the next step

            self.user_input = user_input
            energy_tariffs_option = user_input.get('victron_gx')


            energy_tariffs = None
            # Convert the selected option_name to the corresponding key
            for key, option in VICTRON_MENU_OPTIONS.items():
                if option["option_name"] == energy_tariffs_option:
                    energy_tariffs = key
                    break

            #if energy_tariffs == "4010":
            return await self.async_step_victron_gx_ip()
        energy_tariffs_option_names = [option["option_name"] for option in VICTRON_MENU_OPTIONS.values()]

        data_schema = vol.Schema({
            vol.Required("victron_gx", description="What do you want to add"): vol.In(energy_tariffs_option_names),

        })
        return self.async_show_form(
            step_id="victron_gx",
            data_schema=data_schema,
        )


    async def async_step_victron_gx_ip(self, user_input=None):
        """Handle the Victron GX step."""
        if user_input is not None:
            # Update stored user input
            self.user_input = user_input
            client = ModbusTcpClient(self.user_input['victron_gx_ip'])
            response = None
            try:
                if client.connect():
                    response = client.read_input_registers(800, 6, unit=100)
                    
                    # Check if response contains an error
                    if not response.isError():
                        serial_string = decode_registers_to_string(response.registers)
                        _LOGGER.debug("Decoded serial string: %s", serial_string)
                        title = f"Victron GX: {self.user_input['victron_gx_ip']} - {serial_string}"
                        return self.async_create_entry(title=title, data=self.user_input)
                        # For your introspection:
                        public_attributes = {attr: getattr(response, attr) for attr in dir(response) if not attr.startswith("_")}
                        _LOGGER.debug("response attributes: %s", public_attributes)
                    else:
                        _LOGGER.error("Error reading from Modbus device: %s", response)
                        
                    client.close()
            except Exception as e:
                return self.async_abort(reason="Connector port is not active")
            return await self.async_step_victron_gx_ip()

        data_schema = vol.Schema({
            vol.Required("victron_gx_ip", description="Please enter GX IP", default="192.168.1.153"): str
        })

        return self.async_show_form(
            step_id="victron_gx_ip",
            data_schema=data_schema,
        )
