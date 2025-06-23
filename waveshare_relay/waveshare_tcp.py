import logging
from pymodbus.client import AsyncModbusTcpClient

_LOGGER = logging.getLogger(__name__)

class ModbusRelayClient:
    def __init__(self, host, port=502, channel_count=16):
        self.host = host
        self.port = port
        self.channel_count = channel_count
        self.client = AsyncModbusTcpClient(host=self.host, port=self.port)

    async def connect(self):
        await self.client.connect()

    async def disconnect(self):
        await self.client.close()

    async def read_all_channels(self):
        result = await self.client.read_coils(address=0, count=self.channel_count, slave=1)
        if not result.isError():
            return {i: result.bits[i] for i in range(self.channel_count)}
        raise IOError("Modbus read_coils failed")

    async def set_channel(self, channel, state):
        await self.client.write_coil(address=channel, value=bool(state), slave=1)
