from homeassistant.helpers.entity import Entity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.components.binary_sensor import BinarySensorEntity
import serial
import time
import aiohttp
import json
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from ....const import (
    NAME,
    DOMAIN,
    VERSION,
    ATTRIBUTION,
)

_LOGGER = logging.getLogger(__name__)



# Usage example:
# commands = ["command1", "command2", "command3"]
# port = "/dev/ttyUSB0"  # Replace with your serial port
# responses = send_serial_commands(commands, port, baudrate=19200, timeout=2)
# for i, response in enumerate(responses):
#     _LOGGER.debug(f"Response {i + 1}: {response}")

async def SeplosV2BMS(hass, entry):
    def send_serial_commands(commands, port, baudrate=19200, timeout=2):
        responses = []
        _LOGGER.debug(commands)

        with serial.Serial(port, baudrate=baudrate, timeout=timeout) as ser:
            for command in commands:
                _LOGGER.debug(command)
                ser.write(command.encode())
                time.sleep(0.5)
                responses.append(ser.read(ser.in_waiting).decode().replace('\r', '').replace('\n', ''))
        _LOGGER.debug(responses)

        return responses

    ha_update_time = entry.data.get("sensor_update_frequency")
    usb_port = entry.data.get("usb_port")
    battery_address = entry.data.get("battery_address")
    name_prefix = entry.data.get("name_prefix")

    async def async_update_data():

        V2_COMMAND_ARRAY = {
            "0x00": ["~20004642E00200FD37\r", "~20004644E00200FD35\r", "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
            "0x01": ["~20004642E00215FD31\r", "~20004644E00200FD35\r", "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
            "0x02": ["~20004642E00200FD37\r", "~20004644E00200FD35\r", "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
            "0x03": ["~20004642E00200FD37\r", "~20004644E00200FD35\r", "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
        }

        _LOGGER.debug("BATTERY PACK SELECTED: %s", battery_address)
        commands = V2_COMMAND_ARRAY[battery_address]
        data = send_serial_commands(commands, usb_port, baudrate=19200, timeout=2)
        _LOGGER.debug("data: %s", data)
        info_str = data[0]
        if info_str.startswith("~"):
            info_str = info_str[1:]

        msg_wo_chk_sum = info_str[:-4]
        info_str = msg_wo_chk_sum[12:]
        _LOGGER.debug("info_str PACK SELECTED: %s", info_str)

        cursor = 4

        cellsCount = int(info_str[cursor:cursor+2], 16)
        cursor += 2
        cellVoltage = []
        temperatures = []
        for i in range(cellsCount):
            cellVoltage.append(int(info_str[cursor:cursor+4], 16))
            cursor += 4

        tempCount = int(info_str[cursor:cursor+2], 16)
        cursor += 2
        for i in range(tempCount):
            temperature = (int(info_str[cursor:cursor+4], 16) - 2731) / 10
            temperatures.append(temperature)
            cursor += 4

        current = int(info_str[cursor:cursor+4], 16)
        if current > 32767:
            current -= 65536 
        current /= 100 
        cursor += 4
        voltage = int(info_str[cursor:cursor+4], 16) / 100
        cursor += 4
        resCap = int(info_str[cursor:cursor+4], 16) / 100
        cursor += 4
        customNumber = int(info_str[cursor:cursor+2], 16)
        cursor += 2
        capacity = int(info_str[cursor:cursor+4], 16) / 100
        cursor += 4
        soc = int(info_str[cursor:cursor+4], 16) / 10
        cursor += 4
        ratedCapacity = int(info_str[cursor:cursor+4], 16) / 100
        cursor += 4
        cycles = int(info_str[cursor:cursor+4], 16)
        cursor += 4
        soh = int(info_str[cursor:cursor+4], 16) / 10
        cursor += 4
        portVoltage = int(info_str[cursor:cursor+4], 16) / 100

        return { 
                'binary_sensors': {},
                'sensors': {
                    'cellsCount': {
                        'state': cellsCount,
                        'name': f"{name_prefix}Number of Cells",
                        'unique_id': f"{name_prefix}Number of Cells",
                        'unit': "",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    }, 
                    'resCap': {
                        'state': resCap,
                        'name': f"{name_prefix}Residual Capacity",
                        'unique_id': f"{name_prefix}Residual Capacity",
                        'unit': "Ah",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    }, 
                    'capacity': {
                        'state': capacity,
                        'name': f"{name_prefix}Capacity",
                        'unique_id': f"{name_prefix}Capacity",
                        'unit': "Ah",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    }, 
                    'soc': {
                        'state': soc,
                        'name': f"{name_prefix}State of Charge",
                        'unique_id': f"{name_prefix}State of Charge",
                        'unit': "%",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    }, 
                    'ratedCapacity': {
                        'state': ratedCapacity,
                        'name': f"{name_prefix}Rated Capacity",
                        'unique_id': f"{name_prefix}Rated Capacity",
                        'unit': "Ah",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    }, 
                    'cycles': {
                        'state': cycles,
                        'name': f"{name_prefix}Cycles",
                        'unique_id': f"{name_prefix}Cycles",
                        'unit': "",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    }, 
                    'soh': {
                        'state': soh,
                        'name': f"{name_prefix}State of Health",
                        'unique_id': f"{name_prefix}State of Health",
                        'unit': "%",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    },  
                    'portVoltage': {
                        'state': portVoltage,
                        'name': f"{name_prefix}Port Voltage",
                        'unique_id': f"{name_prefix}Port Voltage",
                        'unit': "v",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    },                            
                    'current': {
                        'state': current,
                        'name': f"{name_prefix}Current",
                        'unique_id': f"{name_prefix}Current",
                        'unit': "A",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    },  
                    'voltage': {
                        'state': voltage,
                        'name': f"{name_prefix}Voltage",
                        'unique_id': f"{name_prefix}Voltage",
                        'unit': "v",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    },                   
                },
            }

    await async_update_data()

    hass.data[DOMAIN]["HOME_ENERGY_HUB_SENSOR_COORDINATOR"+entry.entry_id] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="home_energy_hub_"+entry.entry_id,
        update_method=async_update_data,
        update_interval=timedelta(seconds=ha_update_time),  # Define how often to fetch data
    )
    await hass.data[DOMAIN]["HOME_ENERGY_HUB_SENSOR_COORDINATOR"+entry.entry_id].async_refresh() 