from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.entity_component import EntityComponent
from pymodbus.client.tcp import ModbusTcpClient
import aiohttp
import json
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from ..const import (
    NAME,
    DOMAIN,
    VERSION,
    ATTRIBUTION,
)

_LOGGER = logging.getLogger(__name__)
def decode_registers_to_string(registers):
    """Decode Modbus registers to an ASCII string."""
    data = []
    for register in registers:
        data.append(register >> 8)  # High byte
        data.append(register & 0xFF)  # Low byte
    return bytes(data).decode('ascii', errors='ignore').strip()

def determine_length(data_type):
    if data_type.startswith("string"):
        length = int(data_type.split("[")[1].split("]")[0])
        return length
    else:
        return 1

async def generate_sensors(hass, gx_ip, entry, async_add_entities):

    async def async_update_data():
        client = ModbusTcpClient(gx_ip)
        victron_data = {
            "system": {}
        }
        try:
            if client.connect():
                response = client.read_input_registers(800, 27, unit=100)  # Reading from address 800 to 866
                if not response.isError():
                    registers = response.registers
                    _LOGGER.debug("Received data: %s", registers)  # Print received data for debugging
                    victron_data["system"]["serial"] = decode_registers_to_string(registers[0:6])
                    victron_data["system"]["CCGX Relay 1 state"] = registers[6]
                    victron_data["system"]["CCGX Relay 2 state"] = registers[7]
                    victron_data["system"]["PV - AC-coupled on output L1"] = registers[8]
                    victron_data["system"]["PV - AC-coupled on output L2"] = registers[9]
                    victron_data["system"]["PV - AC-coupled on output L3"] = registers[10]
                    victron_data["system"]["PV - AC-coupled on input L1"] = registers[11]
                    victron_data["system"]["PV - AC-coupled on input L2"] = registers[12]
                    victron_data["system"]["PV - AC-coupled on input L3"] = registers[13]
                    victron_data["system"]["PV - AC-coupled on generator L1"] = registers[14]
                    victron_data["system"]["PV - AC-coupled on generator L2"] = registers[15]
                    victron_data["system"]["PV - AC-coupled on generator L3"] = registers[16]
                    victron_data["system"]["AC Consumption L1"] = registers[17]
                    victron_data["system"]["AC Consumption L2"] = registers[18]
                    victron_data["system"]["AC Consumption L3"] = registers[19]
                    victron_data["system"]["Grid L1"] = registers[20]
                    victron_data["system"]["Grid L2"] = registers[21]
                    victron_data["system"]["Grid L3"] = registers[22]
                    victron_data["system"]["Genset L1"] = registers[23]
                    victron_data["system"]["Genset L2"] = registers[24]
                    victron_data["system"]["Genset L3"] = registers[25]
                    victron_data["system"]["Active input source"] = registers[26]

                response = client.read_input_registers(840, 7, unit=100)  # Reading from address 800 to 866
                if not response.isError():
                    registers = response.registers
                    _LOGGER.debug("Received data: %s", registers)  # Print received data for debugging
                    victron_data["system"]["Battery Voltage - System"] = registers[0] / 10.0
                    victron_data["system"]["Battery Current - System"] = registers[1] / 10.0
                    victron_data["system"]["Battery Power - System"] = registers[2]
                    victron_data["system"]["Battery State of Charge - System"] = registers[3]
                    victron_data["system"]["Battery state - System"] = registers[4]
                    victron_data["system"]["Battery Consumed Amphours - System"] = registers[5] / -10.0
                    victron_data["system"]["Battery Time to Go - System"] = registers[6] / 100.0

                response = client.read_input_registers(850, 2, unit=100)  # Reading from address 800 to 866
                if not response.isError():
                    registers = response.registers
                    _LOGGER.debug("Received data: %s", registers)  # Print received data for debugging
                    victron_data["system"]["PV - DC-coupled power"] = registers[0]
                    victron_data["system"]["PV - DC-coupled current"] = registers[1] / 10.0


                response = client.read_input_registers(855, 1, unit=100)  # Reading from address 800 to 866
                if not response.isError():
                    registers = response.registers
                    _LOGGER.debug("Received data: %s", registers)  # Print received data for debugging
                    victron_data["system"]["Charger power"] = registers[0]


                response = client.read_input_registers(860, 1, unit=100)  # Reading from address 800 to 866
                if not response.isError():
                    registers = response.registers
                    _LOGGER.debug("Received data: %s", registers)  # Print received data for debugging
                    victron_data["system"]["DC System Power"] = registers[0]


                response = client.read_input_registers(865, 2, unit=100)  # Reading from address 800 to 866
                if not response.isError():
                    registers = response.registers
                    _LOGGER.debug("Received data: %s", registers)  # Print received data for debugging
                    victron_data["system"]["VE.Bus charge current - System"] = registers[0] / 10.0
                    victron_data["system"]["VE.Bus charge power - System"] = registers[1]

                    return victron_data

                else:
                    _LOGGER.error("Error reading from Modbus device: %s", response)
        except Exception as e:
            _LOGGER.error("Error connecting or communicating with device: %s", str(e))
        finally:
            client.close()


    victron_data = await async_update_data()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="victron_gx",
        update_method=async_update_data,
        update_interval=timedelta(seconds=5),  # Define how often to fetch data
    )
    await coordinator.async_refresh() 

    serial_number = victron_data["system"]["serial"]
    # Add more sensors here
    setting_sensors = [
        OctopusSensor(coordinator, f"CCGX Relay 1 State - Victron GX {serial_number}", "CCGX Relay 1 state"),
        OctopusSensor(coordinator, f"CCGX Relay 2 State - Victron GX {serial_number}", "CCGX Relay 2 state"),
        OctopusSensor(coordinator, f"PV - AC-coupled on output L1 - Victron GX {serial_number}", "PV - AC-coupled on output L1", "w"),
        OctopusSensor(coordinator, f"PV - AC-coupled on output L2 - Victron GX {serial_number}", "PV - AC-coupled on output L2", "w"),
        OctopusSensor(coordinator, f"PV - AC-coupled on output L3 - Victron GX {serial_number}", "PV - AC-coupled on output L3", "w"),
        OctopusSensor(coordinator, f"PV - AC-coupled on input L1 - Victron GX {serial_number}", "PV - AC-coupled on input L1", "w"),
        OctopusSensor(coordinator, f"PV - AC-coupled on input L2 - Victron GX {serial_number}", "PV - AC-coupled on input L2", "w"),
        OctopusSensor(coordinator, f"PV - AC-coupled on input L3 - Victron GX {serial_number}", "PV - AC-coupled on input L3", "w"),
        OctopusSensor(coordinator, f"PV - AC-coupled on generator L1 - Victron GX {serial_number}", "PV - AC-coupled on generator L1", "w"),
        OctopusSensor(coordinator, f"PV - AC-coupled on generator L2 - Victron GX {serial_number}", "PV - AC-coupled on generator L2", "w"),
        OctopusSensor(coordinator, f"PV - AC-coupled on generator L3 - Victron GX {serial_number}", "PV - AC-coupled on generator L3", "w"),
        OctopusSensor(coordinator, f"AC Consumption L1 - Victron GX {serial_number}", "AC Consumption L1", "w"),
        OctopusSensor(coordinator, f"AC Consumption L2 - Victron GX {serial_number}", "AC Consumption L2", "w"),
        OctopusSensor(coordinator, f"AC Consumption L3 - Victron GX {serial_number}", "AC Consumption L3", "w"),
        OctopusSensor(coordinator, f"Grid L1 - Victron GX {serial_number}", "Grid L1", "w"),
        OctopusSensor(coordinator, f"Grid L2 - Victron GX {serial_number}", "Grid L2", "w"),
        OctopusSensor(coordinator, f"Grid L3 - Victron GX {serial_number}", "Grid L3", "w"),
        OctopusSensor(coordinator, f"Genset L1 - Victron GX {serial_number}", "Genset L1", "w"),
        OctopusSensor(coordinator, f"Genset L2 - Victron GX {serial_number}", "Genset L2", "w"),
        OctopusSensor(coordinator, f"Genset L3 - Victron GX {serial_number}", "Genset L3", "w"),
        OctopusSensor(coordinator, f"Active input source - Victron GX {serial_number}", "Active input source"),
        OctopusSensor(coordinator, f"Battery Voltage - System - Victron GX {serial_number}", "Battery Voltage - System", "v"),
        OctopusSensor(coordinator, f"Battery Current - System - Victron GX {serial_number}", "Battery Current - System", "A"),
        OctopusSensor(coordinator, f"Battery Power - System - Victron GX {serial_number}", "Battery Power - System", "w"),
        OctopusSensor(coordinator, f"Battery State of Charge - System - Victron GX {serial_number}", "Battery State of Charge - System", "%"),
        OctopusSensor(coordinator, f"Battery state - System - Victron GX {serial_number}", "Battery state - System"),
        OctopusSensor(coordinator, f"Battery Consumed Amphours - System - Victron GX {serial_number}", "Battery Consumed Amphours - System", "Ah"),
        OctopusSensor(coordinator, f"Battery Time to Go - System - Victron GX {serial_number}", "Battery Time to Go - System"),
        OctopusSensor(coordinator, f"PV - DC-coupled power - Victron GX {serial_number}", "PV - DC-coupled power", "w"),
        OctopusSensor(coordinator, f"PV - DC-coupled current - Victron GX {serial_number}", "PV - DC-coupled current", "A"),
        OctopusSensor(coordinator, f"Charger power - Victron GX {serial_number}", "Charger power", "w"),
        OctopusSensor(coordinator, f"DC System Power - Victron GX {serial_number}", "DC System Power", "w"),
        OctopusSensor(coordinator, f"VE.Bus charge current - System - Victron GX {serial_number}", "VE.Bus charge current - System", "w"),
        OctopusSensor(coordinator, f"VE.Bus charge power - System - Victron GX {serial_number}", "VE.Bus charge power - System", "w"),
        # Add more sensors here
    ]


    # Combine all sensor lists
    sensors = setting_sensors

    async_add_entities(sensors, True)

class OctopusSensor(CoordinatorEntity):
    def __init__(self, coordinator, name, time_key, unit=None, icon=None):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._name = name
        self._time_key = time_key  # Either 'serial', 'CCGX Relay 1 state', etc.
        self._unit = unit
        self._icon = icon
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name}"

    @property
    def unique_id(self):
        """Return a unique ID for this entity."""
        return f"{self._name}"

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return self._icon

    @property
    def state(self):
        if self._time_key in self.coordinator.data['system']:
            return self.coordinator.data['system'][self._time_key]
        else:
            _LOGGER.error("Key not found: %s", self._time_key)
            return None

    @property
    def unit_of_measurement(self):
        """Return the state of the sensor."""
        if self._unit:
            return self._unit