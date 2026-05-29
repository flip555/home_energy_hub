"""Modbus RTU serial/Telnet transport for Seplos BMS V3.

Ported from bms_connector with full RS485 half-duplex handling:
  - reset_input_buffer() before each command
  - Explicit echo consumption — some USB-RS485 adapters loop back
    transmitted bytes into the RX buffer.
  - Byte-level frame synchronisation on [addr, 0x04, LEN] to avoid
    confusing echo bytes or stale frames with the real response.
  - CRC-16 Modbus validation on every received frame.
"""

import asyncio
import logging
import serial
import struct
import telnetlib
import time
from typing import List

_LOGGER = logging.getLogger(__name__)

# Known data-byte counts for V3 Modbus responses
# PIA : 18 registers × 2 = 36 = 0x24
# PIB : 26 registers × 2 = 52 = 0x34
_VALID_DATA_LENS = (0x24, 0x34)

# ---------------------------------------------------------------------------
# CRC-16 Modbus
# ---------------------------------------------------------------------------

def _modbus_crc(data: bytes) -> bytes:
    """Return CRC-16 (Modbus) as 2 bytes, little-endian."""
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return struct.pack("<H", crc)


def _frame_crc_ok(frame: bytes) -> bool:
    """Check that the last 2 bytes of *frame* are a valid Modbus CRC."""
    if len(frame) < 4:
        return False
    payload = frame[:-2]
    expected = _modbus_crc(payload)
    return frame[-2:] == expected


def _expected_data_len(command_hex: str) -> int:
    """Derive the expected response data byte count from a Modbus command."""
    try:
        raw = bytes.fromhex(command_hex)
        count = (raw[4] << 8) | raw[5]
        return count * 2
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Serial transport
# ---------------------------------------------------------------------------

def _read_modbus_frame(ser, expected_addr: int, expected_data_len: int,
                       sync_timeout: float = 2.0) -> bytes:
    """Read one Modbus RTU response frame with byte-level synchronisation."""
    deadline = time.monotonic() + sync_timeout

    while time.monotonic() < deadline:
        # Phase 1 — find [addr, 0x04]
        addr_byte = ser.read(1)
        if not addr_byte:
            continue
        if addr_byte[0] != expected_addr:
            continue

        cmd_byte = ser.read(1)
        if not cmd_byte:
            continue
        if cmd_byte[0] != 0x04:
            continue

        # Phase 2 — read LEN byte
        len_byte = ser.read(1)
        if not len_byte:
            continue
        data_len = len_byte[0]

        if data_len not in _VALID_DATA_LENS:
            _LOGGER.debug("Sync false-positive — LEN=0x%02X not in %s, resyncing",
                          data_len, _VALID_DATA_LENS)
            continue

        if data_len != expected_data_len:
            _LOGGER.debug("Skipping frame LEN=0x%02X (expected 0x%02X) — wrong type",
                          data_len, expected_data_len)
            ser.read(data_len + 2)
            continue

        # Phase 3 — read data + CRC
        frame = bytes([expected_addr, 0x04, data_len]) + ser.read(data_len + 2)

        if len(frame) < 3 + data_len + 2:
            _LOGGER.warning("Incomplete frame — got %d bytes, expected %d",
                            len(frame), 3 + data_len + 2)
            continue

        if not _frame_crc_ok(frame):
            _LOGGER.warning("CRC mismatch on frame (%d bytes): %s",
                            len(frame), frame.hex())
            continue

        return frame

    _LOGGER.warning("Timeout — no valid Modbus frame found for addr=0x%02X in %.1fs",
                    expected_addr, sync_timeout)
    return b""


def send_serial_commands(commands: List[str], port: str,
                         baudrate: int = 19200, timeout: int = 2) -> List[str]:
    """Send Modbus RTU commands over RS485 and return hex-string responses."""
    responses = []
    _LOGGER.debug("send_serial_commands: commands=%s port=%s", commands, port)

    try:
        with serial.Serial(
            port,
            baudrate=baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            timeout=0.2,
        ) as ser:

            for command in commands:
                try:
                    cmd_bytes = bytes.fromhex(command)
                except Exception as e:
                    _LOGGER.error("Invalid command: %s — %s", command, e)
                    responses.append("")
                    continue

                expected_addr = cmd_bytes[0]
                expected_data_len = _expected_data_len(command)

                # Flush, write, consume echo
                ser.reset_input_buffer()
                ser.write(cmd_bytes)

                saved_timeout = ser.timeout
                ser.timeout = 0.15
                echo = ser.read(len(cmd_bytes))
                ser.timeout = saved_timeout

                if len(echo) == len(cmd_bytes):
                    _LOGGER.debug("Echo consumed (%d bytes)", len(echo))
                elif len(echo) > 0:
                    _LOGGER.debug("Partial echo (%d/%d bytes)", len(echo), len(cmd_bytes))

                # Read Modbus response frame
                raw = _read_modbus_frame(ser, expected_addr, expected_data_len)
                responses.append(raw.hex() if raw else "")

                time.sleep(0.3)  # Gap between commands

    except serial.SerialException as e:
        _LOGGER.error("Serial error on %s: %s", port, e)
        return [""] * len(commands)

    return responses


# ---------------------------------------------------------------------------
# Telnet transport
# ---------------------------------------------------------------------------

def send_telnet_commands(commands: List[str], host: str, port: int = 23,
                         timeout: int = 8) -> List[str]:
    """Send Modbus RTU commands via Telnet and return hex-string responses."""
    responses = []
    _LOGGER.debug("send_telnet_commands: connecting to %s:%s", host, port)

    try:
        tn = telnetlib.Telnet(host, port, timeout=5)

        try:
            for command in commands:
                try:
                    cmd_bytes = bytes.fromhex(command)
                except Exception as e:
                    _LOGGER.error("Invalid command: %s — %s", command, e)
                    responses.append("")
                    continue

                tn.write(cmd_bytes)
                time.sleep(0.5)

                chunks = []
                last_data = time.monotonic()
                deadline_time = last_data + timeout

                while time.monotonic() < deadline_time:
                    try:
                        chunk = tn.read_very_eager()
                        if chunk:
                            chunks.append(chunk)
                            last_data = time.monotonic()
                        else:
                            if time.monotonic() - last_data > 0.9:
                                break
                    except EOFError:
                        break
                    time.sleep(0.03)

                raw = b"".join(chunks)
                responses.append(raw.hex())
                _LOGGER.debug("Telnet response for %s: %d bytes",
                              command[:20], len(raw))

        finally:
            tn.close()

    except Exception as e:
        _LOGGER.error("Telnet error on %s:%s — %s", host, port, e)
        return [""] * len(commands)

    return responses


# ---------------------------------------------------------------------------
# Async factory
# ---------------------------------------------------------------------------

async def send_serial_commands_async(commands: List[str], port: str,
                                     baudrate: int = 19200,
                                     timeout: int = 2) -> List[str]:
    """Async wrapper for send_serial_commands (runs in executor)."""
    import functools
    return await asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(send_serial_commands, commands, port, baudrate, timeout),
    )


async def send_telnet_commands_async(commands: List[str], host: str,
                                     port: int = 23,
                                     timeout: int = 8) -> List[str]:
    """Async wrapper for send_telnet_commands (runs in executor)."""
    import functools
    return await asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(send_telnet_commands, commands, host, port, timeout),
    )
