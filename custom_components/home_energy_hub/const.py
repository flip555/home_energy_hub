# const.py
NAME = "Home Energy Hub"
DOMAIN = "home_energy_hub"
VERSION = "0.0.1"
ATTRIBUTION = "Easily add Energy related things to HA without the hassle."

MAIN_MENU_OPTIONS = {
    "1000": {"option_name": "Battery Monitoring Systems"},
    "2000": {"option_name": "Energy Company Tariffs"},
    "3000": {"option_name": "In Home Displays"},
    "4000": {"option_name": "(Coming Soon) Victron Equipment"},
    "5000": {"option_name": "(Coming Soon) Sunsynk Equipment"},
    "6000": {"option_name": "(Coming Soon) Renogy Equipment"},
}

ENERGY_MENU_OPTIONS = {
    "2010": {"option_name": "Octopus Energy"},
}

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

BMS_MENU_OPTIONS = {
    "1010": {"option_name": "Seplos BMS"},
    "1020": {"option_name": "JKBMS"},
}

SEPLOS_BMS_TYPE_DEFAULTS = {
    "SEPLV2": {"bms_name": "SEP BMS V2 (SEPLV2)", "default_prefix": "Seplos BMS HA", "default_address": "0x00"},
    "SEPLV3": {"bms_name": "SEP BMS V3 (SEPLV3)", "default_prefix": "Seplos BMS V3", "default_address": "0x01"},
}

