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