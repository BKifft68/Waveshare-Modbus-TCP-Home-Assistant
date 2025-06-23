from homeassistant import config_entries
import voluptuous as vol
from homeassistant.core import callback
from .const import DOMAIN, DEFAULT_PORT, DEFAULT_CHANNELS

class WaveshareRelayConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            user_input["mac"] = user_input["host"].replace(".", "-")
            return self.async_create_entry(title=user_input["host"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Optional("port", default=DEFAULT_PORT): int,
                vol.Optional("channel_count", default=DEFAULT_CHANNELS): int,
            }),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return WaveshareRelayOptionsFlowHandler(config_entry)

class WaveshareRelayOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "channel_count",
                    default=self.config_entry.data.get("channel_count", DEFAULT_CHANNELS)
                ): int,
            }),
        )
