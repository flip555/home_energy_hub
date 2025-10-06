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

### v2.0.0+ Architecture
This major update introduced a modular architecture with clear separation between connectors, integrations, and core components. The platform now supports easy extension with new device integrations.

### Safety Disclaimer
**Use at Your Own Risk**: This integration is for informational and control purposes only. All electrical installations should be performed by a qualified electrician. Ensure all connected devices have proper safety settings configured.

## Quick Overview

### Key Features
- **Modular Architecture**: Easy to extend with new integrations
- **Multiple Connection Methods**: USB-RS485 Serial (✅ tested), Telnet Serial (🧪 untested), HTTP API (✅ tested)
- **Comprehensive Monitoring**: 167 sensors for Seplos V2 BMS, 18 sensors for GEO IHD
- **Clean Device Organization**: Separate devices for operational data and settings

### Supported Devices

#### ✅ Tested & Verified
- **Seplos V2 BMS** (Single pack via USB-RS485): Advanced battery management with 167 sensors (80 BMS + 87 Settings)
- **GEO IHD**: Energy monitoring via HTTP API with 18 sensors (9 Electricity + 9 Gas)

#### 🧪 Experimental/Untested
- **Seplos V2 via Telnet Serial**: Network-based serial connection (untested)
- **Multiple Seplos battery packs**: Parallel battery configurations (untested)
- **Other connection methods**: Additional protocols and devices (see roadmap)

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
