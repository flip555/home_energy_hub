"""Seplos V3 Modbus RTU data parser — ported from bms_connector.

Credits: Christian F5UII (@f5uii) for the Modbus RTU implementation.
"""

import struct
import logging

_LOGGER = logging.getLogger(__name__)


def modbus_crc(data: bytes) -> bytes:
    """Calculate the Modbus RTU CRC (little-endian, 2 bytes)."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack('<H', crc)


def verify_crc(frame_hex: str) -> bool:
    """Verify CRC of a received Modbus frame."""
    try:
        raw = bytes.fromhex(frame_hex)
        if len(raw) < 4:
            return False
        payload = raw[:-2]
        received_crc = raw[-2:]
        expected_crc = modbus_crc(payload)
        return received_crc == expected_crc
    except Exception:
        return False


def build_read_command(addr: int, register: int, count: int) -> str:
    """Build a Modbus RTU 0x04 (Read Input Registers) command as hex string."""
    payload = bytes([addr, 0x04]) + struct.pack('>HH', register, count)
    crc = modbus_crc(payload)
    return (payload + crc).hex()


def build_commands_for_address(battery_addr: int) -> list:
    """Return PIA + PIB commands for a given battery address.

    PIA: register 0x1000, 18 registers (0x12) — pack global data
    PIB: register 0x1100, 26 registers (0x1A) — cell voltages + temperatures
    """
    cmd_pia = build_read_command(battery_addr, 0x1000, 0x12)
    cmd_pib = build_read_command(battery_addr, 0x1100, 0x1A)
    return [cmd_pia, cmd_pib]


def convert_bytes_to_data(data_type: str, byte1: int, byte2: int):
    """Convert two bytes to typed value (UINT16 or INT16)."""
    if data_type == "UINT16":
        return (byte1 << 8) | byte2
    elif data_type == "INT16":
        value = (byte1 << 8) | byte2
        if value & 0x8000:
            value -= 0x10000
        return value
    return None


class V3PIA:
    """Pack Info A: pack-level battery data."""

    def __init__(self):
        self.pack_voltage = 0.0
        self.current = 0.0
        self.remaining_capacity = 0.0
        self.total_capacity = 0.0
        self.total_discharge_capacity = 0.0
        self.soc = 0.0
        self.soh = 0.0
        self.cycle = 0
        self.avg_cell_voltage = 0.0
        self.avg_cell_temperature = 0.0
        self.max_cell_voltage = 0.0
        self.min_cell_voltage = 0.0
        self.max_cell_temperature = 0.0
        self.min_cell_temperature = 0.0
        self.max_discharge_current = 0.0
        self.max_charge_current = 0.0


class V3PIB:
    """Pack Info B: cell voltages and temperatures."""

    def __init__(self):
        self.cell1_voltage = 0.0
        self.cell2_voltage = 0.0
        self.cell3_voltage = 0.0
        self.cell4_voltage = 0.0
        self.cell5_voltage = 0.0
        self.cell6_voltage = 0.0
        self.cell7_voltage = 0.0
        self.cell8_voltage = 0.0
        self.cell9_voltage = 0.0
        self.cell10_voltage = 0.0
        self.cell11_voltage = 0.0
        self.cell12_voltage = 0.0
        self.cell13_voltage = 0.0
        self.cell14_voltage = 0.0
        self.cell15_voltage = 0.0
        self.cell16_voltage = 0.0
        self.cell_temperature_1 = 0.0
        self.cell_temperature_2 = 0.0
        self.cell_temperature_3 = 0.0
        self.cell_temperature_4 = 0.0
        self.environment_temperature = 0.0
        self.power_temperature = 0.0


def decode_pia_response(response: str):
    """Decode a PIA Modbus response into a V3PIA object."""
    if not response:
        return None
    if response.startswith("~"):
        response = response[1:]

    if not verify_crc(response):
        _LOGGER.warning("PIA CRC invalid for %s", response)

    try:
        raw = bytes.fromhex(response)
    except ValueError:
        return None

    if len(raw) < 41:
        _LOGGER.warning("PIA frame too short (%d bytes)", len(raw))
        return None

    data = raw[3:-2]
    pia = V3PIA()

    try:
        pia.pack_voltage             = convert_bytes_to_data("UINT16", data[0],  data[1])  * 0.01
        pia.current                  = convert_bytes_to_data("INT16",  data[2],  data[3])  * 0.01
        pia.remaining_capacity       = convert_bytes_to_data("UINT16", data[4],  data[5])  * 0.01
        pia.total_capacity           = convert_bytes_to_data("UINT16", data[6],  data[7])  * 0.01
        pia.total_discharge_capacity = convert_bytes_to_data("UINT16", data[8],  data[9])  * 10
        pia.soc                      = convert_bytes_to_data("UINT16", data[10], data[11]) * 0.1
        pia.soh                      = convert_bytes_to_data("UINT16", data[12], data[13]) * 0.1
        pia.cycle                    = convert_bytes_to_data("UINT16", data[14], data[15])
        pia.avg_cell_voltage         = convert_bytes_to_data("UINT16", data[16], data[17]) * 0.001
        pia.avg_cell_temperature     = convert_bytes_to_data("UINT16", data[18], data[19]) * 0.1 - 273.15
        pia.max_cell_voltage         = convert_bytes_to_data("UINT16", data[20], data[21]) * 0.001
        pia.min_cell_voltage         = convert_bytes_to_data("UINT16", data[22], data[23]) * 0.001
        pia.max_cell_temperature     = convert_bytes_to_data("UINT16", data[24], data[25]) * 0.1 - 273.15
        pia.min_cell_temperature     = convert_bytes_to_data("UINT16", data[26], data[27]) * 0.1 - 273.15
        if len(data) >= 32:
            pia.max_discharge_current = convert_bytes_to_data("UINT16", data[30], data[31])
        if len(data) >= 34:
            pia.max_charge_current    = convert_bytes_to_data("UINT16", data[32], data[33])
    except IndexError:
        return None

    return pia


def decode_pib_response(response: str):
    """Decode a PIB Modbus response into a V3PIB object."""
    if not response:
        return None
    if response.startswith("~"):
        response = response[1:]

    if not verify_crc(response):
        _LOGGER.warning("PIB CRC invalid for %s", response)

    try:
        raw = bytes.fromhex(response)
    except ValueError:
        return None

    if len(raw) < 57:
        _LOGGER.warning("PIB frame too short (%d bytes)", len(raw))
        return None

    data = raw[3:-2]
    pib = V3PIB()

    try:
        pib.cell1_voltage  = convert_bytes_to_data("UINT16", data[0],  data[1])  * 0.001
        pib.cell2_voltage  = convert_bytes_to_data("UINT16", data[2],  data[3])  * 0.001
        pib.cell3_voltage  = convert_bytes_to_data("UINT16", data[4],  data[5])  * 0.001
        pib.cell4_voltage  = convert_bytes_to_data("UINT16", data[6],  data[7])  * 0.001
        pib.cell5_voltage  = convert_bytes_to_data("UINT16", data[8],  data[9])  * 0.001
        pib.cell6_voltage  = convert_bytes_to_data("UINT16", data[10], data[11]) * 0.001
        pib.cell7_voltage  = convert_bytes_to_data("UINT16", data[12], data[13]) * 0.001
        pib.cell8_voltage  = convert_bytes_to_data("UINT16", data[14], data[15]) * 0.001
        pib.cell9_voltage  = convert_bytes_to_data("UINT16", data[16], data[17]) * 0.001
        pib.cell10_voltage = convert_bytes_to_data("UINT16", data[18], data[19]) * 0.001
        pib.cell11_voltage = convert_bytes_to_data("UINT16", data[20], data[21]) * 0.001
        pib.cell12_voltage = convert_bytes_to_data("UINT16", data[22], data[23]) * 0.001
        pib.cell13_voltage = convert_bytes_to_data("UINT16", data[24], data[25]) * 0.001
        pib.cell14_voltage = convert_bytes_to_data("UINT16", data[26], data[27]) * 0.001
        pib.cell15_voltage = convert_bytes_to_data("UINT16", data[28], data[29]) * 0.001
        pib.cell16_voltage = convert_bytes_to_data("UINT16", data[30], data[31]) * 0.001
        pib.cell_temperature_1 = convert_bytes_to_data("UINT16", data[32], data[33]) * 0.1 - 273.15
        pib.cell_temperature_2 = convert_bytes_to_data("UINT16", data[34], data[35]) * 0.1 - 273.15
        pib.cell_temperature_3 = convert_bytes_to_data("UINT16", data[36], data[37]) * 0.1 - 273.15
        pib.cell_temperature_4 = convert_bytes_to_data("UINT16", data[38], data[39]) * 0.1 - 273.15
        if len(data) >= 50:
            pib.environment_temperature = convert_bytes_to_data("UINT16", data[48], data[49]) * 0.1 - 273.15
        if len(data) >= 52:
            pib.power_temperature = convert_bytes_to_data("UINT16", data[50], data[51]) * 0.1 - 273.15
    except IndexError:
        return None

    return pib


def extract_data_from_message(msg, config_battery_address=None):
    """Parse PIA and PIB responses into a flat dict for the coordinator.

    Returns a dict like:
    {
        "pack_voltage": 51.2,
        "current": -5.0,
        "cell1_voltage": 3.201,
        ...
    }
    """
    pia_data = None
    pib_data = None

    if not msg or len(msg) < 2:
        _LOGGER.error("Need at least 2 response frames (PIA + PIB)")
        return {}

    for idx, response in enumerate(msg):
        if isinstance(response, str) and response.startswith("~"):
            response = response[1:]

        if idx == 0:
            pia_data = decode_pia_response(response)
        elif idx == 1:
            pib_data = decode_pib_response(response)

    result = {}

    if pia_data:
        for attr in ["pack_voltage", "current", "remaining_capacity", "total_capacity",
                      "total_discharge_capacity", "soc", "soh", "cycle",
                      "avg_cell_voltage", "avg_cell_temperature",
                      "max_cell_voltage", "min_cell_voltage",
                      "max_cell_temperature", "min_cell_temperature",
                      "max_discharge_current", "max_charge_current"]:
            val = getattr(pia_data, attr, None)
            if val is not None:
                result[attr] = round(val, 3) if isinstance(val, float) else val

    if pib_data:
        for i in range(1, 17):
            val = getattr(pib_data, f"cell{i}_voltage", None)
            if val is not None:
                result[f"cell{i}_voltage"] = round(val, 3)

        for i in range(1, 5):
            val = getattr(pib_data, f"cell_temperature_{i}", None)
            if val is not None:
                result[f"cell_temperature_{i}"] = round(val, 1)

        if pib_data.environment_temperature:
            result["environment_temperature"] = round(pib_data.environment_temperature, 1)
        if pib_data.power_temperature:
            result["power_temperature"] = round(pib_data.power_temperature, 1)

    return result
