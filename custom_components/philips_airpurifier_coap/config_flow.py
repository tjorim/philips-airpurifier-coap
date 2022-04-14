"""The Philips AirPurifier component."""
import asyncio
import async_timeout
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
        self._host: str = None
        self._model: str = None
        self._device_id: str = None
        self._name: str = None


    def _get_schema(self, user_input):
        """Provide schema for user input."""
        schema = vol.Schema({
            vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, '')): cv.string
        })
        return schema


    async def async_step_dhcp(self, discovery_info: dhcp.DhcpServiceInfo) -> FlowResult:
        """Handle initial step of auto discovery flow."""
        _LOGGER.debug(f"async_step_dhcp: called, found: {discovery_info}")

        self._host = discovery_info.ip
        _LOGGER.debug(f"trying to configure host: {self._host}")

        # let's try and connect to an AirPurifier
        try:
            client = None

            # try for 10s to get a valid client
            async with async_timeout.timeout(10):
                client = await CoAPClient.create(self._host)
                _LOGGER.debug(f"got a valid client for host {self._host}")

            # we give it 10s to get a status, otherwise we abort
            # wrap the query for status
            def get_status(client: CoAPClient):
                _LOGGER.debug(f"trying to get status")
                status = client.get_status()
                _LOGGER.debug("got status")
                return status

            # now make this a process for 10s
            async with async_timeout.timeout(10):
                status = await get_status(client)

            if client is not None:
                await client.shutdown()

            # get the status out of the queue
            _LOGGER.debug(f"status for host {self._host} is: {status}")

        except asyncio.TimeoutError:
            _LOGGER.warning(r"Host %s doesn't answer like a supported Philips AirPurifier, aborting", self._host)
            self.async_abort(reason="model_unsupported")

        except Exception as ex:
            _LOGGER.warning(r"Failed to connect: %s", ex)
            raise exceptions.ConfigEntryNotReady from ex

        # autodetect model and name
        self._model = status['type']
        self._name = status['name']
        self._device_id = status['DeviceId']
        _LOGGER.debug("Detected host %s as model %s with name: %s", self._host, self._model, self._name)

        # check if model is supported
        if not self._model in model_to_class.keys():
            _LOGGER.warn(f"Model {self._model} found, but not supported. Aborting discovery.")
            return self.async_abort(reason="model_unsupported")

        # use the device ID as unique_id
        unique_id = self._device_id
        _LOGGER.debug(f"async_step_user: unique_id={unique_id}")

        # set the unique id for the entry, abort if it already exists
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured()

        # store the data for the next step to get confirmation
        self.context.update({
            "title_placeholders": {
                CONF_NAME: self._model + " " + self._name,
            }
        })

        # show the confirmation form to the user
        _LOGGER.debug(f"waiting for async_step_dhcp_confirm")
        return await self.async_step_dhcp_confirm()


    async def async_step_dhcp_confirm(
        self,
        user_input: dict[str, Any] = None
    ) -> FlowResult:
        """Confirm the dhcp discovered data."""
        _LOGGER.debug(f"async_step_dhcp_confirm called with user_input: {user_input}")

        # user input was provided, so check and save it
        if user_input is not None:
            _LOGGER.debug(f"entered creation for model {self._model} with name '{self._name}' at {self._host}")
            user_input[CONF_MODEL] = self._model
            user_input[CONF_NAME] = self._name
            user_input[CONF_DEVICE_ID] = self._device_id
            user_input[CONF_HOST] = self._host

            return self.async_create_entry(
                title=self._model + " " + self._name,
                data=user_input
            )

        _LOGGER.debug(f"showing form")
        # show the form to the user
        return self.async_show_form(
            step_id="dhcp_confirm",
        )



    async def async_step_user(self, user_input: dict[str, Any] = None) -> FlowResult:
        """Handle initial step of user config flow."""

        errors = {}

        # user input was provided, so check and save it
        if user_input is not None:
            try:
                # first some sanitycheck on the host input
                if not host_valid(user_input[CONF_HOST]):
                    raise InvalidHost()
                self._host = user_input[CONF_HOST]
                _LOGGER.debug("trying to configure host: %s", self._host)

                # let's try and connect to an AirPurifier
                try:
                    client = await CoAPClient.create(self._host)
                    _LOGGER.debug("got a valid client")

                    status = await client.get_status()
                    _LOGGER.debug("got status")

                    if client is not None:
                        await client.shutdown()

                except Exception as ex:
                    _LOGGER.warning(r"Failed to connect: %s", ex)
                    raise exceptions.ConfigEntryNotReady from ex

                # autodetect model and name
                self._model = status['type']
                self._name = status['name']
                self._device_id = status['DeviceId']
                user_input[CONF_MODEL] = self._model
                user_input[CONF_NAME] = self._name
                user_input[CONF_DEVICE_ID] = self._device_id
                _LOGGER.debug("Detected host %s as model %s with name: %s", self._host, self._model, self._name)

                # check if model is supported
                if not self._model in model_to_class.keys():
                    return self.async_abort(reason="model_unsupported")

                # use the device ID as unique_id
                unique_id = self._device_id
                _LOGGER.debug(f"async_step_user: unique_id={unique_id}")

                # set the unique id for the entry, abort if it already exists
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                # compile a name and return the config entry
                return self.async_create_entry(
                    title=self._model + " " + self._name,
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