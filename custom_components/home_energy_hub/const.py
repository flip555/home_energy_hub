"""Shared constants for Home Energy Hub."""

DOMAIN = "home_energy_hub"

# Config keys
CONF_INTEGRATION_TYPE = "integration_type"
CONF_CONNECTOR_TYPE = "connector_type"

# Integration categories for organized UI
INTEGRATION_CATEGORIES = {
    "energy_monitors": "Energy Monitors",
    "battery_systems": "Battery Systems",
}

# Integration details with category, human-readable name, and description
INTEGRATION_TYPES = {
    "geo_ihd": {
        "name": "Geo Home IHD",
        "category": "energy_monitors",
        "description": "Geo Home In-Home Display for electricity and gas monitoring"
    },
    "seplos_v2": {
        "name": "Seplos BMS V2",
        "category": "battery_systems",
        "description": "Seplos Battery Management System Version 2"
    },
    "iog_slots": {
        "name": "IOG-Ohme Slots",
        "category": "energy_monitors",
        "description": "IOG-Ohme charging slot duration tracking"
    }
}

CONNECTOR_TYPES = {
    "usb_serial": "USB-RS485 Serial",
    "telnet_serial": "Telnet Serial",
}

# Seplos-specific configuration
CONF_SERIAL_PORT = "serial_port"
CONF_BAUD_RATE = "baud_rate"
DEFAULT_BAUD_RATE = 19200  # Seplos V2 uses 19200 baud
CONF_HOST = "host"  # For TCP
CONF_PORT = "port"  # For TCP/ESPHome
CONF_ESP_HOME_DEVICE_ID = "esphome_device_id"  # For ESPHome

# Seplos V2 specific configuration
CONF_BATTERY_ADDRESS = "battery_address"
CONF_PACK_MODE = "pack_mode"
CONF_NAME_PREFIX = "name_prefix"
CONF_POLL_INTERVAL = "poll_interval"

# Battery addresses for Seplos V2
BATTERY_ADDRESSES = {
    "0x00": "Pack 0x00 (Single/Master)",
    "0x01": "Pack 0x01",
    "0x02": "Pack 0x02",
    "0x03": "Pack 0x03"
}

# Pack modes
PACK_MODES = {
    "single": "Single Pack",
    "parallel": "Parallel Packs"
}

# Seplos V2 sensor definitions
SENSOR_UNITS = {
    "cellsCount": None,
    "resCap": "Ah",
    "capacity": "Ah",
    "soc": "%",
    "ratedCapacity": "Ah",
    "cycles": None,
    "soh": "%",
    "portVoltage": "V",
    "current": "A",
    "voltage": "V",
    "battery_watts": "W",
    "full_charge_watts": "W",
    "full_charge_amps": "Ah",
    "remaining_watts": "W",
    "capacity_watts": "W",
    "highest_cell_voltage": "mV",
    "highest_cell_number": None,
    "lowest_cell_voltage": "mV",
    "lowest_cell_number": None,
    "cell_difference": "mV",
    "customNumber": None,
    "power_temperature": "°C",
    "environment_temperature": "°C",
    "device_name": None,
    "software_version": None,
    "manufacturer_name": None,
    # Cell voltage sensors
    "cell_1_voltage": "mV",
    "cell_2_voltage": "mV",
    "cell_3_voltage": "mV",
    "cell_4_voltage": "mV",
    "cell_5_voltage": "mV",
    "cell_6_voltage": "mV",
    "cell_7_voltage": "mV",
    "cell_8_voltage": "mV",
    "cell_9_voltage": "mV",
    "cell_10_voltage": "mV",
    "cell_11_voltage": "mV",
    "cell_12_voltage": "mV",
    "cell_13_voltage": "mV",
    "cell_14_voltage": "mV",
    "cell_15_voltage": "mV",
    "cell_16_voltage": "mV",
    # Cell temperature sensors
    "cell_temperature_1": "°C",
    "cell_temperature_2": "°C",
    "cell_temperature_3": "°C",
    "cell_temperature_4": "°C",
    "cell_temperature_5": "°C",
    "cell_temperature_6": "°C",
    "cell_temperature_7": "°C",
    "cell_temperature_8": "°C",
    # Alarm sensors (no units - they return strings)
    "currentAlarm": None,
    "voltageAlarm": None,
    "alarmEvent0": None,
    "alarmEvent1": None,
    "alarmEvent2": None,
    "alarmEvent3": None,
    "alarmEvent4": None,
    "alarmEvent5": None,
    "alarmEvent6": None,
    "alarmEvent7": None,
    "onOffState": None,
    "equilibriumState0": None,
    "equilibriumState1": None,
    "systemState": None,
    "disconnectionState0": None,
    "disconnectionState1": None,
    # Temperature protection sensors (these are settings, not measurements)
    "charging_high_temperature_protection": "°C",
    "charging_high_temperature_recovery": "°C",
    "charging_low_temperature_protection": "°C",
    "charging_low_temperature_recovery": "°C",
    "discharge_high_temperature_protection": "°C",
    "discharge_high_temperature_recovery": "°C",
    "discharge_low_temperature_protection": "°C",
    "discharge_low_temperature_recovery": "°C",
    "charging_under_temperature_protection": "°C",
    "charging_under_temperature_recovery": "°C",
    "discharge_high_temperature_warning": "°C",
    "power_high_temperature_alarm": "°C",
    "power_high_temperature_recovery": "°C",
    "power_over_temperature_protection": "°C",
    "power_over_temperature_recovery": "°C",
    # Current protection sensors
    "charging_overcurrent_warning": "A",
    "charging_overcurrent_recovery": "A",
    "discharge_overcurrent_warning": "A",
    "discharge_overcurrent_recovery": "A",
    "charge_overcurrent_protection": "A",
    "discharge_overcurrent_protection": "A",
    "transient_overcurrent_protection": "A",
    "charge_overcurrent_delay": "A",
    "discharge_overcurrent_delay": "A",
    "transient_overcurrent_delay": "A",
    "overcurrent_delay_recovery": "A",
    "overcurrent_recovery_times": "A",
    "charge_current_limit_delay": "A",
    # Voltage protection sensors
    "monomer_high_voltage_alarm": "mV",
    "monomer_overvoltage_protection": "mV",
    "monomer_overvoltage_recovery": "mV",
    "monomer_undervoltage_protection": "mV",
    "monomer_undervoltage_recovery": "mV",
    "equalization_opening_voltage": "mV",
    "battery_low_voltage_forbidden_charging": "mV",
    "total_voltage_overvoltage_protection": "V",
    "total_voltage_undervoltage_protection": "V",
    "total_pressure_undervoltage_recovery": "V",
    "charging_overvoltage_protection": "V",
    "charging_overvoltage_recovery": "V",
    # Additional temperature protection sensors
    "charging_high_temperature_warning": "°C",
    "charging_high_temperature_recovery": "°C",
    "charging_low_temperature_warning": "°C",
    "charging_low_temperature_recovery": "°C",
    "charging_over_temperature_protection": "°C",
    "charging_over_temperature_recovery": "°C",
    "charging_under_temperature_protection": "°C",
    "charging_under_temperature_recovery": "°C",
    "discharge_high_temperature_warning": "°C",
    "discharge_high_temperature_recovery": "°C",
    "discharge_low_temperature_warning": "°C",
    "discharge_low_temperature_recovery": "°C",
    "discharge_over_temperature_protection": "°C",
    "discharge_over_temperature_recovery": "°C",
    "discharge_under_temperature_protection": "°C",
    "discharge_under_temperature_recovery": "°C",
    "cell_low_temperature_heating": "°C",
    "ambient_high_temperature_alarm": "°C",
    "ambient_high_temperature_recovery": "°C",
    "ambient_low_temperature_alarm": "°C",
    "ambient_low_temperature_recovery": "°C",
    "environment_over_temperature_protection": "°C",
    "environment_over_temperature_recovery": "°C",
    "environment_under_temperature_protection": "°C",
    "environment_under_temperature_recovery": "°C",
    "power_high_temperature_alarm": "°C",
    "power_high_temperature_recovery": "°C",
    "power_over_temperature_protection": "°C",
    "power_over_temperature_recovery": "°C",
    # SOC sensor
    "soc_ah": "Ah",
    # Settings sensors with _settings suffix (from 47H codes)
    "monomer_high_voltage_alarm_settings": "mV",
    "monomer_overvoltage_protection_settings": "mV",
    "monomer_overvoltage_recovery_settings": "mV",
    "monomer_undervoltage_protection_settings": "mV",
    "monomer_undervoltage_recovery_settings": "mV",
    "equalization_opening_voltage_settings": "mV",
    "battery_low_voltage_forbidden_charging_settings": "mV",
    "total_voltage_overvoltage_protection_settings": "V",
    "total_voltage_undervoltage_protection_settings": "V",
    "total_pressure_undervoltage_recovery_settings": "V",
    "charging_overvoltage_protection_settings": "V",
    "charging_overvoltage_recovery_settings": "V",
    "charging_high_temperature_warning_settings": "°C",
    "charging_high_temperature_recovery_settings": "°C",
    "charging_low_temperature_warning_settings": "°C",
    "charging_low_temperature_recovery_settings": "°C",
    "charging_over_temperature_protection_settings": "°C",
    "charging_over_temperature_recovery_settings": "°C",
    "charging_under_temperature_protection_settings": "°C",
    "charging_under_temperature_recovery_settings": "°C",
    "discharge_high_temperature_warning_settings": "°C",
    "discharge_high_temperature_recovery_settings": "°C",
    "discharge_low_temperature_warning_settings": "°C",
    "discharge_low_temperature_recovery_settings": "°C",
    "discharge_over_temperature_protection_settings": "°C",
    "discharge_over_temperature_recovery_settings": "°C",
    "discharge_under_temperature_protection_settings": "°C",
    "discharge_under_temperature_recovery_settings": "°C",
    "cell_low_temperature_heating_settings": "°C",
    "ambient_high_temperature_alarm_settings": "°C",
    "ambient_high_temperature_recovery_settings": "°C",
    "ambient_low_temperature_alarm_settings": "°C",
    "ambient_low_temperature_recovery_settings": "°C",
    "environment_over_temperature_protection_settings": "°C",
    "environment_over_temperature_recovery_settings": "°C",
    "environment_under_temperature_protection_settings": "°C",
    "environment_under_temperature_recovery_settings": "°C",
    "power_high_temperature_alarm_settings": "°C",
    "power_high_temperature_recovery_settings": "°C",
    "power_over_temperature_protection_settings": "°C",
    "power_over_temperature_recovery_settings": "°C",
    "charging_overcurrent_warning_settings": "A",
    "charging_overcurrent_recovery_settings": "A",
    "discharge_overcurrent_warning_settings": "A",
    "discharge_overcurrent_recovery_settings": "A",
    "charge_overcurrent_protection_settings": "A",
    "discharge_overcurrent_protection_settings": "A",
    "transient_overcurrent_protection_settings": "A",
    "charge_overcurrent_delay_settings": "A",
    "discharge_overcurrent_delay_settings": "A",
    "transient_overcurrent_delay_settings": "A",
    "overcurrent_delay_recovery_settings": "A",
    "overcurrent_recovery_times_settings": "A",
    "charge_current_limit_delay_settings": "A",
    "soc_ah_settings": "Ah",
}

# Seplos V2 alarm mappings (from reference file)
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