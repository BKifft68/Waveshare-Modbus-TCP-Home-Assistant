from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    mac = data["mac"]
    channel_count = coordinator.channel_count

    entities = [
        WaveshareRelaySwitch(coordinator, data["client"], mac, i)
        for i in range(channel_count)
    ]
    async_add_entities(entities)

class WaveshareRelaySwitch(CoordinatorEntity, SwitchEntity):
    def __init__(self, coordinator, client, mac, channel):
        super().__init__(coordinator)
        self._client = client
        self._channel = channel
        self._mac = mac
        self._attr_name = f"Relay Kanal {channel + 1}"
        self._attr_unique_id = f"{mac}_relay_{channel}"

    @property
    def is_on(self):
        return self.coordinator.data.get(self._channel, False)

    async def async_turn_on(self, **kwargs):
        await self._client.set_channel(self._channel, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        await self._client.set_channel(self._channel, False)
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, f"{self._mac}_relay_{self._channel}")},
            "name": f"Relay Kanal {self._channel + 1}",
            "manufacturer": "Waveshare",
            "model": "POE ETH 16CH TCP",
            "sw_version": "1.1.0",
        }
