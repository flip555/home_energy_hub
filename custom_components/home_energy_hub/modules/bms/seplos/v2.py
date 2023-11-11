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
ALARM_MAPPINGS = {
    "alarmEvent0": [
        "No Alarm", 
        "Alarm that analog quantity reaches the lower limit", 
        "Alarm that analog quantity reaches the upper limit", 
        "Other alarms"
    ],
    "alarmEvent1": [
        "Voltage sensor fault", 
        "Temperature sensor fault", 
        "Current sensor fault", 
        "Key switch fault", 
        "Cell voltage dropout fault", 
        "Charge switch fault", 
        "Discharge switch fault", 
        "Current limit switch fault"
    ],
    "alarmEvent2": [
        "Monomer high voltage alarm", 
        "Monomer overvoltage protection", 
        "Monomer low voltage alarm", 
        "Monomer under voltage protection", 
        "High voltage alarm for total voltage", 
        "Overvoltage protection for total voltage", 
        "Low voltage alarm for total voltage", 
        "Under voltage protection for total voltage"
    ],
    "alarmEvent3": [
        "Charge high temperature alarm", 
        "Charge over temperature protection", 
        "Charge low temperature alarm", 
        "Charge under temperature protection", 
        "Discharge high temperature alarm", 
        "Discharge over temperature protection", 
        "Discharge low temperature alarm", 
        "Discharge under temperature protection"
    ],
    "alarmEvent4": [
        "Environment high temperature alarm", 
        "Environment over temperature protection", 
        "Environment low temperature alarm", 
        "Environment under temperature protection", 
        "Power over temperature protection", 
        "Power high temperature alarm", 
        "Cell low temperature heating", 
        "Reservation bit"
    ],
    "alarmEvent5": [
        "Charge over current alarm", 
        "Charge over current protection", 
        "Discharge over current alarm", 
        "Discharge over current protection", 
        "Transient over current protection", 
        "Output short circuit protection", 
        "Transient over current lockout", 
        "Output short circuit lockout"
    ],
    "alarmEvent6": [
        "Charge high voltage protection", 
        "Intermittent recharge waiting", 
        "Residual capacity alarm", 
        "Residual capacity protection", 
        "Cell low voltage charging prohibition", 
        "Output reverse polarity protection", 
        "Output connection fault", 
        "Inside bit"
    ],
    "alarmEvent7": [
        "Inside bit", 
        "Inside bit", 
        "Inside bit", 
        "Inside bit", 
        "Automatic charging waiting", 
        "Manual charging waiting", 
        "Inside bit", 
        "Inside bit"
    ],
    "alarmEvent8": [
        "EEP storage fault", 
        "RTC error", 
        "Voltage calibration not performed", 
        "Current calibration not performed", 
        "Zero calibration not performed", 
        "Inside bit", 
        "Inside bit", 
        "Inside bit"
    ],
    "cellAlarm": {
        0: "No Alarm",
        1: "Alarm"
    },
    "tempAlarm": {
        0: "No Alarm",
        1: "Alarm"
    },
    "currentAlarm": {
        1: "Charge/Discharge Current Alarm"
    },
    "voltageAlarm": {
        1: "Total Battery Voltage Alarm"
    },
    "onOffState": [
        "Discharge switch state",
        "Charge switch state",
        "Current limit switch state",
        "Heating switch state",
        "Reservation bit",
        "Reservation bit",
        "Reservation bit",
        "Reservation bit"
    ],
    "equilibriumState0": [
        "Cell 01 equilibrium",
        "Cell 02 equilibrium",
        "Cell 03 equilibrium",
        "Cell 04 equilibrium",
        "Cell 05 equilibrium",
        "Cell 06 equilibrium",
        "Cell 07 equilibrium",
        "Cell 08 equilibrium"
    ],
    "equilibriumState1": [
        "Cell 09 equilibrium",
        "Cell 10 equilibrium",
        "Cell 11 equilibrium",
        "Cell 12 equilibrium",
        "Cell 13 equilibrium",
        "Cell 14 equilibrium",
        "Cell 15 equilibrium",
        "Cell 16 equilibrium"
    ],
    "systemState": [
        "Discharge",
        "Charge",
        "Floating charge",
        "Reservation bit",
        "Standby",
        "Shutdown",
        "Reservation bit",
        "Reservation bit"
    ],
    "disconnectionState0": [
        "Cell 01 disconnection",
        "Cell 02 disconnection",
        "Cell 03 disconnection",
        "Cell 04 disconnection",
        "Cell 05 disconnection",
        "Cell 06 disconnection",
        "Cell 07 disconnection",
        "Cell 08 disconnection"
    ],
    "disconnectionState1": [
        "Cell 09 disconnection",
        "Cell 10 disconnection",
        "Cell 11 disconnection",
        "Cell 12 disconnection",
        "Cell 13 disconnection",
        "Cell 14 disconnection",
        "Cell 15 disconnection",
        "Cell 16 disconnection"
    ]
}
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
    sensors = {}
    binary_sensors = {}

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

        # PROCESS 42H CODES
        info_str = data[0]
        if info_str.startswith("~"):
            info_str = info_str[1:]

        msg_wo_chk_sum = info_str[:-4]
        info_str = msg_wo_chk_sum[12:]
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

        # Assuming cellVoltage is a list containing the voltages of each cell
        highest_voltage = max(enumerate(cellVoltage), key=lambda x: x[1])
        lowest_voltage = min(enumerate(cellVoltage), key=lambda x: x[1])

        # highest_voltage and lowest_voltage are tuples in the form (index, value)
        highest_voltage_cell_number = highest_voltage[0] + 1  # Adding 1 because cell numbering usually starts from 1
        highest_voltage_value = highest_voltage[1]

        lowest_voltage_cell_number = lowest_voltage[0] + 1  # Adding 1 for the same reason
        lowest_voltage_value = lowest_voltage[1]
        cell_difference =  highest_voltage[1] - lowest_voltage[1]
        sensors = {
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
                    'battery_watts': {
                        'state': int(voltage * current),
                        'name': f"{name_prefix}Battery Watts",
                        'unique_id': f"{name_prefix}Battery Watts",
                        'unit': "w",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    }, 
                    'full_charge_watts': {
                        'state': int((capacity - resCap) * voltage),
                        'name': f"{name_prefix}Full Charge Watts",
                        'unique_id': f"{name_prefix}Full Charge Watts",
                        'unit': "w",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    }, 
                    'full_charge_amps': {
                        'state': int((capacity - resCap)),
                        'name': f"{name_prefix}Full Charge Amps",
                        'unique_id': f"{name_prefix}Full Charge Amps",
                        'unit': "Ah",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    },
                    'remaining_watts': {
                        'state': int(resCap * voltage),
                        'name': f"{name_prefix}Remaining Watts",
                        'unique_id': f"{name_prefix}Remaining Watts",
                        'unit': "w",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    }, 
                    'highest_cell_voltage': {
                        'state': highest_voltage_value,
                        'name': f"{name_prefix}Highest Cell Voltage",
                        'unique_id': f"{name_prefix}Highest Cell Voltage",
                        'unit': "mV",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    }, 
                    'highest_cell_number': {
                        'state': highest_voltage_cell_number,
                        'name': f"{name_prefix}Cell Number of Highest Voltage",
                        'unique_id': f"{name_prefix}Cell Number of Highest Voltage",
                        'unit': "",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    }, 
                    'lowest_cell_voltage': {
                        'state': lowest_voltage_value,
                        'name': f"{name_prefix}Lowest Cell Voltage",
                        'unique_id': f"{name_prefix}Lowest Cell Voltage",
                        'unit': "mV",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    }, 
                    'lowest_cell_number': {
                        'state': lowest_voltage_cell_number,
                        'name': f"{name_prefix}Cell Number of Lowest Voltage",
                        'unique_id': f"{name_prefix}Cell Number of Lowest Voltage",
                        'unit': "",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    }, 
                    'cell_difference': {
                        'state': cell_difference,
                        'name': f"{name_prefix}Cell Voltage Difference",
                        'unique_id': f"{name_prefix}Cell Voltage Difference",
                        'unit': "mV",
                        'icon': "",
                        'device_class': "",
                        'state_class': "",
                        'attributes': {},
                    }, 


            }


        for i in range(cellsCount):
            cell_voltage_key = f"cell_{i+1}_voltage"  # Create a unique key for each cell
            sensors[cell_voltage_key] = {
                'state': cellVoltage[i],
                'name': f"{name_prefix}Cell Voltage {i+1}",
                'unique_id': f"{name_prefix}Cell Voltage {i+1}",
                'unit': "mV",  # Assuming the unit is volts
                'icon': "mdi:battery",  # Example icon, you can change it
                'device_class': "",
                'state_class': "",
                'attributes': {},
            }
        for i, temp in enumerate(temperatures):
            if i < tempCount - 2:
                # For the first (tempCount - 2) temperatures, label them as Cell 1 Temp, Cell 2 Temp, etc.
                sensor_key = f"cell temperature {i+1}"
                sensor_name = f"{name_prefix}Cell Temperature {i+1}"
            elif i == tempCount - 2:
                # The second last temperature is Power Temp
                sensor_key = "power_temperature"
                sensor_name = f"{name_prefix}Power Temperature"
            else:
                # The last temperature is Environment Temp
                sensor_key = "environment_temperature"
                sensor_name = f"{name_prefix}Environment Temperature"

            sensors[sensor_key] = {
                'state': temp,
                'name': sensor_name,
                'unique_id': f"{name_prefix}{sensor_key}",
                'unit': "°C",  # Assuming the unit is Celsius
                'icon': "mdi:thermometer",  # Example icon, you can change it
                'device_class': "",
                'state_class': "",
                'attributes': {},
            }

        def get_value(data, attribute):
            """Retrieve the value from the data based on the attribute name."""
            # Check if the attribute name indicates list access (e.g., 'cellVoltages[0]')
            if '[' in attribute and ']' in attribute:
                attr, index = attribute.split('[')
                index = int(index.rstrip(']'))  # Convert index to integer
                # Check if the attribute exists in data and is a list
                if attr in data and isinstance(data[attr], list):
                    list_data = data[attr]
                    if index < len(list_data):
                        return list_data[index]  # Return the value at the specified index
            else:
                # For non-list attributes, directly access the dictionary
                return data.get(attribute, None)  # Safely return None if key doesn't exist

            return None  # Return None if attribute format is incorrect or index is out of range

        def interpret_alarm(event, value):
            """Interpret the alarm based on the event and value."""
            flags = ALARM_MAPPINGS.get(event, [])

            if not flags:
                return f"Unknown event: {event}"

            # Interpret the value as bit flags
            triggered_alarms = [flag for idx, flag in enumerate(flags) if value is not None and value & (1 << idx)]
            return ', '.join(str(alarm) for alarm in triggered_alarms) if triggered_alarms else "No Alarm"


        info_str = data[1]
        if info_str.startswith("~"):
            info_str = info_str[1:]

        msg_wo_chk_sum = info_str[:-4]
        info_str = msg_wo_chk_sum[12:]
        cursor = 4
        result = {}

        def remaining_length():
            return len(info_str) - cursor

        # Assign cellsCount to the result dictionary
        result['cellsCount'] = int(info_str[cursor:cursor+2], 16)
        cursor += 2

        # Initialize cellAlarm as a list in the result dictionary
        result['cellAlarm'] = []
        for i in range(result['cellsCount']):
            if remaining_length() < 2:
                return result
            result['cellAlarm'].append(int(info_str[cursor:cursor+2], 16))
            cursor += 2

        # Assign tempCount to the result dictionary
        result['tempCount'] = int(info_str[cursor:cursor+2], 16)
        cursor += 2

        # Initialize tempAlarm as a list in the result dictionary
        result['tempAlarm'] = []
        for i in range(result['tempCount']):
            if remaining_length() < 2:
                return result
            result['tempAlarm'].append(int(info_str[cursor:cursor+2], 16))
            cursor += 2

        # Add other attributes to the result dictionary
        for attribute in ['currentAlarm', 'voltageAlarm', 'customAlarms', 'alarmEvent0', 'alarmEvent1', 'alarmEvent2', 'alarmEvent3', 'alarmEvent4', 'alarmEvent5', 'onOffState', 'equilibriumState0', 'equilibriumState1', 'systemState', 'disconnectionState0', 'disconnectionState1', 'alarmEvent6', 'alarmEvent7']:
            if remaining_length() < 2:
                return result
            result[attribute] = int(info_str[cursor:cursor+2], 16)
            cursor += 2

        currentAlarm = interpret_alarm('currentAlarm', get_value(result, 'currentAlarm'))
        sensors["currentAlarm"] = {
            'state': currentAlarm,
            'name': f"{name_prefix}Current Alarm",
            'unique_id': f"{name_prefix}Current Alarm",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        voltageAlarm = interpret_alarm('voltageAlarm', get_value(result, 'voltageAlarm'))
        sensors["voltageAlarm"] = {
            'state': voltageAlarm,
            'name': f"{name_prefix}Voltage Alarm",
            'unique_id': f"{name_prefix}Voltage Alarm",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        customAlarms = interpret_alarm('customAlarms', get_value(result, 'customAlarms'))
        sensors["customAlarms"] = {
            'state': customAlarms,
            'name': f"{name_prefix}Custom Alarms",
            'unique_id': f"{name_prefix}Custom Alarms",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        alarmEvent0 = interpret_alarm('alarmEvent0', get_value(result, 'alarmEvent0'))
        sensors["alarmEvent0"] = {
            'state': alarmEvent0,
            'name': f"{name_prefix}Alarm Event 0",
            'unique_id': f"{name_prefix}Alarm Event 0",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        alarmEvent1 = interpret_alarm('alarmEvent1', get_value(result, 'alarmEvent1'))
        sensors["alarmEvent1"] = {
            'state': alarmEvent1,
            'name': f"{name_prefix}Alarm Event 1",
            'unique_id': f"{name_prefix}Alarm Event 1",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        alarmEvent2 = interpret_alarm('alarmEvent2', get_value(result, 'alarmEvent2'))
        sensors["alarmEvent2"] = {
            'state': alarmEvent2,
            'name': f"{name_prefix}Alarm Event 2",
            'unique_id': f"{name_prefix}Alarm Event 2",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        alarmEvent3 = interpret_alarm('alarmEvent3', get_value(result, 'alarmEvent3'))
        sensors["alarmEvent3"] = {
            'state': alarmEvent3,
            'name': f"{name_prefix}Alarm Event 3",
            'unique_id': f"{name_prefix}Alarm Event 3",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        alarmEvent4 = interpret_alarm('alarmEvent4', get_value(result, 'alarmEvent4'))
        sensors["alarmEvent4"] = {
            'state': alarmEvent4,
            'name': f"{name_prefix}Alarm Event 4",
            'unique_id': f"{name_prefix}Alarm Event 4",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        alarmEvent5 = interpret_alarm('alarmEvent5', get_value(result, 'alarmEvent5'))
        sensors["alarmEvent5"] = {
            'state': alarmEvent5,
            'name': f"{name_prefix}Alarm Event 5",
            'unique_id': f"{name_prefix}Alarm Event 5",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        alarmEvent6 = interpret_alarm('alarmEvent6', get_value(result, 'alarmEvent6'))
        sensors["alarmEvent6"] = {
            'state': alarmEvent6,
            'name': f"{name_prefix}Alarm Event 6",
            'unique_id': f"{name_prefix}Alarm Event 6",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        alarmEvent7 = interpret_alarm('alarmEvent7', get_value(result, 'alarmEvent7'))
        sensors["alarmEvent7"] = {
            'state': alarmEvent7,
            'name': f"{name_prefix}Alarm Event 7",
            'unique_id': f"{name_prefix}Alarm Event 7",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        onOffState = interpret_alarm('onOffState', get_value(result, 'onOffState'))
        sensors["onOffState"] = {
            'state': onOffState,
            'name': f"{name_prefix}On Off State",
            'unique_id': f"{name_prefix}On Off State",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        equilibriumState0 = interpret_alarm('equilibriumState0', get_value(result, 'equilibriumState0'))
        sensors["equilibriumState0"] = {
            'state': equilibriumState0,
            'name': f"{name_prefix}Equilibrium State 0",
            'unique_id': f"{name_prefix}Equilibrium State 0",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        equilibriumState1 = interpret_alarm('equilibriumState1', get_value(result, 'equilibriumState1'))
        sensors["equilibriumState1"] = {
            'state': equilibriumState1,
            'name': f"{name_prefix}Equilibrium State 1",
            'unique_id': f"{name_prefix}Equilibrium State 1",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }

        for i in range(cellsCount):
            if f"Cell 0{i+1}" in equilibriumState0 or f"Cell 0{i+1}" in equilibriumState1 or f"Cell {i+1}" in equilibriumState1:
                balancerActiveCell = True
            else:
                balancerActiveCell = False 
            balance_key = f"balancerActiveCell{i+1}"  # Create a unique key for each cell
            binary_sensors[balance_key] = {
                'state': balancerActiveCell,
                'name': f"{name_prefix}Balancer Active Cell {i+1}",
                'unique_id': f"{name_prefix}Balancer Active Cell {i+1}",
                'device_class': "",
                'state_class': "",
                'icon': "",  # Example icon, you can change it
                'attributes': {},
            }

        systemState = interpret_alarm('systemState', get_value(result, 'systemState'))
        sensors["systemState"] = {
            'state': systemState,
            'name': f"{name_prefix}System State",
            'unique_id': f"{name_prefix}System State",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        disconnectionState0 = interpret_alarm('disconnectionState0', get_value(result, 'disconnectionState0'))
        sensors["disconnectionState0"] = {
            'state': disconnectionState0,
            'name': f"{name_prefix}Disconnection State 0",
            'unique_id': f"{name_prefix}Disconnection State 0",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        disconnectionState1 = interpret_alarm('disconnectionState1', get_value(result, 'disconnectionState1'))
        sensors["disconnectionState1"] = {
            'state': disconnectionState1,
            'name': f"{name_prefix}Disconnection State 1",
            'unique_id': f"{name_prefix}Disconnection State 1",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }




        # PROCESS 42H CODES
        info_str = data[3]
        if info_str.startswith("~"):
            info_str = info_str[1:]

        msg_wo_chk_sum = info_str[:-4]
        hex_string = msg_wo_chk_sum[12:]
        cursor = 4

        hex_string = bytes.fromhex(hex_string)
        if len(hex_string) < 10:
            return None
        device_name_bytes = hex_string[0:10]
        software_version_bytes = hex_string[10:12]
        manufacturer_name_bytes = hex_string[12:24]

        # Convert bytes to ASCII strings
        device_name = device_name_bytes.decode('ascii')
        
        # Interpret the software version correctly
        software_version = int.from_bytes(software_version_bytes, byteorder='big') / 1000 * 4  # Really unsure if this is correct ... my version is 16.4 so * 4 made 4.1 16.4
        software_version = "{:.1f}".format(software_version)

        manufacturer_name = manufacturer_name_bytes.decode('ascii')

        sensors["device_name"] = {
            'state': device_name,
            'name': f"{name_prefix}Device Name",
            'unique_id': f"{name_prefix}Device Name",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        sensors["software_version"] = {
            'state': software_version,
            'name': f"{name_prefix}Software Version",
            'unique_id': f"{name_prefix}Software Version",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
        sensors["manufacturer_name"] = {
            'state': manufacturer_name,
            'name': f"{name_prefix}Manufacturer Name",
            'unique_id': f"{name_prefix}Manufacturer Name",
            'unit': "",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }

        info_str = data[2]
        if info_str.startswith("~"):
            info_str = info_str[1:]

        msg_wo_chk_sum = info_str[:-4]
        hex_string = msg_wo_chk_sum[12:]
        hex_string = bytes.fromhex(hex_string)
        if len(hex_string) < 10:
            return None, None, None

        soi = hex_string[0]
        ver = hex_string[1]
        adr = hex_string[2]
        infoflag = hex_string[3]
        
        # Extract length correctly
        length = int.from_bytes(hex_string[4:6], byteorder='big')
        
        # Extract datai correctly as bytes
        datai_start = 2
        datai_end = datai_start + length
        datai_bytes = hex_string[datai_start:datai_end]
        
        chksum = hex_string[-4:-2]
        eoi = hex_string[-2]


        # Convert DATAI to human-readable format
        datai_values = [
            int.from_bytes(datai_bytes[i:i+2], byteorder='big') 
            for i in range(0, len(datai_bytes), 2)
        ]

        datai_values = [
            # Monomer high voltage alarm: 3.550 V
            int.from_bytes(datai_bytes[0:2], byteorder='big') / 1000.0,

            # Monomer high pressure recovery: 3.400 V
            int.from_bytes(datai_bytes[2:4], byteorder='big') / 1000.0,

            # Monomer low pressure alarm: 2.900 V
            int.from_bytes(datai_bytes[4:6], byteorder='big') / 1000.0,

            # Monomer low pressure recovery: 3.000 V
            int.from_bytes(datai_bytes[6:8], byteorder='big') / 1000.0,

            # Monomer overvoltage protection: 3.650 V
            int.from_bytes(datai_bytes[8:10], byteorder='big') / 1000.0,

            # Monomer overvoltage recovery: 3.400 V
            int.from_bytes(datai_bytes[10:12], byteorder='big') / 1000.0,

            # Monomer undervoltage protection: 2.700 V
            int.from_bytes(datai_bytes[12:14], byteorder='big') / 1000.0,

            # Monomer undervoltage recovery: 2.900 V
            int.from_bytes(datai_bytes[14:16], byteorder='big') / 1000.0,

            # Equalization opening voltage: 3.400 V
            int.from_bytes(datai_bytes[16:18], byteorder='big') / 1000.0,

            # Battery low voltage forbidden charging: 1.500 V
            int.from_bytes(datai_bytes[18:20], byteorder='big') / 1000.0,

            # Total pressure high pressure alarm: 58.00 V
            int.from_bytes(datai_bytes[20:22], byteorder='big') / 100.0,

            # Total pressure and high pressure recovery: 54.40 V
            int.from_bytes(datai_bytes[22:24], byteorder='big') / 100.0,

            # Total pressure low pressure alarm: 46.40 V
            int.from_bytes(datai_bytes[24:26], byteorder='big') / 100.0,

            # Total pressure and low pressure recovery: 48.00 V
            int.from_bytes(datai_bytes[26:28], byteorder='big') / 100.0,

            # Total_voltage overvoltage protection: 56.80 V
            int.from_bytes(datai_bytes[28:30], byteorder='big') / 100.0,

            # Total pressure overpressure recovery: 54.40 V
            int.from_bytes(datai_bytes[30:32], byteorder='big') / 100.0,

            # Total_voltage undervoltage protection: 41.60 V
            int.from_bytes(datai_bytes[32:34], byteorder='big') / 100.0,

            # Total pressure undervoltage recovery: 46.00 V
            int.from_bytes(datai_bytes[34:36], byteorder='big') / 100.0,

            # Charging overvoltage protection: 56.80 V
            int.from_bytes(datai_bytes[36:38], byteorder='big') / 100.0,

            # Charging overvoltage recovery: 56.80 V
            int.from_bytes(datai_bytes[38:40], byteorder='big') / 100.0,

            # Charging high temperature warning: 50.0 ℃
            (int.from_bytes(datai_bytes[40:42], byteorder='big')  - 2731) / 10.0,

            # Charging high temperature recovery: 47.0 ℃
            (int.from_bytes(datai_bytes[42:44], byteorder='big')  - 2731) / 10.0,

            # Charging low temperature warning: 2.0 ℃
            (int.from_bytes(datai_bytes[44:46], byteorder='big')  - 2731) / 10.0,

            # Charging low temperature recovery: 5.0 ℃
            (int.from_bytes(datai_bytes[46:48], byteorder='big')  - 2731) / 10.0,

            # Charging over temperature protection: 55.0 ℃
            (int.from_bytes(datai_bytes[48:50], byteorder='big')  - 2731) / 10.0,

            # Charging over temperature recovery: 50.0 ℃
            (int.from_bytes(datai_bytes[50:52], byteorder='big')  - 2731) / 10.0,

            # Charging under-temperature protection: -10.0 ℃
            (int.from_bytes(datai_bytes[52:54], byteorder='big')  - 2731) / 10.0,

            # Charging under temperature recovery: 0.0 ℃
            (int.from_bytes(datai_bytes[54:56], byteorder='big')  - 2731) / 10.0,

            # Discharge high temperature warning: 52.0 ℃
            (int.from_bytes(datai_bytes[56:58], byteorder='big')  - 2731) / 10.0,

            # Discharge high temperature recovery: 47.0 ℃
            (int.from_bytes(datai_bytes[58:60], byteorder='big')  - 2731) / 10.0,

            # Discharge low temperature warning: -10.0 ℃
            (int.from_bytes(datai_bytes[60:62], byteorder='big')  - 2731) / 10.0,

            # Discharge low temperature recovery: 3.0 ℃
            (int.from_bytes(datai_bytes[62:64], byteorder='big')  - 2731) / 10.0,

            # Discharge over temperature protection: 60.0 ℃
            (int.from_bytes(datai_bytes[64:66], byteorder='big')  - 2731) / 10.0,

            # Discharge over temperature recovery: 55.0 ℃
            (int.from_bytes(datai_bytes[66:68], byteorder='big')  - 2731) / 10.0,

            # Discharge under temperature protection: -20.0 ℃
            (int.from_bytes(datai_bytes[68:70], byteorder='big')  - 2731) / 10.0,

            # Discharge under temperature recovery: -10.0 ℃
            (int.from_bytes(datai_bytes[70:72], byteorder='big')  - 2731) / 10.0,

            # Cell low temperature heating
            (int.from_bytes(datai_bytes[72:74], byteorder='big')  - 2731) / 10.0,

            # Cell heating recovery
            (int.from_bytes(datai_bytes[74:76], byteorder='big')  - 2731) / 10.0,

            # Ambient high temperature alarm
            (int.from_bytes(datai_bytes[76:78], byteorder='big')  - 2731) / 10.0,

            # Ambient high temperature recovery
            (int.from_bytes(datai_bytes[78:80], byteorder='big')  - 2731) / 10.0,

            # Ambient low temperature alarm
            (int.from_bytes(datai_bytes[80:82], byteorder='big')  - 2731) / 10.0,

            # Ambient low temperature recovery
            (int.from_bytes(datai_bytes[82:84], byteorder='big')  - 2731) / 10.0,

            # Environmental over-temperature protection
            (int.from_bytes(datai_bytes[84:86], byteorder='big')  - 2731) / 10.0,

            # Environmental overtemperature recovery
            (int.from_bytes(datai_bytes[86:88], byteorder='big')  - 2731) / 10.0,

            # Environmental under-temperature protection
            (int.from_bytes(datai_bytes[88:90], byteorder='big')  - 2731) / 10.0,

            # Environmental undertemperature recovery
            (int.from_bytes(datai_bytes[90:92], byteorder='big')  - 2731) / 10.0,

            # Power high temperature alarm
            (int.from_bytes(datai_bytes[92:94], byteorder='big')  - 2731) / 10.0,

            # Power high temperature recovery
            (int.from_bytes(datai_bytes[94:96], byteorder='big')  - 2731) / 10.0,

            # Power over temperature protection
            (int.from_bytes(datai_bytes[96:98], byteorder='big')  - 2731) / 10.0,

            # Power over temperature recovery
            (int.from_bytes(datai_bytes[98:100], byteorder='big')  - 2731) / 10.0,

            # Charging overcurrent warning
            int.from_bytes(datai_bytes[100:102], byteorder='big') / 10.0,

            # Charging overcurrent recovery
            int.from_bytes(datai_bytes[102:104], byteorder='big') / 10.0,

            # Discharge overcurrent warning
            int.from_bytes(datai_bytes[104:106], byteorder='big') / 10.0,

            # Discharge overcurrent recovery
            int.from_bytes(datai_bytes[106:108], byteorder='big') / 10.0,

            # Charge overcurrent protection
            int.from_bytes(datai_bytes[108:110], byteorder='big') / 10.0,

            # Discharge overcurrent protection
            int.from_bytes(datai_bytes[110:112], byteorder='big') / 10.0,

            # Transient overcurrent protection
            int.from_bytes(datai_bytes[112:114], byteorder='big') / 10.0,


            # Output soft start delay
            int.from_bytes(datai_bytes[114:116], byteorder='big') / 1000.0,

            # Battery rated capacity
            int.from_bytes(datai_bytes[116:118], byteorder='big') / 100.0,

            # SOC
            int.from_bytes(datai_bytes[118:120], byteorder='big') / 100.0,

            # Cell invalidation differential pressure
            int.from_bytes(datai_bytes[120:122], byteorder='big') / 1000.0,

            # Cell invalidation recovery
            int.from_bytes(datai_bytes[122:124], byteorder='big') / 1000.0,

            # Equalization opening pressure difference
            int.from_bytes(datai_bytes[124:126], byteorder='big') / 1000.0,

            # Equalization closing pressure difference
            int.from_bytes(datai_bytes[126:128], byteorder='big') / 1000.0,

            # Static equilibrium time
            int.from_bytes(datai_bytes[128:130], byteorder='big'),

            # Battery number in series
            int.from_bytes(datai_bytes[130:132], byteorder='big'),

            # Charge overcurrent delay
            int.from_bytes(datai_bytes[132:134], byteorder='big'),

            # Discharge overcurrent delay
            int.from_bytes(datai_bytes[134:136], byteorder='big'),

            # Transient overcurrent delay
            int.from_bytes(datai_bytes[136:138], byteorder='big'),

            # Overcurrent delay recovery
            int.from_bytes(datai_bytes[138:140], byteorder='big'),

            # Overcurrent recovery times
            int.from_bytes(datai_bytes[140:142], byteorder='big'),

            # Charge current limit delay
            int.from_bytes(datai_bytes[142:144], byteorder='big'),

            # Charge activation delay
            int.from_bytes(datai_bytes[144:146], byteorder='big'),

            # Charging activation interval
            int.from_bytes(datai_bytes[146:148], byteorder='big'),

            # Charge activation times
            int.from_bytes(datai_bytes[148:150], byteorder='big'),

            # Work record interval
            int.from_bytes(datai_bytes[150:152], byteorder='big'),

            # Standby recording interval
            int.from_bytes(datai_bytes[152:154], byteorder='big'),

            # Standby shutdown delay
            int.from_bytes(datai_bytes[154:156], byteorder='big'),

            # Remaining capacity alarm
            int.from_bytes(datai_bytes[156:158], byteorder='big') / 100.0,

            # Remaining capacity protection
            int.from_bytes(datai_bytes[158:160], byteorder='big') / 100.0,

            # Interval charge capacity
            int.from_bytes(datai_bytes[160:162], byteorder='big') / 100.0,

            # Cycle cumulative capacity
            int.from_bytes(datai_bytes[162:164], byteorder='big') / 100.0,

            # Connection fault impedance
            int.from_bytes(datai_bytes[164:166], byteorder='big'),

            # Compensation point 1 position
            int.from_bytes(datai_bytes[166:168], byteorder='big'),

            # Compensation point 1 impedance
            int.from_bytes(datai_bytes[168:170], byteorder='big'),

            # Compensation point 2 position
            int.from_bytes(datai_bytes[170:172], byteorder='big'),

            # Compensation point 2 impedance
            int.from_bytes(datai_bytes[172:174], byteorder='big')

        ]      
 # Assign the calculated values to the result object
# monomer_high_voltage_alarm = datai_values[0]
        sensors["monomer_high_voltage_alarm"] = {
            'state': datai_values[0],
            'name': f"{name_prefix}Monomer High Voltage Alarm",
            'unique_id': f"{name_prefix}Monomer High Voltage Alarm",
            'unit': "v",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
# monomer_high_pressure_recovery = datai_values[1]
        sensors["monomer_high_pressure_recovery"] = {
            'state': datai_values[1],
            'name': f"{name_prefix}Monomer High Pressure Recovery",
            'unique_id': f"{name_prefix}Monomer High Pressure Recovery",
            'unit': "v",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
# monomer_low_pressure_alarm = datai_values[2]
        sensors["monomer_low_pressure_alarm"] = {
            'state': datai_values[2],
            'name': f"{name_prefix}Monomer Low Pressure Alarm",
            'unique_id': f"{name_prefix}Monomer High Pressure Alarm",
            'unit': "v",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
# monomer_low_pressure_recovery = datai_values[3]
        sensors["monomer_low_pressure_recovery"] = {
            'state': datai_values[3],
            'name': f"{name_prefix}Monomer Low Pressure Recovery",
            'unique_id': f"{name_prefix}Monomer Low Pressure Recovery",
            'unit': "v",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
# monomer_overvoltage_protection = datai_values[4]
        sensors["monomer_overvoltage_protection"] = {
            'state': datai_values[4],
            'name': f"{name_prefix}Monomer Overvoltage Protection",
            'unique_id': f"{name_prefix}Monomer Overvoltage Protection",
            'unit': "v",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }
# monomer_overvoltage_recovery = datai_values[5]
# monomer_undervoltage_protection = datai_values[6]
# monomer_undervoltage_recovery = datai_values[7]
# equalization_opening_voltage = datai_values[8]
# battery_low_voltage_forbidden_charging = datai_values[9]
# total_pressure_high_pressure_alarm = datai_values[10]
# total_pressure_high_pressure_recovery = datai_values[11]
# total_pressure_low_pressure_alarm = datai_values[12]
# total_pressure_low_pressure_recovery = datai_values[13]
# total_voltage_overvoltage_protection = datai_values[14]
# total_pressure_overpressure_recovery = datai_values[15]
# total_voltage_undervoltage_protection = datai_values[16]
# total_pressure_undervoltage_recovery = datai_values[17]
# charging_overvoltage_protection = datai_values[18]
# charging_overvoltage_recovery = datai_values[19]
# charging_high_temperature_warning = datai_values[20]
# charging_high_temperature_recovery = datai_values[21]
# charging_low_temperature_warning = datai_values[22]
# charging_low_temperature_recovery = datai_values[23]
# charging_over_temperature_protection = datai_values[24]
# charging_over_temperature_recovery = datai_values[25]
# charging_under_temperature_protection = datai_values[26]
# charging_under_temperature_recovery = datai_values[27]
# discharge_high_temperature_warning = datai_values[28]
# discharge_high_temperature_recovery = datai_values[29]
# discharge_low_temperature_warning = datai_values[30]
# discharge_low_temperature_recovery = datai_values[31]
# discharge_over_temperature_protection = datai_values[32]
# discharge_over_temperature_recovery = datai_values[33]
# discharge_under_temperature_protection = datai_values[34]
# discharge_under_temperature_recovery = datai_values[35]
# cell_low_temperature_heating = datai_values[36]
# cell_heating_recovery = datai_values[37]
# ambient_high_temperature_alarm = datai_values[38]
# ambient_high_temperature_recovery = datai_values[39]
# ambient_low_temperature_alarm = datai_values[40]
# ambient_low_temperature_recovery = datai_values[41]
# environmental_over_temperature_protection = datai_values[42]
# environmental_overtemperature_recovery = datai_values[43]
# environmental_under_temperature_protection = datai_values[44]
# environmental_undertemperature_recovery = datai_values[45]
# power_high_temperature_alarm = datai_values[46]
# power_high_temperature_recovery = datai_values[47]
# power_over_temperature_protection = datai_values[48]
# power_over_temperature_recovery = datai_values[49]
# charging_overcurrent_warning = datai_values[50]
# charging_overcurrent_recovery = datai_values[51]
# discharge_overcurrent_warning = datai_values[52]
# discharge_overcurrent_recovery = datai_values[53]
# charge_overcurrent_protection = datai_values[54]
# discharge_overcurrent_protection = datai_values[55]
# transient_overcurrent_protection = datai_values[56]
# output_soft_start_delay = datai_values[57]
# battery_rated_capacity = datai_values[58]
# soc_ah = datai_values[59]
# cell_invalidation_differential_pressure = datai_values[60]
# cell_invalidation_recovery = datai_values[61]
# equalization_opening_pressure_difference = datai_values[62]
# equalization_closing_pressure_difference = datai_values[63]
# static_equilibrium_time = datai_values[64]
# battery_number_in_series = datai_values[65]
# charge_overcurrent_delay = datai_values[66]
# discharge_overcurrent_delay = datai_values[67]
# transient_overcurrent_delay = datai_values[68]
# overcurrent_delay_recovery = datai_values[69]
# overcurrent_recovery_times = datai_values[70]
# charge_current_limit_delay = datai_values[71]
# charge_activation_delay = datai_values[72]
# charging_activation_interval = datai_values[73]
# charge_activation_times = datai_values[74]
# work_record_interval = datai_values[75]
# standby_recording_interval = datai_values[76]
# standby_shutdown_delay = datai_values[77]
# remaining_capacity_alarm = datai_values[78]
# remaining_capacity_protection = datai_values[79]
# interval_charge_capacity = datai_values[80]
# cycle_cumulative_capacity = datai_values[81]
# connection_fault_impedance = datai_values[82]
# compensation_point_1_position = datai_values[83]
# compensation_point_1_impedance = datai_values[84]
# compensation_point_2_position = datai_values[85]
# compensation_point_2_impedance = datai_values[86]
        # Assign the calculated values to the result object
        sensors["monomer_high_voltage_alarm"] = {
            'state': datai_values[0],
            'name': f"{name_prefix}Monomer High Voltage Alarm",
            'unique_id': f"{name_prefix}Monomer High Voltage Alarm",
            'unit': "v",  # Assuming the unit is Celsius
            'icon': "",  # Example icon, you can change it
            'device_class': "",
            'state_class': "",
            'attributes': {},
        }





        return {
                'binary_sensors': binary_sensors,
                'sensors': sensors
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