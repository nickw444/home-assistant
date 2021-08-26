"""Config flow for Aussie Broadband integration."""
from __future__ import annotations

from typing import Any

from aussiebb import AussieBB, AuthenticationException
import voluptuous as vol

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlow as ConfigFlowBase
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import CONF_SERVICES, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ConfigFlow(ConfigFlowBase, domain=DOMAIN):
    """Handle a config flow for Aussie Broadband."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.data = {}
        self.services = None
        self.client = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
            )

        errors = {}
        try:
            self.client = await self.hass.async_add_executor_job(
                AussieBB, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
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
            return await self.async_step_service()

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_service(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the service selection step."""

        if user_input is not None:
            return await self.create_entry(user_input[CONF_SERVICES])

        service_options = {s["service_id"]: s["description"] for s in self.services}
        return self.async_show_form(
            step_id="service",
            data_schema=vol.Schema(
                {vol.Required(CONF_SERVICES): cv.multi_select(service_options)}
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
        if self.source == SOURCE_REAUTH:
            self.hass.config_entries.async_update_entry(entry, data=self.data)
            await self.hass.config_entries.async_reload(entry.entry_id)
            return self.async_abort(reason="reauth_successful")

        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=self.data[CONF_USERNAME], data=self.data)
