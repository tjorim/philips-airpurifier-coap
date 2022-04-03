"""Support for Philips AirPurifier with CoAP."""
from __future__ import annotations

import asyncio
import logging

from aioairctrl import CoAPClient
import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_ICON, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.config_entries import ConfigEntry

from .philips import PhilipsEntity, Coordinator

from .const import (
    CONF_MODEL,
    DATA_KEY_CLIENT,
    DATA_KEY_COORDINATOR,
    DEFAULT_ICON,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.All(
            cv.ensure_list,
            [
                vol.Schema(
                    {
                        vol.Required(CONF_HOST): cv.string,
                        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                        vol.Optional(CONF_ICON, default=DEFAULT_ICON): cv.icon,
                    },
                )
            ],
        )
    },
    extra=vol.ALLOW_EXTRA,
)

PLATFORMS = ["fan", "sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("async_setup_entry called")
    return False


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    
    for p in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(entry, p)

    hass.data[DOMAIN].pop(entry.entry_id)

    return True


async def async_setup_old(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Philips AirPurifier integration."""
    hass.data[DOMAIN] = {}

    async def async_setup_air_purifier(conf: ConfigType):
        host = conf[CONF_HOST]

        _LOGGER.debug("Setting up %s integration with %s", DOMAIN, host)

        try:
            client = await CoAPClient.create(host)
        except Exception as ex:
            _LOGGER.warning(r"Failed to connect: %s", ex)
            raise ConfigEntryNotReady from ex

        coordinator = Coordinator(client)

        hass.data[DOMAIN][host] = {
            DATA_KEY_CLIENT: client,
            DATA_KEY_COORDINATOR: coordinator,
        }

        await coordinator.async_first_refresh()

        # autodetect model and name
        model = coordinator.status['type']
        name = coordinator.status['name']
        conf[CONF_MODEL] = model
        conf[CONF_NAME] = name
        _LOGGER.debug("Detected host %s as model %s with name: %s", host, model, name)

        for platform in PLATFORMS:
            hass.async_create_task(
                discovery.async_load_platform(hass, platform, DOMAIN, conf, config)
            )

    tasks = [async_setup_air_purifier(conf) for conf in config[DOMAIN]]
    if tasks:
        await asyncio.wait(tasks)

    return True