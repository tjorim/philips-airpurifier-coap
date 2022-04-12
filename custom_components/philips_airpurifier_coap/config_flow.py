"""The Philips AirPurifier component."""
from homeassistant import config_entries, exceptions
from homeassistant.components import dhcp
from homeassistant.data_entry_flow import FlowResult

from homeassistant.helpers import config_validation as cv
from homeassistant.const import CONF_HOST, CONF_NAME

from aioairctrl import CoAPClient

from .const import CONF_MODEL, CONF_DEVICE_ID, DOMAIN
from .philips import model_to_class

from typing import Any

import logging
import voluptuous as vol
import ipaddress
import re

_LOGGER = logging.getLogger(__name__)


def host_valid(host: str) -> bool:
    """Return True if hostname or IP address is valid."""
    try:
        if ipaddress.ip_address(host).version in [4, 6]:
            return True
    except ValueError:
        pass
    disallowed = re.compile(r"[^a-zA-Z\d\-]")
    return all(x and not disallowed.search(x) for x in host.split("."))


class PhilipsAirPurifierConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Philips AirPurifier."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self.host: str = None


    def _get_schema(self, user_input):
        """Provide schema for user input."""
        schema = vol.Schema({
            vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, '')): cv.string
        })
        return schema


    async def async_step_dhcp(self, discovery_info: dhcp.DhcpServiceInfo) -> FlowResult:
        _LOGGER.debug(f"async_step_dhcp: called, found: {discovery_info}")
        return self.async_abort(reason="no_ready")


    async def async_step_user(self, user_input: dict[str, Any] = None) -> FlowResult:
        """Handle initial step of user config flow."""

        errors = {}

        # user input was provided, so check and save it
        if user_input is not None:
            try:
                # first some sanitycheck on the host input
                if not host_valid(user_input[CONF_HOST]):
                    raise InvalidHost()
                self.host = user_input[CONF_HOST]
                _LOGGER.debug("trying to configure host: %s", self.host)

                # let's try and connect to an AirPurifier
                try:
                    client = await CoAPClient.create(self.host)
                    _LOGGER.debug("got a valid client")

                    status = await client.get_status()
                    _LOGGER.debug("got status")

                    if client is not None:
                        await client.shutdown()

                except Exception as ex:
                    _LOGGER.warning(r"Failed to connect: %s", ex)
                    raise exceptions.ConfigEntryNotReady from ex

                # autodetect model and name
                model = status['type']
                name = status['name']
                device_id = status['DeviceId']
                user_input[CONF_MODEL] = model
                user_input[CONF_NAME] = name
                user_input[CONF_DEVICE_ID] = device_id
                _LOGGER.debug("Detected host %s as model %s with name: %s", self.host, model, name)

                # check if model is supported
                if not model in model_to_class.keys():
                    return self.async_abort(reason="model_unsupported")

                # use the device ID as unique_id
                unique_id = device_id
                _LOGGER.debug(f"async_step_user: unique_id={unique_id}")

                # set the unique id for the entry, abort if it already exists
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                # compile a name and return the config entry
                return self.async_create_entry(
                    title=model + " " + name,
                    data=user_input
                )

            except InvalidHost:
                errors[CONF_HOST] = "host"
            except exceptions.ConfigEntryNotReady:
                errors[CONF_HOST] = "connect"

        if user_input is None:
            user_input = {}

        # no user_input so far
        # what to ask the user
        schema = self._get_schema(user_input)

        # show the form to the user
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate that hostname/IP address is invalid."""