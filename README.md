# Home Energy Hub

A Home Assistant custom component for integrating energy management devices, featuring a modular architecture with support for multiple device types and connection methods.

[![Discord](https://img.shields.io/discord/1161651448011034734?style=for-the-badge&logo=discord)](https://discord.gg/4eQbPEETBR)

## Documentation

**Comprehensive documentation is in the [GitHub Wiki](https://github.com/flip555/home_energy_hub/wiki).**

- [Installation](https://github.com/flip555/home_energy_hub/wiki/Installation)
- [Configuration](https://github.com/flip555/home_energy_hub/wiki/Configuration)
- [Supported Integrations](https://github.com/flip555/home_energy_hub/wiki/Supported-Integrations)
- [Upgrade Notes](https://github.com/flip555/home_energy_hub/wiki/Upgrade-Notes)
- [Troubleshooting](https://github.com/flip555/home_energy_hub/wiki/Troubleshooting)
- [Development](https://github.com/flip555/home_energy_hub/wiki/Development)

## Upgrading?

- **v2.1+** removed IOG-Ohme Slots and Parallel Seplos V2 packs; single-pack only.
- **v2.2+** adds Seplos V3 support (USB-RS485 or Telnet).
- **Before upgrading from v2.0.0-alpha**, delete the old Seplos V2 entries, restart, then re-add — entity unique IDs changed.

Read the full [Upgrade Notes](https://github.com/flip555/home_energy_hub/wiki/Upgrade-Notes) before upgrading.

## Safety

**Use at your own risk.** This integration is for informational and control purposes only. Electrical installations must be performed by a qualified electrician, and every connected device should have its own safety settings configured.

## Overview

| Device | Connection | Sensors | Status |
|---|---|---:|---|
| Seplos V2 BMS | USB-RS485 / Telnet | 167 | ✅ tested |
| Seplos V3 BMS | USB-RS485 / Telnet | 22 | 🧪 experimental |
| GEO IHD | HTTP API | 18 | ✅ tested |

Separate devices are created for operational data and settings. See [Supported Integrations](https://github.com/flip555/home_energy_hub/wiki/Supported-Integrations) for details.

## Quick Start

1. Install via HACS (recommended) or manually
2. Add the integration in **Settings → Devices & Services**
3. Configure your device with the setup wizard
4. Restart Home Assistant

See the [Installation Guide](https://github.com/flip555/home_energy_hub/wiki/Installation) for step-by-step instructions.

## Requirements

- Home Assistant 2023.12.0 or later
- Python 3.9 or later
- `pymodbus` and `aiohttp` (installed automatically)

## Getting Help

- [Wiki](https://github.com/flip555/home_energy_hub/wiki)
- [Discord](https://discord.gg/4eQbPEETBR)
- [GitHub Issues](https://github.com/flip555/home_energy_hub/issues)
- [Related Projects](https://github.com/flip555/home_energy_hub/wiki/Related-Projects)

## Contributing & Support

- [Contributing Guidelines](CONTRIBUTING.md)
- [Development Guide](https://github.com/flip555/home_energy_hub/wiki/Development)
- [Project Roadmap](https://github.com/flip555/home_energy_hub/wiki/Development-Roadmap)
- [GitHub Sponsors](https://github.com/sponsors/flip555)

## License

GPL-3.0 License — see [LICENSE](LICENSE).
