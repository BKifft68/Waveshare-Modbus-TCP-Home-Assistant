import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .waveshare_tcp import ModbusRelayClient
from .coordinator import WaveshareDataCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    host = entry.data["host"]
    port = entry.data.get("port", 502)
    channel_count = entry.data.get("channel_count", 16)
    mac = entry.data.get("mac", f"{host.replace('.', '-')}_relay")

    client = ModbusRelayClient(host, port, channel_count)
    await client.connect()

    coordinator = WaveshareDataCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "client": client,
        "coordinator": coordinator,
        "mac": mac,
    }

    # Korrekte Methode für neuere Home Assistant Versionen
    await hass.config_entries.async_forward_entry_setups(entry, ["switch"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].pop(entry.entry_id)
    await data["client"].disconnect()
    return await hass.config_entries.async_unload_platforms(entry, ["switch"])
