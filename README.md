# Home Energy Hub

A Home Assistant custom component for integrating energy management devices, featuring a modular architecture with support for multiple device types and connection methods.

[![Discord](https://img.shields.io/discord/1161651448011034734?style=for-the-badge&logo=discord)](https://discord.gg/4eQbPEETBR)

## ⚠️ Important Update Notice

**Breaking Change**: This major update (v2.0.0) includes significant architectural changes. If you are updating from a previous version, you will likely need to:
- Remove existing Home Energy Hub integration entries from Home Assistant
- Re-add the integration with fresh configuration
- Reconfigure any automations or dashboards that use these entities

**Note**: Some features from previous versions have been temporarily removed as part of this architectural overhaul. These features will be re-added in future updates as we rebuild them on the new modular platform.

## ⚠️ Disclaimer

**Use at Your Own Risk**: This integration is intended for informational and control purposes only. All electrical installations should be performed by a qualified electrician. Ensure that all individual devices connected to this integration have their safety settings correctly configured. The developers are not responsible for any damage or issues that may arise from using this integration.

## Features

### Seplos V2 BMS Integration
- **Dual Device Support**: Automatically creates separate BMS and Settings devices in Home Assistant
- **Multiple Connection Methods**:
  - USB-RS485 Serial (direct connection)
  - Telnet Serial (for serial-to-telnet bridges like ser2net, ESP8266/ESP32)
- **Comprehensive Sensor Coverage**: 160+ sensors including:
  - Cell voltages and temperatures
  - Battery capacity and state of charge
  - Current, voltage, and power measurements
  - System alarms and status indicators
  - Configuration settings and limits

### GEO IHD Integration
- HTTP API-based energy monitoring
- Electricity and gas consumption tracking
- Real-time power usage data

### Architecture
- **Modular Design**: Easy to extend with new integrations and connectors
- **Unified Configuration**: Single domain with category-based organization
- **Factory Pattern**: Dynamic connector selection at setup time

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to Integrations
3. Click the three dots in the top right
4. Select "Custom repositories"
5. Add `https://github.com/flip555/home_energy_hub` as a repository URL
6. Select "Integration" as category
7. Click "Add"
8. Find "Home Energy Hub" in the list and install
9. Restart Home Assistant

### Manual Installation

1. Download this repository
2. Copy the `home_energy_hub` folder to your `config/custom_components/` directory
3. Restart Home Assistant

## Configuration

### Seplos V2 BMS Setup

1. Go to Settings > Devices & Services > Add Integration
2. Search for "Home Energy Hub"
3. Select "Battery Systems" category
4. Choose "Seplos BMS V2"
5. Select connection method:
   - **USB-RS485 Serial**: For direct USB-to-RS485 adapters
     - Serial port (e.g., `/dev/ttyUSB0`)
     - Baud rate (default: 19200)
   - **Telnet Serial**: For serial-to-telnet bridges
     - Host (IP address or hostname)
     - Port (default: 23)
6. Configure Seplos-specific settings:
   - Battery address (0x00-0x03)
   - Pack mode (single or parallel)
   - Name prefix for entities
   - Poll interval (seconds)
7. Complete the setup

### GEO IHD Setup

1. Go to Settings > Devices & Services > Add Integration
2. Search for "Home Energy Hub"
3. Select "Energy Monitors" category
4. Choose "Geo Home IHD"
5. Enter API credentials and endpoint details
6. Complete the setup

## Supported Integrations

### Battery Systems
- **Seplos V2 BMS**: Advanced battery management system with comprehensive monitoring
  - Two separate devices: BMS (operational data) and Settings (configuration)
  - Clean entity names without technical suffixes
  - Full manufacturer and model information

### Energy Monitors
- **GEO IHD**: In-home display for electricity and gas monitoring via HTTP API

## Connector Types

### USB-RS485 Serial
- Direct connection to Seplos V2 BMS via USB-to-RS485 adapter
- Requires physical serial port access
- Baud rate: 19200 (Seplos V2 standard)

### Telnet Serial
- Network-based serial connection via telnet
- Compatible with ser2net, ESP8266/ESP32 serial servers
- Ideal for remote or network-connected setups
- Same protocol as USB serial, different transport

## Device Structure

### Seplos V2 Device Organization
- **BMS Device**: Contains operational data (voltages, currents, temperatures, alarms)
- **Settings Device**: Contains configuration parameters (limits, thresholds, system settings)
- **Clean Entity Names**: Human-readable names without technical suffixes
- **Proper Device Info**: Manufacturer, model, and software version details

## Requirements

- Home Assistant 2023.12.0 or later
- Python 3.9 or later
- For Seplos V2 USB Serial: pyserial library
- For Seplos V2 Telnet: telnetlib (included in Python standard library)
- For GEO IHD: aiohttp library

## Repository Structure

```
home_energy_hub/
├── .github/                    # GitHub workflows and templates
├── assets/                     # Logo and branding assets
├── config/                     # Example configuration files
├── custom_components/          # Home Assistant custom component
│   └── home_energy_hub/        # Main integration code
│       ├── connectors/         # Connection abstraction layer
│       ├── integrations/       # Device-specific implementations
│       └── translations/       # Internationalization files
├── scripts/                    # Development and build scripts
├── CONTRIBUTING.md             # Contribution guidelines
├── hacs.json                   # HACS integration metadata
├── LICENSE                     # MIT License
├── README.md                   # This file
├── requirements.txt            # Python dependencies
└── TODO.md                     # Development roadmap
```

## Troubleshooting

### Seplos V2 Connection Issues
- **USB Serial**: Verify serial port permissions and device presence
- **Telnet Serial**: Check network connectivity and telnet server configuration
- **No Data**: Ensure correct battery address and Seplos V2 protocol compatibility

### Device Not Appearing
- Restart Home Assistant after installation
- Check integration logs for connection errors
- Verify all required configuration parameters

## Development

This project uses:
- **Ruff** for linting and formatting
- **HACS** for Home Assistant integration distribution
- **GitHub Actions** for CI/CD

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development guidelines and [`TODO.md`](TODO.md) for the development roadmap.

## Contributing

Contributions are welcome! Please open issues or pull requests on GitHub.

See our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## License

GPL-3.0 License - see [LICENSE](LICENSE) file for details.
