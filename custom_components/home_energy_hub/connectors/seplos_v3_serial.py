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
import socket
import struct
import time
from typing import List

_LOGGER = logging.getLogger(__name__)

# Known data-byte counts for V3 Modbus responses
# PIA : 18 registers × 2 = 36 = 0x24
# PIB : 26 registers × 2 = 52 = 0x34
_VALID_DATA_LENS_BY_FUNCTION = {
    0x04: (0x24, 0x34, 0x66, 0xd4, 0x14),
    0x01: (0x12, 0x0a),
}
_VALID_DATA_LENS = (0x24, 0x34)


def _valid_data_lens(function_code: int) -> tuple:
    return _VALID_DATA_LENS_BY_FUNCTION.get(function_code, _VALID_DATA_LENS)

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
        function = raw[1]
        count = (raw[4] << 8) | raw[5]
        if function == 0x01:
            return (count + 7) // 8
        return count * 2
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Serial transport
# ---------------------------------------------------------------------------

def _read_modbus_frame(ser, expected_addr: int, expected_data_len: int,
                       sync_timeout: float = 2.0, function_code: int = 0x04) -> bytes:
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
        if cmd_byte[0] != function_code:
            continue

        # Phase 2 — read LEN byte
        len_byte = ser.read(1)
        if not len_byte:
            continue
        data_len = len_byte[0]

        valid_lens = _valid_data_lens(function_code)
        if data_len not in valid_lens:
            _LOGGER.debug("Sync false-positive — LEN=0x%02X not in %s, resyncing",
                          data_len, valid_lens)
            continue

        if data_len != expected_data_len:
            _LOGGER.debug("Skipping frame LEN=0x%02X (expected 0x%02X) — wrong type",
                          data_len, expected_data_len)
            ser.read(data_len + 2)
            continue

        # Phase 3 — read data + CRC
        frame = bytes([expected_addr, function_code, data_len]) + ser.read(data_len + 2)

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
                raw = _read_modbus_frame(ser, expected_addr, expected_data_len, function_code=cmd_bytes[1])
                responses.append(raw.hex() if raw else "")

                time.sleep(0.3)  # Gap between commands

    except serial.SerialException as e:
        _LOGGER.error("Serial error on %s: %s", port, e)
        return [""] * len(commands)

    return responses


# ---------------------------------------------------------------------------
# Telnet transport
# ---------------------------------------------------------------------------

def _read_bytes_until_silence(sock, timeout: float, silence: float = 0.9) -> bytes:
    """Collect bytes until the link goes quiet or the deadline expires."""
    chunks = []
    deadline = time.monotonic() + timeout
    last_data = time.monotonic()

    while True:
        now = time.monotonic()
        if now - last_data > silence or now >= deadline:
            break

        sock.settimeout(min(silence, max(0.01, deadline - now)))
        try:
            chunk = sock.recv(4096)
        except TimeoutError:
            continue
        except OSError:
            break

        if not chunk:
            break

        chunks.append(chunk)
        last_data = time.monotonic()

    return b"".join(chunks)


def send_telnet_commands(commands: List[str], host: str, port: int = 23,
                         timeout: int = 8) -> List[str]:
    """Send Modbus RTU commands over TCP and return hex-string responses."""
    responses: List[str] = []
    _LOGGER.debug("send_telnet_commands: connecting to %s:%s", host, port)

    sock = None
    try:
        sock = socket.create_connection((host, port), timeout=5)

        for command in commands:
            try:
                cmd_bytes = bytes.fromhex(command)
            except Exception as e:
                _LOGGER.error("Invalid command: %s - %s", command, e)
                responses.append("")
                continue

            sock.sendall(cmd_bytes)
            time.sleep(0.5)

            raw = _read_bytes_until_silence(sock, timeout)
            responses.append(raw.hex())
            _LOGGER.debug("Telnet response for %s: %d bytes",
                          command[:20], len(raw))

    except OSError as e:
        _LOGGER.error("Telnet error on %s:%s - %s", host, port, e)
        return [""] * len(commands)
    finally:
        if sock is not None:
            try:
                sock.close()
            except OSError:
                pass

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
