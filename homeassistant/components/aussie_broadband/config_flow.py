"""Config flow for Aussie Broadband integration."""
from __future__ import annotations

from typing import Any

from aussiebb.asyncio import AussieBB, AuthenticationException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import CONF_SERVICES, DOMAIN, SERVICE_ID


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aussie Broadband."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.data = {}
        self.options = {}
        self.services = None
        self.client = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        default_username = None
        default_password = None
        if user_input is not None:
            try:
                self.client = await self.hass.async_add_executor_job(
                    AussieBB, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                )
                await self.client.login()
            except AuthenticationException:
                errors["base"] = "invalid_auth"

            if self.client is not None:
                self.data.update(user_input)
                self.services = await self.client.get_services()
                if len(self.services) == 0:
                    return self.async_abort(reason="no_services_found")

                if len(self.services) == 1:
                    return await self.create_entry(self.services)

                # account has more than one service, select service to add
                if (
                    self.source == config_entries.SOURCE_REAUTH
                    and CONF_SERVICES in user_input
                ):
                    return await self.create_entry(user_input)
                return await self.async_step_service()
            default_username = user_input.get(CONF_USERNAME)
            default_password = user_input.get(CONF_PASSWORD)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME, default_username): str,
                    vol.Required(CONF_PASSWORD, default_password): str,
                }
            ),
            errors=errors,
        )

    async def async_step_service(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the service selection step."""
        print(user_input)
        if user_input is not None:
            return await self.create_entry(user_input[CONF_SERVICES])

        service_options = {str(s[SERVICE_ID]): s["description"] for s in self.services}
        return self.async_show_form(
            step_id="service",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SERVICES, default=list(service_options.keys())
                    ): cv.multi_select(service_options)
                }
            ),
        )

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle reauth."""
        return await self.async_step_user(user_input)

    async def create_entry(self, services):
        """Create entry for a service."""
        self.data[CONF_SERVICES] = services

        entry = await self.async_set_unique_id(self.data[CONF_USERNAME])

        if self.source == config_entries.SOURCE_REAUTH:
            self.hass.config_entries.async_update_entry(entry, data=self.data)
            await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=self.data[CONF_USERNAME], data=self.data)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow for picking services."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            print(user_input)
            return self.async_create_entry(title="", data=user_input)
            # await self.hass.config_entries.async_reload(self.config_entry.entry_id)

        data = self.hass.data[DOMAIN][self.config_entry.entry_id]
        services = await data["client"].get_services()
        service_options = {str(s[SERVICE_ID]): s["description"] for s in services}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SERVICES,
                        default=self.config_entry.options.get(CONF_SERVICES),
                    ): cv.multi_select(service_options)
                }
            ),
        )
