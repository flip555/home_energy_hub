"""USB-RS485 Serial connector for Seplos V2."""

import asyncio
import logging
import serial
from typing import List

from ..const import CONF_SERIAL_PORT, CONF_BAUD_RATE, CONF_BATTERY_ADDRESS, CONF_PACK_MODE

_LOGGER = logging.getLogger(__name__)

class SeplosV2SerialClient:
    """Custom serial client for Seplos V2 protocol."""
    
    def __init__(self, port: str, baudrate: int = 19200, timeout: int = 2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._ser = None

    async def connect(self):
        """Connect to serial port."""
        self._ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout,
            bytesize=8,
            parity='N',
            stopbits=1
        )
        return self

    async def close(self):
        """Close serial connection."""
        if self._ser and self._ser.is_open:
            self._ser.close()

    async def send_serial_commands(self, commands: List[str], collect_all: bool = False) -> List[str]:
        """Send serial commands and collect responses (from reference file)."""
        responses = []
        _LOGGER.debug("Sending commands: %s", commands)

        try:
            if collect_all:
                for command in commands:
                    self._ser.write(command.encode())
                    await asyncio.sleep(0.3)
                
                messages = []
                end_time = asyncio.get_event_loop().time() + self.timeout
                while asyncio.get_event_loop().time() < end_time:
                    if self._ser.in_waiting > 0:
                        response = self._ser.read(self._ser.in_waiting).decode()
                        messages.append(response)
                    await asyncio.sleep(0.1)
                
                full_response = ''.join(messages).replace('\r', '').replace('\n', '')
                parts = full_response.split('~')
                responses = ['~' + part for part in parts if part]
            else:
                for command in commands:
                    _LOGGER.debug("Sending command: %s", command)
                    self._ser.write(command.encode())
                    await asyncio.sleep(0.3)
                    response = self._ser.read(self._ser.in_waiting).decode().replace('\r', '').replace('\n', '')
                    if response:
                        responses.append(response)
            
            _LOGGER.debug("Received responses: %s", responses)
            return responses
            
        except Exception as err:
            _LOGGER.error("Serial communication error: %s", err)
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

async def create_client(hass, config: dict, integration_type: str) -> SeplosV2SerialClient:
    """Create Seplos V2 serial client."""
    client = SeplosV2SerialClient(
        port=config[CONF_SERIAL_PORT],
        baudrate=config.get(CONF_BAUD_RATE, 19200),
        timeout=2
    )
    await client.connect()
    return client