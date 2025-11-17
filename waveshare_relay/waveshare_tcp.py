import logging
import inspect
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusIOException

_LOGGER = logging.getLogger(__name__)


class ModbusRelayClient:
    def __init__(self, host, port=502, channel_count=16, unit_id=1):
        self.host = host
        self.port = port
        self.channel_count = channel_count
        self.unit_id = unit_id
        # Client wie im Original beim Erzeugen anlegen
        self.client = AsyncModbusTcpClient(host=self.host, port=self.port)

    async def connect(self):
        await self.client.connect()

    async def disconnect(self):
        # close kann je nach pymodbus-Version coroutine oder sync sein
        if not self.client:
            return
        close = getattr(self.client, "close", None)
        if close:
            try:
                if inspect.iscoroutinefunction(close):
                    await close()
                else:
                    close()
            except Exception:
                _LOGGER.exception("Error while closing Modbus client for %s:%s", self.host, self.port)
        self.client = None

    async def _call_read_coils(self, address: int, count: int):
        """
        Versuche kompatible Aufrufvarianten für read_coils:
        1) keyword-first mit unit (neuere pymodbus)
        2) positional (address, count)
        3) Einzelaufrufe pro Coil als letzter Fallback (nicht hier)
        """
        read_fn = getattr(self.client, "read_coils", None)
        if read_fn is None:
            raise RuntimeError("Modbus client has no read_coils")

        # 1) keyword-first (address=..., count=..., unit=...)
        try:
            return await read_fn(address=address, count=count, unit=self.unit_id)
        except TypeError:
            pass

        # 2) positional (address, count)
        try:
            return await read_fn(address, count)
        except TypeError:
            pass

        # 3) try named without unit (address/count only)
        try:
            return await read_fn(address=address, count=count)
        except TypeError:
            pass

        # If none matched, let caller handle fallback
        return None

    async def read_all_channels(self):
        if not self.client:
            raise ConnectionError("Client not connected")

        # Try batch read with compatible variants
        result = await self._call_read_coils(0, self.channel_count)

        # If batch failed (signature mismatch), fallback to reading single coils
        if result is None:
            bits = []
            read_fn = getattr(self.client, "read_coils", None)
            if read_fn is None:
                raise RuntimeError("Modbus client has no read_coils")
            for i in range(self.channel_count):
                single = None
                # try keyword-first with unit
                try:
                    single = await read_fn(address=i, count=1, unit=self.unit_id)
                except TypeError:
                    single = None
                # try positional
                if single is None:
                    try:
                        single = await read_fn(i, 1)
                    except TypeError:
                        single = None
                # try named without unit
                if single is None:
                    try:
                        single = await read_fn(address=i, count=1)
                    except TypeError:
                        single = None

                if single is None:
                    _LOGGER.error("read_coils: no compatible call signature for single coil read")
                    raise ModbusIOException("read_coils single: incompatible client signature")

                if hasattr(single, "isError") and single.isError():
                    raise ModbusIOException(f"read_coils single failed: {single}")

                single_bits = getattr(single, "bits", None) or getattr(single, "coils", None) or []
                bits.append(bool(single_bits[0]) if single_bits else False)

            return {i: bits[i] for i in range(self.channel_count)}

        # Check result for Modbus error
        if hasattr(result, "isError") and result.isError():
            raise ModbusIOException("Modbus read_coils failed")

        bits = getattr(result, "bits", None) or getattr(result, "coils", None) or []
        return {i: bool(bits[i]) if i < len(bits) else False for i in range(self.channel_count)}

    async def set_channel(self, channel, state):
        if not self.client:
            raise ConnectionError("Client not connected")

        write_fn = getattr(self.client, "write_coil", None)
        if write_fn is None:
            raise RuntimeError("Modbus client has no write_coil")

        result = None

        # 1) keyword-first with unit
        try:
            result = await write_fn(address=channel, value=bool(state), unit=self.unit_id)
        except TypeError:
            result = None

        # 2) positional fallback (address, value)
        if result is None:
            try:
                result = await write_fn(channel, bool(state))
            except TypeError:
                result = None

        # 3) named without unit
        if result is None:
            try:
                result = await write_fn(address=channel, value=bool(state))
            except TypeError:
                result = None

        if result is None:
            _LOGGER.error("write_coil: no compatible call signature found")
            raise ModbusIOException("write_coil incompatible with client")

        if hasattr(result, "isError") and result.isError():
            raise ModbusIOException("Modbus write_coil failed")
