"""Telnet Serial connector for Seplos V2 - Final Optimized"""

import asyncio
import logging
import telnetlib
import time
from typing import List

from ..const import CONF_HOST, CONF_PORT, CONF_BATTERY_ADDRESS

_LOGGER = logging.getLogger(__name__)


class SeplosV2TelnetClient:
    """Telnet client for Seplos V2 protocol over serial-to-telnet bridge."""

    def __init__(self, host: str, port: int = 23, timeout: int = 8):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._tn = None

    async def connect(self):
        """Connect to telnet server."""
        _LOGGER.debug("Connecting to %s:%s", self.host, self.port)
        start = time.perf_counter()
        self._tn = await asyncio.to_thread(
            telnetlib.Telnet, self.host, self.port, timeout=5
        )
        _LOGGER.info("Telnet connected in %.3f s", time.perf_counter() - start)
        return self

    async def close(self):
        """Close telnet connection."""
        if self._tn:
            await asyncio.to_thread(self._tn.close)
            self._tn = None

    async def send_serial_commands(self, commands: List[str]) -> List[str]:
        """Send commands and collect responses efficiently."""
        responses = []
        _LOGGER.debug("Sending %d commands", len(commands))

        for raw_cmd in commands:
            # Send command
            await asyncio.to_thread(self._tn.write, raw_cmd.encode('ascii'))
            await asyncio.sleep(0.1)

            # Receive response
            messages = []
            last_data = time.perf_counter()

            while True:
                chunk = await asyncio.to_thread(self._tn.read_very_eager)
                if chunk:
                    messages.append(chunk.decode('ascii', errors='ignore'))
                    last_data = time.perf_counter()
                else:
                    # No more data for ~900ms -> assume command is done
                    if time.perf_counter() - last_data > 0.9:
                        break

                # Safety timeout
                if time.perf_counter() - last_data > self.timeout:
                    break

                await asyncio.sleep(0.03)

            # Parse responses
            full = ''.join(messages).replace('\r', '').replace('\n', '')
            parts = [p for p in full.split('~') if p]
            responses.extend(['~' + p for p in parts])

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
