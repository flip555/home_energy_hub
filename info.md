# Home Energy Hub

A comprehensive Home Assistant integration for managing and monitoring various energy management systems with a modular architecture.

## Supported Integrations

### Battery Systems
- **Seplos V2 BMS**: Advanced battery management system with comprehensive monitoring
  - Dual device support (BMS operational data and Settings configuration)
  - Multiple connection methods (USB-RS485 Serial, Telnet Serial)
  - 160+ sensors covering all operational parameters

### Energy Monitors  
- **GEO IHD**: In-home display for electricity and gas monitoring via HTTP API
  - Real-time consumption tracking
  - Electricity and gas usage monitoring

## Features

- **Modular Design**: Easy to extend with new integrations and connectors
- **Unified Configuration**: Single domain with category-based organization  
- **Factory Pattern**: Dynamic connector selection at setup time
- **Clean Entity Names**: Human-readable names without technical suffixes
- **Proper Device Info**: Manufacturer, model, and software version details

## Requirements

- Home Assistant 2023.12.0 or later
- Python 3.9 or later
- pymodbus, aiohttp, and pyserial libraries

## Installation

Available via HACS (recommended) or manual installation. See the main [README.md](README.md) for detailed installation instructions.

## Support

- [GitHub Issues](https://github.com/flip555/home_energy_hub/issues)
- [Discord Community](https://discord.gg/4eQbPEETBR)