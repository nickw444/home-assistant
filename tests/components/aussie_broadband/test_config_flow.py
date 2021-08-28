"""Test the Aussie Broadband config flow."""
from unittest.mock import patch

from aussiebb.asyncio import AuthenticationException

from homeassistant import config_entries
from homeassistant.components.aussie_broadband.const import CONF_SERVICES, DOMAIN
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME  # CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)

TEST_USERNAME = "test-username"
TEST_PASSWORD = "test-password"
FAKE_SERVICES = [
    {
        "service_id": "12345678",
        "description": "Fake ABB NBN Service",
        "type": "NBN",
        "name": "NBN",
    },
    {
        "service_id": "87654321",
        "description": "Fake ABB Mobile Service",
        "type": "PhoneMobile",
        "name": "Mobile",
    },
]


async def test_form(hass: HomeAssistant) -> None:
    """Test the form happy path with a single service."""
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result1["type"] == RESULT_TYPE_FORM
    assert result1["errors"] is None

    with patch("aussiebb.asyncio.AussieBB.__init__", return_value=None), patch(
        "aussiebb.asyncio.AussieBB.login", return_value=True
    ), patch(
        "aussiebb.asyncio.AussieBB.get_services", return_value=[FAKE_SERVICES[0]]
    ), patch(
        "homeassistant.components.aussie_broadband.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result1["flow_id"],
            {
                CONF_USERNAME: TEST_USERNAME,
                CONF_PASSWORD: TEST_PASSWORD,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == TEST_USERNAME
    assert result2["data"] == {
        CONF_USERNAME: TEST_USERNAME,
        CONF_PASSWORD: TEST_PASSWORD,
    }
    assert result2["options"] == {CONF_SERVICES: ["12345678"]}
    assert len(mock_setup_entry.mock_calls) == 1

    # Test Already configured
    result3 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch("aussiebb.asyncio.AussieBB.__init__", return_value=None), patch(
        "aussiebb.asyncio.AussieBB.login", return_value=True
    ), patch(
        "aussiebb.asyncio.AussieBB.get_services", return_value=[FAKE_SERVICES[0]]
    ), patch(
        "homeassistant.components.aussie_broadband.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            {
                CONF_USERNAME: TEST_USERNAME,
                CONF_PASSWORD: TEST_PASSWORD,
            },
        )
        await hass.async_block_till_done()

    assert result4["type"] == RESULT_TYPE_ABORT

    # Test reauth
    result5 = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_REAUTH},
        data={
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )
    assert result5["step_id"] == "reauth"

    with patch("aussiebb.asyncio.AussieBB.__init__", return_value=None), patch(
        "aussiebb.asyncio.AussieBB.login", return_value=True
    ), patch("aussiebb.asyncio.AussieBB.get_services", return_value=[FAKE_SERVICES[0]]):

        result6 = await hass.config_entries.flow.async_configure(
            result5["flow_id"],
            {
                CONF_PASSWORD: "test-newpassword",
            },
        )
        await hass.async_block_till_done()

        assert result6["type"] == "abort"
        assert result6["reason"] == "reauth_successful"


async def test_no_services(hass: HomeAssistant) -> None:
    """Test when there are no services."""
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result1["type"] == RESULT_TYPE_FORM
    assert result1["errors"] is None

    with patch("aussiebb.asyncio.AussieBB.__init__", return_value=None), patch(
        "aussiebb.asyncio.AussieBB.login", return_value=True
    ), patch("aussiebb.asyncio.AussieBB.get_services", return_value=[]), patch(
        "homeassistant.components.aussie_broadband.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result1["flow_id"],
            {
                CONF_USERNAME: TEST_USERNAME,
                CONF_PASSWORD: TEST_PASSWORD,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_ABORT
    assert result2["reason"] == "no_services_found"
    assert len(mock_setup_entry.mock_calls) == 0


async def test_form_multiple_services(hass: HomeAssistant) -> None:
    """Test the config flow with multiple services."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert result["errors"] is None

    with patch("aussiebb.asyncio.AussieBB.__init__", return_value=None), patch(
        "aussiebb.asyncio.AussieBB.login", return_value=True
    ), patch("aussiebb.asyncio.AussieBB.get_services", return_value=FAKE_SERVICES):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: TEST_USERNAME,
                CONF_PASSWORD: TEST_PASSWORD,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["step_id"] == "service"
    assert result2["errors"] is None

    with patch(
        "homeassistant.components.aussie_broadband.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_SERVICES: [FAKE_SERVICES[1]["service_id"]]},
        )
        await hass.async_block_till_done()

    assert result3["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result3["title"] == TEST_USERNAME
    assert result3["data"] == {
        CONF_USERNAME: TEST_USERNAME,
        CONF_PASSWORD: TEST_PASSWORD,
    }
    assert result3["options"] == {
        CONF_SERVICES: [FAKE_SERVICES[1]["service_id"]],
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test invalid auth is handled."""
    result1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch("aussiebb.asyncio.AussieBB.__init__", return_value=None), patch(
        "aussiebb.asyncio.AussieBB.login", side_effect=AuthenticationException()
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result1["flow_id"],
            {
                CONF_USERNAME: TEST_USERNAME,
                CONF_PASSWORD: TEST_PASSWORD,
            },
        )

    assert result2["type"] == RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "invalid_auth"}
