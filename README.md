# Home Energy Hub

A Home Assistant custom component for integrating energy management devices, featuring a modular architecture with support for multiple device types and connection methods.

[![Discord](https://img.shields.io/discord/1161651448011034734?style=for-the-badge&logo=discord)](https://discord.gg/4eQbPEETBR)

## 📚 Documentation

**Comprehensive documentation is available in our [GitHub Wiki](https://github.com/flip555/home_energy_hub/wiki)**

The wiki contains detailed guides for:
- [Installation](https://github.com/flip555/home_energy_hub/wiki/Installation) - Step-by-step setup instructions
- [Configuration](https://github.com/flip555/home_energy_hub/wiki/Configuration) - Device setup and configuration
- [Supported Integrations](https://github.com/flip555/home_energy_hub/wiki/Supported-Integrations) - Available devices and features
- [Troubleshooting](https://github.com/flip555/home_energy_hub/wiki/Troubleshooting) - Common issues and solutions
- [Development](https://github.com/flip555/home_energy_hub/wiki/Development) - Contributing and extending the platform

## ⚠️ Important Notices

### Breaking Changes in v2.1+
- **IOG-Ohme Slots Removed**: The IOG-Ohme Slots integration has been removed.
- **Parallel Packs Removed**: Parallel Seplos V2 BMS support has been removed as it was never functional. Single-pack operation only.
- **Architecture Cleanup**: Configuration options simplified, dead code removed.
- **🔴 Required: Delete existing Seplos V2 entries before upgrading.** Entity unique IDs changed. Delete old entries, restart HA, then re-add.

### What's New in v2.2
- **Seplos BMS V3 support** (🧪 experimental) — Modbus RTU protocol via USB-RS485 or Telnet
  - Pack Info A: voltage, current, capacity, SOC, SOH, cycle count, temperatures
  - Pack Info B: 16 cell voltages, 4 cell temperatures, environment & power temps
  - 22 sensors per entry
- **Telnet Serial** now available for both V2 and V3 (✅ tested on V2, 🧪 untested on V3)

### v2.0.0+ Architecture
This major update introduced a modular architecture with clear separation between connectors, integrations, and core components. The platform supports easy extension with new device integrations.

### Safety Disclaimer
**Use at Your Own Risk**: This integration is for informational and control purposes only. All electrical installations should be performed by a qualified electrician. Ensure all connected devices have proper safety settings configured.

## Quick Overview

### Key Features
- **Modular Architecture**: Easy to extend with new integrations
- **Multiple Connection Methods**: USB-RS485 Serial (✅ tested), Telnet Serial (✅ tested V2, 🧪 untested V3), HTTP API (✅ tested)
- **Comprehensive Monitoring**: 167 sensors for Seplos V2 BMS, 22 sensors for Seplos V3 BMS, 18 sensors for GEO IHD
- **Clean Device Organization**: Separate devices for operational data and settings

### Supported Devices

#### ✅ Tested & Verified
- **Seplos V2 BMS** (USB-RS485 or Telnet Serial): 167 sensors (80 BMS + 87 Settings)
- **GEO IHD** (HTTP API): 18 sensors (9 Electricity + 9 Gas)

#### 🧪 Experimental
- **Seplos V3 BMS** (USB-RS485 or Telnet): Modbus RTU protocol, 22 sensors (pack and cell data)

## Quick Start

1. **Install via HACS** (recommended) or manual installation
2. **Add integration** in Home Assistant Settings > Devices & Services
3. **Configure your devices** following the setup wizard
4. **Restart Home Assistant** to complete installation

For detailed instructions, see the [Installation Guide](https://github.com/flip555/home_energy_hub/wiki/Installation).

## Requirements

- Home Assistant 2023.12.0 or later
- Python 3.9 or later
- Required Python libraries (automatically installed): pymodbus, aiohttp

## Getting Help

- **Wiki Documentation**: Comprehensive guides and troubleshooting
- **Discord Community**: [Join our Discord](https://discord.gg/4eQbPEETBR) for support
- **GitHub Issues**: Report bugs and request features
- **Related Projects**: [Complementary integrations](https://github.com/flip555/home_energy_hub/wiki/Related-Projects) that work well with Home Energy Hub

## Contributing & Support

We welcome contributions! Please see our:
- [Contributing Guidelines](CONTRIBUTING.md)
- [Development Guide](https://github.com/flip555/home_energy_hub/wiki/Development)
- [Project Roadmap](https://github.com/flip555/home_energy_hub/wiki/Development-Roadmap)

### Support the Project
- [GitHub Sponsors](https://github.com/sponsors/flip555) - Support ongoing development
- [Discord Community](https://discord.gg/4eQbPEETBR) - Get help and discuss features

## License

GPL-3.0 License - see [LICENSE](LICENSE) file for details.
