from datetime import timedelta
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)

class WaveshareDataCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client):
        self.client = client
        self.channel_count = entry.data.get("channel_count", 16)
        super().__init__(
            hass,
            _LOGGER,
            name="waveshare_relay",
            update_interval=SCAN_INTERVAL,
        )

    async def _async_update_data(self):
        try:
            return await self.client.read_all_channels()
        except Exception as err:
            raise UpdateFailed(f"Fehler beim Abrufen der Relais-Zustände: {err}")
