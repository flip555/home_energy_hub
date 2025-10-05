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

### Breaking Changes (v2.0.0+)
This major update includes significant architectural changes. If updating from a previous version:
- Remove existing Home Energy Hub integration entries from Home Assistant
- Re-add the integration with fresh configuration
- Reconfigure any automations or dashboards that use these entities

### Safety Disclaimer
**Use at Your Own Risk**: This integration is for informational and control purposes only. All electrical installations should be performed by a qualified electrician. Ensure all connected devices have proper safety settings configured.

## Quick Overview

### Key Features
- **Modular Architecture**: Easy to extend with new integrations
- **Multiple Connection Methods**: USB Serial, Telnet Serial, HTTP API
- **Comprehensive Monitoring**: 160+ sensors for detailed energy data
- **Clean Device Organization**: Separate devices for operational data and settings

### Supported Devices
- **Seplos V2 BMS**: Advanced battery management system monitoring
- **GEO IHD**: Energy monitoring via HTTP API

## Quick Start

1. **Install via HACS** (recommended) or manual installation
2. **Add integration** in Home Assistant Settings > Devices & Services
3. **Configure your devices** following the setup wizard
4. **Restart Home Assistant** to complete installation

For detailed instructions, see the [Installation Guide](https://github.com/flip555/home_energy_hub/wiki/Installation).

## Requirements

- Home Assistant 2023.12.0 or later
- Python 3.9 or later
- Required Python libraries (automatically installed): pyserial, aiohttp

## Getting Help

- **Wiki Documentation**: Comprehensive guides and troubleshooting
- **Discord Community**: [Join our Discord](https://discord.gg/4eQbPEETBR) for support
- **GitHub Issues**: Report bugs and request features

## Contributing

We welcome contributions! Please see our:
- [Contributing Guidelines](CONTRIBUTING.md)
- [Development Guide](https://github.com/flip555/home_energy_hub/wiki/Development)
- [Project Roadmap](TODO.md)

## License

GPL-3.0 License - see [LICENSE](LICENSE) file for details.
