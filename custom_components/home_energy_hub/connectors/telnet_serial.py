"""Telnet Serial connector for Seplos V2 - socket-based."""

import asyncio
import contextlib
import logging
import socket
import time
from typing import List

from ..const import CONF_HOST, CONF_PORT, CONF_BATTERY_ADDRESS

_LOGGER = logging.getLogger(__name__)

# End-of-message heuristic for bridges that do not preserve Modbus framing.
_SILENCE = 0.9


def _read_until_silence(
    sock: socket.socket, timeout: float, silence: float = _SILENCE
) -> str:
    """Collect ASCII text until the link goes quiet or the deadline expires."""
    chunks: list[str] = []
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

        chunks.append(chunk.decode("ascii", errors="ignore"))
        last_data = time.monotonic()

    return "".join(chunks)


class SeplosV2TelnetClient:
    """Socket client for Seplos V2 over a serial-to-Telnet bridge."""

    def __init__(self, host: str, port: int = 23, timeout: int = 8):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: socket.socket | None = None

    async def connect(self):
        """Connect to the bridge."""
        _LOGGER.debug("Connecting to %s:%s", self.host, self.port)
        start = time.perf_counter()
        self._sock = await asyncio.to_thread(
            socket.create_connection, (self.host, self.port), 5
        )
        _LOGGER.info("Telnet connected in %.3f s", time.perf_counter() - start)
        return self

    async def close(self):
        """Close the connection."""
        if self._sock is not None:
            with contextlib.suppress(OSError):
                self._sock.close()
            self._sock = None

    async def send_serial_commands(self, commands: List[str]) -> List[str]:
        """Send commands and collect the '~'-delimited BMS messages."""
        responses: List[str] = []
        _LOGGER.debug("Sending %d commands", len(commands))

        for raw_cmd in commands:
            await asyncio.to_thread(self._sock.sendall, raw_cmd.encode("ascii"))
            await asyncio.sleep(0.1)

            full = await asyncio.to_thread(
                _read_until_silence, self._sock, self.timeout
            )
            full = full.replace("\r", "").replace("\n", "")
            responses.extend("~" + part for part in full.split("~") if part)

        return responses

    async def read_seplos_data(self, config: dict) -> List[str]:
        """Read Seplos V2 data."""
        start = time.perf_counter()
        battery_address = config.get(CONF_BATTERY_ADDRESS, "0x00")

        V2_COMMAND_ARRAY = {
            "0x00": ["~20004642E00200FD37\r", "~20004644E00200FD35\r",
                     "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
            "0x01": ["~20004642E00215FD31\r", "~20004644E00200FD35\r",
                     "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
            "0x02": ["~20004642E00200FD37\r", "~20004644E00200FD35\r",
                     "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
            "0x03": ["~20004642E00200FD37\r", "~20004644E00200FD35\r",
                     "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
        }

        commands = V2_COMMAND_ARRAY.get(battery_address, V2_COMMAND_ARRAY["0x00"])
        result = await self.send_serial_commands(commands)

        _LOGGER.info("Seplos V2 read finished in %.3f seconds", time.perf_counter() - start)
        return result


async def create_client(hass, config: dict, integration_type: str) -> SeplosV2TelnetClient:
    """Create Seplos V2 telnet client."""
    client = SeplosV2TelnetClient(
        host=config[CONF_HOST],
        port=config.get(CONF_PORT, 23)
    )
    await client.connect()
    return client
