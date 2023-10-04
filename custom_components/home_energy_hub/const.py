# const.py
NAME = "Home Energy Hub"
DOMAIN = "home_energy_hub"
VERSION = "0.0.1"
ATTRIBUTION = "Easily add Energy related things to HA without the hassle."

BMS_TYPE_DEFAULTS = {
    "SEPLV2": {"bms_name": "SEP BMS V2 (SEPLV2)", "default_prefix": "Seplos BMS HA", "default_address": "0x00"},
    "SEPLV3": {"bms_name": "SEP BMS V3 (SEPLV3)", "default_prefix": "Seplos BMS V3", "default_address": "0x01"},
}

