"""Seplos V2 response parsing."""

import logging
from typing import Dict, Any, List

from ...const import ALARM_MAPPINGS, CONF_NAME_PREFIX

_LOGGER = logging.getLogger(__name__)

def parse_seplos_response(data: List[str], config: dict) -> Dict[str, Any]:
    """Parse Seplos V2 response data into sensor data."""
    if not data or len(data) < 4:
        _LOGGER.warning("Insufficient data received: %s", data)
        return {}
    
    _LOGGER.debug("Raw data packets received: %s", [d[:50] + "..." if len(d) > 50 else d for d in data])

    name_prefix = config.get(CONF_NAME_PREFIX, "Seplos ")
    processed_data = {}
    
    try:
        # Process 42H codes (first data packet)
        processed_data.update(_parse_42h_codes(data[0], name_prefix))
        
        # Process 44H codes (second data packet) - alarms and states
        processed_data.update(_parse_44h_codes(data[1], name_prefix))
        
        # Process 47H codes (third data packet) - battery settings
        settings_data = _parse_47h_codes(data[2], name_prefix)
        # Add "_settings" suffix to all settings keys to distinguish them from BMS data
        settings_data_with_suffix = {f"{key}_settings": value for key, value in settings_data.items()}
        _LOGGER.debug("47H codes (settings) keys with suffix: %s", list(settings_data_with_suffix.keys()))
        processed_data.update(settings_data_with_suffix)
        
        # Process 51H codes (fourth data packet) - device info
        processed_data.update(_parse_51h_codes(data[3], name_prefix))
        
        # Add cell voltage sensors for each cell
        if 'cellVoltage' in processed_data:
            # Get equilibrium states from 44H codes parsing
            equilibrium_state0 = processed_data.get('equilibriumState0_raw', 0)
            equilibrium_state1 = processed_data.get('equilibriumState1_raw', 0)
            highest_voltage = processed_data.get('highest_cell_voltage', 0)
            lowest_voltage = processed_data.get('lowest_cell_voltage', 0)
            
            processed_data.update(_create_cell_voltage_sensors(
                processed_data['cellVoltage'],
                name_prefix,
                highest_voltage,
                lowest_voltage,
                equilibrium_state0,
                equilibrium_state1
            ))
            # Remove the original list to avoid sensor creation
            del processed_data['cellVoltage']
            
        # Add temperature sensors
        if 'temperatures' in processed_data:
            processed_data.update(_create_temperature_sensors(processed_data['temperatures'], name_prefix))
            # Remove the original list to avoid sensor creation
            del processed_data['temperatures']
            
    except Exception as err:
        _LOGGER.error("Error parsing Seplos V2 data: %s", err)
        return {}
        
    return processed_data

def _parse_42h_codes(info_str: str, name_prefix: str) -> Dict[str, Any]:
    """Parse 42H codes (main battery data)."""
    if info_str.startswith("~"):
        info_str = info_str[1:]
        
    msg_wo_chk_sum = info_str[:-4]
    info_str = msg_wo_chk_sum[12:]
    cursor = 4

    cellsCount = int(info_str[cursor:cursor+2], 16)
    cursor += 2
    
    cellVoltage = []
    for _ in range(cellsCount):
        cellVoltage.append(int(info_str[cursor:cursor+4], 16))
        cursor += 4

    tempCount = int(info_str[cursor:cursor+2], 16)
    cursor += 2
    
    temperatures = []
    for _ in range(tempCount):
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

    # Add customNumber to returned data

    # Calculate derived values
    highest_voltage = max(enumerate(cellVoltage), key=lambda x: x[1])
    lowest_voltage = min(enumerate(cellVoltage), key=lambda x: x[1])
    highest_voltage_cell_number = highest_voltage[0] + 1
    highest_voltage_value = highest_voltage[1]
    lowest_voltage_cell_number = lowest_voltage[0] + 1
    lowest_voltage_value = lowest_voltage[1]
    cell_difference = highest_voltage_value - lowest_voltage_value
    nominal_voltage = cellsCount * 3.3125

    return {
        'cellsCount': cellsCount,
        'cellVoltage': cellVoltage,
        'temperatures': temperatures,
        'current': current,
        'voltage': voltage,
        'resCap': resCap,
        'capacity': capacity,
        'soc': soc,
        'ratedCapacity': ratedCapacity,
        'cycles': cycles,
        'soh': soh,
        'portVoltage': portVoltage,
        'customNumber': customNumber,  # Add missing customNumber
        'highest_cell_voltage': highest_voltage_value,
        'highest_cell_number': highest_voltage_cell_number,
        'lowest_cell_voltage': lowest_voltage_value,
        'lowest_cell_number': lowest_voltage_cell_number,
        'cell_difference': cell_difference,
        'battery_watts': int(voltage * current),
        'full_charge_watts': int((capacity - resCap) * nominal_voltage),
        'full_charge_amps': int((capacity - resCap)),
        'remaining_watts': int(resCap * nominal_voltage),
        'capacity_watts': nominal_voltage * capacity,
    }

def _parse_44h_codes(info_str: str, name_prefix: str) -> Dict[str, Any]:
    """Parse 44H codes (alarms and states)."""
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
    for _ in range(result['cellsCount']):
        if remaining_length() < 2:
            return result
        result['cellAlarm'].append(int(info_str[cursor:cursor+2], 16))
        cursor += 2

    # Assign tempCount to the result dictionary
    result['tempCount'] = int(info_str[cursor:cursor+2], 16)
    cursor += 2

    # Initialize tempAlarm as a list in the result dictionary
    result['tempAlarm'] = []
    for _ in range(result['tempCount']):
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

    # Interpret alarms and states
    interpreted_data = {}
    for alarm_key in ['currentAlarm', 'voltageAlarm', 'alarmEvent0', 'alarmEvent1', 'alarmEvent2', 'alarmEvent3', 'alarmEvent4', 'alarmEvent5', 'alarmEvent6', 'alarmEvent7', 'onOffState', 'equilibriumState0', 'equilibriumState1', 'systemState', 'disconnectionState0', 'disconnectionState1']:
        if alarm_key in result:
            interpreted_data[alarm_key] = _interpret_alarm(alarm_key, result[alarm_key])
    
    # Store raw equilibrium states for cell voltage attributes
    interpreted_data['equilibriumState0_raw'] = result.get('equilibriumState0', 0)
    interpreted_data['equilibriumState1_raw'] = result.get('equilibriumState1', 0)

    # Generate binary sensor data for balancing states
    equilibrium_state0 = result.get('equilibriumState0', 0)
    equilibrium_state1 = result.get('equilibriumState1', 0)
    
    # Create binary sensor entries for each cell's balancing state
    for i in range(result['cellsCount']):
        if i < 8:
            # Check equilibriumState0 bits (cells 1-8)
            balancer_active = bool(equilibrium_state0 & (1 << i))
        else:
            # Check equilibriumState1 bits (cells 9-16)
            balancer_active = bool(equilibrium_state1 & (1 << (i - 8)))
        
        interpreted_data[f'balancerActiveCell{i+1}'] = balancer_active

    return interpreted_data

def _parse_47h_codes(info_str: str, name_prefix: str) -> Dict[str, Any]:
    """Parse 47H codes (battery settings)."""
    if info_str.startswith("~"):
        info_str = info_str[1:]

    msg_wo_chk_sum = info_str[:-4]
    hex_string = msg_wo_chk_sum[12:]
    
    hex_bytes = bytes.fromhex(hex_string)
    if len(hex_bytes) < 10:
        return {}

    # Extract datai correctly as bytes
    datai_start = 2
    datai_end = datai_start + len(hex_bytes) - 6  # Adjust for SOI, VER, ADR, INFOFLAG, LENGTH, CHKSUM, EOI
    datai_bytes = hex_bytes[datai_start:datai_end]

    settings = {}
    
    # Monomer voltage settings (divided by 1000.0 for volts)
    settings["monomer_high_voltage_alarm"] = int.from_bytes(datai_bytes[0:2], byteorder='big') / 1000.0
    settings["monomer_high_pressure_recovery"] = int.from_bytes(datai_bytes[2:4], byteorder='big') / 1000.0
    settings["monomer_low_pressure_alarm"] = int.from_bytes(datai_bytes[4:6], byteorder='big') / 1000.0
    settings["monomer_low_pressure_recovery"] = int.from_bytes(datai_bytes[6:8], byteorder='big') / 1000.0
    settings["monomer_overvoltage_protection"] = int.from_bytes(datai_bytes[8:10], byteorder='big') / 1000.0
    settings["monomer_overvoltage_recovery"] = int.from_bytes(datai_bytes[10:12], byteorder='big') / 1000.0
    settings["monomer_undervoltage_protection"] = int.from_bytes(datai_bytes[12:14], byteorder='big') / 1000.0
    settings["monomer_undervoltage_recovery"] = int.from_bytes(datai_bytes[14:16], byteorder='big') / 1000.0
    
    # Equalization and battery settings
    settings["equalization_opening_voltage"] = int.from_bytes(datai_bytes[16:18], byteorder='big') / 1000.0
    settings["battery_low_voltage_forbidden_charging"] = int.from_bytes(datai_bytes[18:20], byteorder='big') / 1000.0
    
    # Total voltage settings (divided by 100.0 for volts)
    settings["total_pressure_high_pressure_alarm"] = int.from_bytes(datai_bytes[20:22], byteorder='big') / 100.0
    settings["total_pressure_high_pressure_recovery"] = int.from_bytes(datai_bytes[22:24], byteorder='big') / 100.0
    settings["total_pressure_low_pressure_alarm"] = int.from_bytes(datai_bytes[24:26], byteorder='big') / 100.0
    settings["total_pressure_low_pressure_recovery"] = int.from_bytes(datai_bytes[26:28], byteorder='big') / 100.0
    settings["total_voltage_overvoltage_protection"] = int.from_bytes(datai_bytes[28:30], byteorder='big') / 100.0
    settings["total_pressure_overpressure_recovery"] = int.from_bytes(datai_bytes[30:32], byteorder='big') / 100.0
    settings["total_voltage_undervoltage_protection"] = int.from_bytes(datai_bytes[32:34], byteorder='big') / 100.0
    settings["total_pressure_undervoltage_recovery"] = int.from_bytes(datai_bytes[34:36], byteorder='big') / 100.0
    
    # Charging voltage settings
    settings["charging_overvoltage_protection"] = int.from_bytes(datai_bytes[36:38], byteorder='big') / 100.0
    settings["charging_overvoltage_recovery"] = int.from_bytes(datai_bytes[38:40], byteorder='big') / 100.0
    
    # Temperature settings (convert from Kelvin)
    def kelvin_to_celsius(kelvin_value):
        return (kelvin_value - 2731) / 10.0
    
    settings["charging_high_temperature_warning"] = kelvin_to_celsius(int.from_bytes(datai_bytes[40:42], byteorder='big'))
    settings["charging_high_temperature_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[42:44], byteorder='big'))
    settings["charging_low_temperature_warning"] = kelvin_to_celsius(int.from_bytes(datai_bytes[44:46], byteorder='big'))
    settings["charging_low_temperature_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[46:48], byteorder='big'))
    settings["charging_over_temperature_protection"] = kelvin_to_celsius(int.from_bytes(datai_bytes[48:50], byteorder='big'))
    settings["charging_over_temperature_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[50:52], byteorder='big'))
    settings["charging_under_temperature_protection"] = kelvin_to_celsius(int.from_bytes(datai_bytes[52:54], byteorder='big'))
    settings["charging_under_temperature_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[54:56], byteorder='big'))
    
    # Discharge temperature settings
    settings["discharge_high_temperature_warning"] = kelvin_to_celsius(int.from_bytes(datai_bytes[56:58], byteorder='big'))
    settings["discharge_high_temperature_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[58:60], byteorder='big'))
    settings["discharge_low_temperature_warning"] = kelvin_to_celsius(int.from_bytes(datai_bytes[60:62], byteorder='big'))
    settings["discharge_low_temperature_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[62:64], byteorder='big'))
    settings["discharge_over_temperature_protection"] = kelvin_to_celsius(int.from_bytes(datai_bytes[64:66], byteorder='big'))
    settings["discharge_over_temperature_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[66:68], byteorder='big'))
    settings["discharge_under_temperature_protection"] = kelvin_to_celsius(int.from_bytes(datai_bytes[68:70], byteorder='big'))
    settings["discharge_under_temperature_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[70:72], byteorder='big'))
    
    # Cell temperature settings
    settings["cell_low_temperature_heating"] = kelvin_to_celsius(int.from_bytes(datai_bytes[72:74], byteorder='big'))
    settings["cell_heating_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[74:76], byteorder='big'))
    
    # Ambient and environment temperature settings
    settings["ambient_high_temperature_alarm"] = kelvin_to_celsius(int.from_bytes(datai_bytes[76:78], byteorder='big'))
    settings["ambient_high_temperature_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[78:80], byteorder='big'))
    settings["ambient_low_temperature_alarm"] = kelvin_to_celsius(int.from_bytes(datai_bytes[80:82], byteorder='big'))
    settings["ambient_low_temperature_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[82:84], byteorder='big'))
    settings["environment_over_temperature_protection"] = kelvin_to_celsius(int.from_bytes(datai_bytes[84:86], byteorder='big'))
    settings["environment_over_temperature_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[86:88], byteorder='big'))
    settings["environment_under_temperature_protection"] = kelvin_to_celsius(int.from_bytes(datai_bytes[88:90], byteorder='big'))
    settings["environment_under_temperature_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[90:92], byteorder='big'))
    
    # Power temperature settings
    settings["power_high_temperature_alarm"] = kelvin_to_celsius(int.from_bytes(datai_bytes[92:94], byteorder='big'))
    settings["power_high_temperature_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[94:96], byteorder='big'))
    settings["power_over_temperature_protection"] = kelvin_to_celsius(int.from_bytes(datai_bytes[96:98], byteorder='big'))
    settings["power_over_temperature_recovery"] = kelvin_to_celsius(int.from_bytes(datai_bytes[98:100], byteorder='big'))
    
    # Current settings (divided by 100.0 for amps)
    settings["charging_overcurrent_warning"] = int.from_bytes(datai_bytes[100:102], byteorder='big') / 100.0
    settings["charging_overcurrent_recovery"] = int.from_bytes(datai_bytes[102:104], byteorder='big') / 100.0
    
    def signed_current(value_bytes):
        value = int.from_bytes(value_bytes, byteorder='big')
        if value > 32767:
            value -= 65536
        return value / 100.0
    
    settings["discharge_overcurrent_warning"] = signed_current(datai_bytes[104:106])
    settings["discharge_overcurrent_recovery"] = signed_current(datai_bytes[106:108])
    settings["charge_overcurrent_protection"] = int.from_bytes(datai_bytes[108:110], byteorder='big') / 100.0
    settings["discharge_overcurrent_protection"] = signed_current(datai_bytes[110:112])
    settings["transient_overcurrent_protection"] = signed_current(datai_bytes[112:114]) / 100.0
    
    # Timing and delay settings
    settings["output_soft_start_delay"] = int.from_bytes(datai_bytes[114:116], byteorder='big')
    settings["battery_rated_capacity"] = int.from_bytes(datai_bytes[116:118], byteorder='big') / 100.0
    settings["soc_ah"] = int.from_bytes(datai_bytes[118:120], byteorder='big') / 100.0
    
    # Cell invalidation and equalization settings
    settings["cell_invalidation_recovery"] = int.from_bytes(datai_bytes[120:121], byteorder='big')
    settings["cell_invalidation_differential_pressure"] = int.from_bytes(datai_bytes[121:122], byteorder='big')
    settings["equalization_opening_pressure_difference"] = int.from_bytes(datai_bytes[122:123], byteorder='big')
    settings["equalization_closing_pressure_difference"] = int.from_bytes(datai_bytes[124:125], byteorder='big')
    settings["static_equilibrium_time"] = int.from_bytes(datai_bytes[125:126], byteorder='big')
    settings["battery_number_in_series"] = int.from_bytes(datai_bytes[126:127], byteorder='big')
    
    # Overcurrent delay settings
    settings["charge_overcurrent_delay"] = int.from_bytes(datai_bytes[127:128], byteorder='big')
    settings["discharge_overcurrent_delay"] = int.from_bytes(datai_bytes[128:129], byteorder='big')
    settings["transient_overcurrent_delay"] = int.from_bytes(datai_bytes[129:130], byteorder='big')
    settings["overcurrent_delay_recovery"] = int.from_bytes(datai_bytes[130:131], byteorder='big')
    settings["overcurrent_recovery_times"] = int.from_bytes(datai_bytes[131:132], byteorder='big')
    
    # Charge activation and timing settings
    settings["charge_current_limit_delay"] = int.from_bytes(datai_bytes[132:133], byteorder='big')
    settings["charge_activation_delay"] = int.from_bytes(datai_bytes[133:134], byteorder='big')
    settings["charging_activation_interval"] = int.from_bytes(datai_bytes[134:135], byteorder='big')
    settings["charge_activation_times"] = int.from_bytes(datai_bytes[135:136], byteorder='big')
    
    # Recording and standby settings
    settings["work_record_interval"] = int.from_bytes(datai_bytes[136:137], byteorder='big')
    settings["standby_recording_interval"] = int.from_bytes(datai_bytes[137:138], byteorder='big')
    settings["standby_shutdown_delay"] = int.from_bytes(datai_bytes[138:139], byteorder='big')
    
    # Capacity settings
    settings["remaining_capacity_alarm"] = int.from_bytes(datai_bytes[139:140], byteorder='big')
    settings["remaining_capacity_protection"] = int.from_bytes(datai_bytes[140:141], byteorder='big')
    settings["interval_charge_capacity"] = int.from_bytes(datai_bytes[141:142], byteorder='big')
    settings["cycle_cumulative_capacity"] = int.from_bytes(datai_bytes[142:143], byteorder='big')
    
    # Connection and compensation settings
    settings["connection_fault_impedance"] = int.from_bytes(datai_bytes[143:144], byteorder='big') / 10.0
    settings["compensation_point_1_position"] = int.from_bytes(datai_bytes[144:145], byteorder='big')
    settings["compensation_point_1_impedance"] = int.from_bytes(datai_bytes[145:146], byteorder='big') / 10.0
    settings["compensation_point_2_position"] = int.from_bytes(datai_bytes[146:147], byteorder='big')
    settings["compensation_point_2_impedance"] = int.from_bytes(datai_bytes[147:148], byteorder='big') / 10.0

    return settings

def _parse_51h_codes(info_str: str, name_prefix: str) -> Dict[str, Any]:
    """Parse 51H codes (device information)."""
    if info_str.startswith("~"):
        info_str = info_str[1:]

    msg_wo_chk_sum = info_str[:-4]
    hex_string = msg_wo_chk_sum[12:]
    cursor = 4

    hex_string = bytes.fromhex(hex_string)
    if len(hex_string) < 10:
        return {}

    device_name_bytes = hex_string[0:10]
    software_version_bytes = hex_string[10:12]
    manufacturer_name_bytes = hex_string[12:24]

    device_name = device_name_bytes.decode('ascii', errors='ignore').strip('\x00')
    software_version = software_version_bytes.decode('ascii', errors='ignore').strip('\x00')
    manufacturer_name = manufacturer_name_bytes.decode('ascii', errors='ignore').strip('\x00')

    software_version = int.from_bytes(software_version_bytes, byteorder='big') / 1000 * 4
    software_version = "{:.1f}".format(software_version)
    
    return {
        'device_name': device_name,
        'software_version': software_version,
        'manufacturer_name': manufacturer_name,
    }

def _interpret_alarm(event: str, value: int) -> str:
    """Interpret the alarm based on the event and value."""
    flags = ALARM_MAPPINGS.get(event, [])

    if not flags:
        return f"Unknown event: {event}"

    # Interpret the value as bit flags
    triggered_alarms = [flag for idx, flag in enumerate(flags) if value is not None and value & (1 << idx)]
    return ', '.join(str(alarm) for alarm in triggered_alarms) if triggered_alarms else "No Alarm"

def _create_cell_voltage_sensors(cellVoltage: List[int], name_prefix: str, highest_voltage_value: int, lowest_voltage_value: int, equilibrium_state0: int, equilibrium_state1: int) -> Dict[str, Any]:
    """Create individual cell voltage sensors with balancing attributes."""
    sensors = {}
    for i, voltage in enumerate(cellVoltage):
        cell_num = i + 1
        sensor_key = f"cell_{cell_num}_voltage"
        
        # Determine if this cell has the highest or lowest voltage
        cell_state_lowest = (voltage == lowest_voltage_value)
        cell_state_highest = (voltage == highest_voltage_value)
        
        # Determine if this cell is currently balancing
        if i < 8:
            # Check equilibriumState0 bits (cells 1-8)
            cell_state_balancing = bool(equilibrium_state0 & (1 << i))
        else:
            # Check equilibriumState1 bits (cells 9-16)
            cell_state_balancing = bool(equilibrium_state1 & (1 << (i - 8)))
        
        sensors[sensor_key] = {
            'state': voltage,
            'attributes': {
                'CELL_STATE_LOWEST': cell_state_lowest,
                'CELL_STATE_HIGHEST': cell_state_highest,
                'CELL_STATE_BALANCING': cell_state_balancing
            }
        }
    return sensors

def _create_temperature_sensors(temperatures: List[float], name_prefix: str) -> Dict[str, Any]:
    """Create temperature sensors."""
    sensors = {}
    tempCount = len(temperatures)
    
    for i, temp in enumerate(temperatures):
        if i < tempCount - 2:
            # For the first (tempCount - 2) temperatures, label them as Cell 1 Temp, Cell 2 Temp, etc.
            sensor_key = f"cell_temperature_{i+1}"
        elif i == tempCount - 2:
            # The second last temperature is Power Temp
            sensor_key = "power_temperature"
        else:
            # The last temperature is Environment Temp
            sensor_key = "environment_temperature"

        sensors[sensor_key] = temp
        
    return sensors