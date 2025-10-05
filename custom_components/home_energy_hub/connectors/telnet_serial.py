"""Telnet Serial connector for Seplos V2."""

import asyncio
import logging
import telnetlib
from typing import List

from ..const import CONF_HOST, CONF_PORT, CONF_BATTERY_ADDRESS, CONF_PACK_MODE

_LOGGER = logging.getLogger(__name__)

class SeplosV2TelnetClient:
    """Telnet client for Seplos V2 protocol over serial-to-telnet bridge."""
    
    def __init__(self, host: str, port: int = 23, timeout: int = 10):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._tn = None

    async def connect(self):
        """Connect to telnet server."""
        self._tn = telnetlib.Telnet(self.host, self.port, self.timeout)
        return self

    async def close(self):
        """Close telnet connection."""
        if self._tn:
            self._tn.close()

    async def send_serial_commands(self, commands: List[str], collect_all: bool = False) -> List[str]:
        """Send serial commands and collect responses."""
        responses = []
        _LOGGER.debug("Sending commands via telnet: %s", commands)

        try:
            if collect_all:
                # Send all commands first
                for command in commands:
                    self._tn.write(command.encode())
                    await asyncio.sleep(0.3)
                
                # Collect all responses
                messages = []
                end_time = asyncio.get_event_loop().time() + self.timeout
                while asyncio.get_event_loop().time() < end_time:
                    try:
                        response = self._tn.read_very_eager().decode()
                        if response:
                            messages.append(response)
                    except EOFError:
                        break
                    await asyncio.sleep(0.1)
                
                full_response = ''.join(messages).replace('\r', '').replace('\n', '')
                parts = full_response.split('~')
                responses = ['~' + part for part in parts if part]
            else:
                # Send commands one by one and collect responses immediately
                for command in commands:
                    _LOGGER.debug("Sending command: %s", command)
                    self._tn.write(command.encode())
                    await asyncio.sleep(0.3)
                    
                    try:
                        response = self._tn.read_very_eager().decode().replace('\r', '').replace('\n', '')
                        if response:
                            responses.append(response)
                    except EOFError:
                        pass
            
            _LOGGER.debug("Received responses: %s", responses)
            return responses
            
        except Exception as err:
            _LOGGER.error("Telnet communication error: %s", err)
            raise

    async def read_seplos_data(self, config: dict) -> List[str]:
        """Read Seplos V2 data using the protocol from reference file."""
        battery_address = config.get(CONF_BATTERY_ADDRESS, "0x00")
        pack_mode = config.get(CONF_PACK_MODE, "single")
        
        # Seplos V2 command array from reference file
        V2_COMMAND_ARRAY = {
            "0x00": ["~20004642E00200FD37\r", "~20004644E00200FD35\r", "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
            "0x01": ["~20004642E00215FD31\r", "~20004644E00200FD35\r", "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
            "0x02": ["~20004642E00200FD37\r", "~20004644E00200FD35\r", "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
            "0x03": ["~20004642E00200FD37\r", "~20004644E00200FD35\r", "~20004647E00200FD32\r", "~20004651E00200FD37\r"],
        }
        
        commands = V2_COMMAND_ARRAY.get(battery_address, V2_COMMAND_ARRAY["0x00"])
        
        if pack_mode == "single":
            data = await self.send_serial_commands(commands, collect_all=True)
        else:
            data = await self.send_serial_commands(commands, collect_all=True)
            
        return data

async def create_client(hass, config: dict, integration_type: str) -> SeplosV2TelnetClient:
    """Create Seplos V2 telnet client."""
    client = SeplosV2TelnetClient(
        host=config[CONF_HOST],
        port=config.get(CONF_PORT, 23),
        timeout=10
    )
    await client.connect()
    return client