"""Config flow for Aussie Broadband integration."""
from __future__ import annotations

from typing import Any

from aussiebb.asyncio import AussieBB, AuthenticationException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .const import CONF_SERVICES, DOMAIN, SERVICE_ID


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aussie Broadband."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.data: dict = {}
        self.options: dict = {CONF_SERVICES: []}
        self.services = None
        self.client = None

    async def auth(self, user_input: dict[str]):
        """Reusable Auth Helper."""
        errors = {}
        try:
            self.client = AussieBB(
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
                async_get_clientsession(self.hass),
            )
            await self.client.login()
        except AuthenticationException:
            errors["base"] = "invalid_auth"

        return errors

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            errors = await self.auth(user_input)

            if self.client is not None:
                await self.async_set_unique_id(user_input[CONF_USERNAME])
                self._abort_if_unique_id_configured()

                self.data = user_input
                self.services = await self.client.get_services()

                if len(self.services) == 0:
                    return self.async_abort(reason="no_services_found")

                if len(self.services) == 1:
                    # self.options[CONF_SERVICES] = [str(self.services[0][SERVICE_ID])]
                    return self.async_create_entry(
                        title=self.data[CONF_USERNAME],
                        data=self.data,
                        options={CONF_SERVICES: [str(self.services[0][SERVICE_ID])]},
                    )

                # account has more than one service, select service to add
                return await self.async_step_service()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_service(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the optional service selection step."""
        if user_input is not None:
            # self.options[CONF_SERVICES] = user_input[CONF_SERVICES]
            return self.async_create_entry(
                title=self.data[CONF_USERNAME], data=self.data, options=user_input
            )

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
        errors = {}
        if user_input and user_input.get(CONF_USERNAME):
            self.username = user_input[CONF_USERNAME]
            self.context["title_placeholders"] = {CONF_USERNAME: self.username}

        elif user_input and user_input.get(CONF_PASSWORD):
            data = {
                CONF_USERNAME: self.username,
                CONF_PASSWORD: user_input[CONF_PASSWORD],
            }
            errors = await self.auth(data)

            if self.client is not None:
                entry = await self.async_set_unique_id(self.username)
                self.hass.config_entries.async_update_entry(
                    entry,
                    data=data,
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

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
