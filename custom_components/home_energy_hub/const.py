# const.py
NAME = "Home Energy Hub"
DOMAIN = "home_energy_hub"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.1.1"
ATTRIBUTION = "Easily add Energy related things to HA without the hassle."

# Platforms
SENSOR = "sensor"
BINARY_SENSOR = "binary_sensor"
SELECT = "select"
NUMBER = "number"
PLATFORMS = [SENSOR, BINARY_SENSOR, SELECT, NUMBER]


HEH_REGISTER = {
    "00000": {
        "option_name": "Home Energy Hub Global Settings",
        "active": "1",
        "config_flow": "async_step_home_energy_hub_global_settings",
        "options_flow": "async_step_home_energy_hub_global_options",
        "init": "OctopusUKEnergyUKINIT"
    },
    "10000": {
        "option_name": "ESS Control",
        "active": "0",
        "submenu": {
            "10100": {
                "option_name": "ESS 1 Test",
                "active": "0",
                "config_flow": "async_step_ess_1_config",
                "options_flow": "async_step_ess_1_options",
                "init": "/config/custom_components/home_energy_hub/ess_1_test/init.py"
            }
        }
    },
    "20000": {
        "option_name": "Energy Tariffs",
        "active": "1",
        "submenu": {
            "20100": {
                "option_name": "Octopus Energy UK",
                "active": "1", 
                "submenu": {
                    "20101": {
                        "option_name": "Octopus Agile",
                        "active": "1",
                        "config_flow": "async_step_octopus_agile_tariffs",
                        "options_flow": "async_step_octopus_options_agile_tariffs",
                        "init": "OctopusEnergyUKAgile"
                    },
                    "20102": {
                        "option_name": "Octopus Flexible",
                        "active": "1",
                        "config_flow": "async_step_octopus_flexible_tariffs",
                        "options_flow": "async_step_octopus_options_flexible_tariffs",
                        "init": "/config/custom_components/home_energy_hub/octopus_flexible/init.py"
                    },
                    "20103": {
                        "option_name": "Octopus Tracker",
                        "active": "1",
                        "config_flow": "async_step_octopus_tracker_tariffs",
                        "options_flow": "async_step_octopus_options_tracker_tariffs",
                        "init": "/config/custom_components/home_energy_hub/octopus_tracker/init.py"
                    },
                    "20190": {
                        "option_name": "Octopus Account Data",
                        "active": "1",
                        "config_flow": "async_step_octopus_account_data",
                        "options_flow": "async_step_octopus_options_account_data",
                        "init": "/config/custom_components/home_energy_hub/octopus_tracker/init.py"
                    }
                }
            }
        }
    },
    "30000": {
        "option_name": "Battery Management Systems",
        "active": "1",
        "submenu": {
            "30100": {
                "option_name": "Seplos BMS",
                "active": "1",
                "submenu": {
                    "30101": {
                        "option_name": "Seplos BMS V2",
                        "active": "1",
                        "config_flow": "async_step_seplos_bms_v2",
                        "options_flow": "async_step_seplos_options_bms_v2",
                        "init": "/config/custom_components/home_energy_hub/seplos_bms_v2/init.py"
                    },
                    "30102": {
                        "option_name": "Seplos BMS V3",
                        "active": "0",
                        "config_flow": "/config/custom_components/home_energy_hub/config_flows/seplos_bms_v3.py",
                        "init": "/config/custom_components/home_energy_hub/seplos_bms_v3/init.py"
                    }
                }
            },
            "30200": {
                "option_name": "JK BMS",
                "active": "0",
                "submenu": {
                    "30201": {
                        "option_name": "JK BMS 1",
                        "active": "1",
                        "config_flow": "/config/custom_components/home_energy_hub/config_flows/jk_bms_1.py",
                        "init": "/config/custom_components/home_energy_hub/jk_bms_1/init.py"
                    }
                }
            }
        }
    },
    "40000": {
        "option_name": "Victron Devices",
        "active": "0",
        "submenu": {
            "40200": {
                "option_name": "Victron GX TCP Modbus",
                "active": "0",
                "config_flow": "/config/custom_components/home_energy_hub/config_flows/victron_gx_tcp_modbus.py",
                "init": "/config/custom_components/home_energy_hub/multiplus_ii/init.py"
            },
            "41001": {
                "option_name": "Multiplus II",
                "active": "0",
                "config_flow": "/config/custom_components/home_energy_hub/config_flows/multiplus_ii.py",
                "init": "/config/custom_components/home_energy_hub/multiplus_ii/init.py"
            },
            "41002": {
                "option_name": "Solar MPPT",
                "active": "0",
                "config_flow": "/config/custom_components/home_energy_hub/config_flows/solar_mppt.py",
                "init": "/config/custom_components/home_energy_hub/solar_mppt/init.py"
            }
        }
    },
    "50000": {
        "option_name": "Sunsynk Devices",
        "active": "0",
        "submenu": {
            "50200": {
                "option_name": "Sunsynk Test",
                "active": "0",
                "config_flow": "/config/custom_components/home_energy_hub/config_flows/sunsynk_test.py",
                "init": "/config/custom_components/home_energy_hub/multiplus_ii/init.py"
            }
        }
    },
    "60000": {
        "option_name": "Renogy Devices",
        "active": "0",
        "submenu": {
            "60200": {
                "option_name": "Renogy Test",
                "active": "0",
                "config_flow": "/config/custom_components/home_energy_hub/config_flows/renogy_test.py",
                "init": "/config/custom_components/home_energy_hub/multiplus_ii/init.py"
            }
        }
    },
}
