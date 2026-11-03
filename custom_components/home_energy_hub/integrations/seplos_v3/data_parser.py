"""Seplos V3 Modbus RTU data parser — ported from bms_connector.

Credits: Christian F5UII (@f5uii) for the Modbus RTU implementation.
"""

import struct

try:
    from .vendor_spec import PIC_BITS, SFA_BITS, SPA_FIELDS
except ImportError:  # standalone tests
    from vendor_spec import PIC_BITS, SFA_BITS, SPA_FIELDS
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


def build_read_command(addr: int, register: int, count: int, function: int = 0x04) -> str:
    """Build a Modbus RTU 0x04 (Read Input Registers) command as hex string."""
    payload = bytes([addr, function]) + struct.pack('>HH', register, count)
    crc = modbus_crc(payload)
    return (payload + crc).hex()


def build_commands_for_address(battery_addr: int) -> list:
    """Build the V3 read commands: PIA, PIB, VIA, model, PIC, SFA, SPA."""
    return [
        build_read_command(battery_addr, 0x1000, 0x12),
        build_read_command(battery_addr, 0x1100, 0x1A),
        build_read_command(battery_addr, 0x1700, 0x33),
        build_read_command(battery_addr, 0x170A, 0x0A),
        build_read_command(battery_addr, 0x1200, 0x90, 0x01),
        build_read_command(battery_addr, 0x1400, 0x50, 0x01),
        build_read_command(battery_addr, 0x1300, 0x6A),
    ]


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
        self.system_events = 0
        self.avg_cell_voltage = 0.0
        self.avg_cell_temperature = 0.0
        self.max_cell_voltage = 0.0
        self.min_cell_voltage = 0.0
        self.max_cell_temperature = 0.0
        self.min_cell_temperature = 0.0
        self.max_discharge_current = 0.0
        self.max_charge_current = 0.0
        self.extern_voltage = 0.0


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
        self.cell_temperature_5 = 0.0
        self.cell_temperature_6 = 0.0
        self.cell_temperature_7 = 0.0
        self.cell_temperature_8 = 0.0
        self.environment_temperature = 0.0
        self.power_temperature = 0.0


class V3VIA:
    def __init__(self):
        self.manufacturer = ""
        self.model = ""
        self.serial = ""


class V3PIC:
    def __init__(self):
        self.bits = []
        self.raw = b""


class V3SFA:
    def __init__(self):
        self.bits = []
        self.raw = b""


class V3SPA:
    def __init__(self):
        self.values = {}
        self.raw = b""


def _frame_data(response, expected_data_len):
    if not response:
        return None
    if response.startswith("~"):
        response = response[1:]
    if not verify_crc(response):
        _LOGGER.warning("CRC invalid for frame %s", response)
        return None
    try:
        raw = bytes.fromhex(response)
    except ValueError:
        return None
    if len(raw) < 3 + expected_data_len + 2:
        return None
    return raw[3:-2]


def decode_model_response(response):
    data = _frame_data(response, 0x14)
    if data is None:
        return ""
    return data[:20].split(b"\0")[0].decode("ascii", errors="replace").strip()


def decode_via_response(response, model_response=None):
    data = _frame_data(response, 0x66)
    if data is None:
        return None
    model = decode_model_response(model_response) if model_response else ""
    combined = data[:40].split(b"\0")[0].decode("ascii", errors="replace").strip()
    serial = data[40:].split(b"\0")[0].decode("ascii", errors="replace").strip()
    via = V3VIA()
    via.serial = serial
    via.model = model
    via.manufacturer = combined[: -len(model)].strip() if model and combined.endswith(model) else combined
    return via


def _decode_bits(response, expected_data_len, spec):
    data = _frame_data(response, expected_data_len)
    if data is None:
        return None
    bits = []
    for item in spec:
        try:
            bits.append((data[item["byte"]] >> item["bit"]) & 1)
        except IndexError:
            bits.append(0)
    return bits, data


def decode_pic_response_modbus(response):
    result = _decode_bits(response, 0x12, PIC_BITS)
    if result is None:
        return None
    bits, data = result
    pic = V3PIC()
    pic.bits = bits
    pic.raw = data
    return pic


def decode_sfa_response(response):
    result = _decode_bits(response, 0x0A, SFA_BITS)
    if result is None:
        return None
    bits, data = result
    sfa = V3SFA()
    sfa.bits = bits
    sfa.raw = data
    return sfa


def decode_spa_response(response):
    data = _frame_data(response, 0xD4)
    if data is None:
        return None
    spa = V3SPA()
    spa.raw = data
    for field in SPA_FIELDS:
        off = field["index"]
        raw = int.from_bytes(data[off:off + 2], "big")
        if field["signed"] and raw >= 0x8000:
            raw -= 0x10000
        value = raw * field["scale"]
        if field["unit"] == "°C":
            value -= 273.15
        spa.values[field["addr"]] = value
    return spa


def decode_pia_response(response: str):
    """Decode a PIA Modbus response into a V3PIA object."""
    if not response:
        return None
    if response.startswith("~"):
        response = response[1:]

    if not verify_crc(response):
        _LOGGER.warning("PIA CRC invalid for %s", response)
        return None

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
        if len(data) >= 30:
            pia.system_events         = convert_bytes_to_data("UINT16", data[28], data[29])
        if len(data) >= 36:
            pia.extern_voltage        = convert_bytes_to_data("UINT16", data[34], data[35]) * 0.001
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
        return None

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
        if len(data) >= 48:
            pib.cell_temperature_5 = convert_bytes_to_data("UINT16", data[40], data[41]) * 0.1 - 273.15
            pib.cell_temperature_6 = convert_bytes_to_data("UINT16", data[42], data[43]) * 0.1 - 273.15
            pib.cell_temperature_7 = convert_bytes_to_data("UINT16", data[44], data[45]) * 0.1 - 273.15
            pib.cell_temperature_8 = convert_bytes_to_data("UINT16", data[46], data[47]) * 0.1 - 273.15
        if len(data) >= 50:
            pib.environment_temperature = convert_bytes_to_data("UINT16", data[48], data[49]) * 0.1 - 273.15
        if len(data) >= 52:
            pib.power_temperature = convert_bytes_to_data("UINT16", data[50], data[51]) * 0.1 - 273.15
    except IndexError:
        return None

    return pib


def extract_data_from_message(msg, config_battery_address=None):
    """Parse PIA/PIB/VIA/PIC/SFA/SPA responses into a flat dict."""
    pia_data = pib_data = via = pic = sfa = spa = None
    if not msg:
        return {}

    def get(idx):
        if len(msg) <= idx:
            return ""
        value = msg[idx]
        return value[1:] if isinstance(value, str) and value.startswith("~") else value

    if len(msg) > 0:
        pia_data = decode_pia_response(get(0))
    if len(msg) > 1:
        pib_data = decode_pib_response(get(1))
    if len(msg) > 2:
        via = decode_via_response(get(2), get(3))
    if len(msg) > 4:
        pic = decode_pic_response_modbus(get(4))
    if len(msg) > 5:
        sfa = decode_sfa_response(get(5))
    if len(msg) > 6:
        spa = decode_spa_response(get(6))

    result = {}
    if pia_data:
        for attr in ["pack_voltage", "current", "remaining_capacity", "total_capacity",
                     "total_discharge_capacity", "soc", "soh", "cycle",
                     "avg_cell_voltage", "avg_cell_temperature",
                     "max_cell_voltage", "min_cell_voltage",
                     "max_cell_temperature", "min_cell_temperature",
                     "system_events", "max_discharge_current", "max_charge_current",
                     "extern_voltage"]:
            val = getattr(pia_data, attr, None)
            if val is not None:
                result[attr] = round(val, 3) if isinstance(val, float) else val
    if pib_data:
        for i in range(1, 17):
            val = getattr(pib_data, f"cell{i}_voltage", None)
            if val is not None:
                result[f"cell{i}_voltage"] = round(val, 3)
        for i in range(1, 9):
            val = getattr(pib_data, f"cell_temperature_{i}", None)
            if val is not None:
                result[f"cell_temperature_{i}"] = round(val, 1)
        if pib_data.environment_temperature:
            result["environment_temperature"] = round(pib_data.environment_temperature, 1)
        if pib_data.power_temperature:
            result["power_temperature"] = round(pib_data.power_temperature, 1)
    if via:
        result["manufacturer"] = via.manufacturer
        result["model"] = via.model
        result["serial"] = via.serial
    if pic:
        result["pic_bits"] = pic.bits
    if sfa:
        result["sfa_bits"] = sfa.bits
    if spa:
        for field in SPA_FIELDS:
            result[f"spa_{field['addr']}"] = spa.values.get(field["addr"])
    return result
