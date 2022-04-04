"""Philips Air Purifier & Humidifier"""
from __future__ import annotations

import logging
from typing import Callable, List, Optional

import voluptuous as vol

from homeassistant.const import CONF_HOST, CONF_ICON, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType, HomeAssistantType
from homeassistant.config_entries import ConfigEntry


from .philips import model_to_class
from .const import (
    CONF_MODEL,
    DATA_KEY_CLIENT,
    DATA_KEY_COORDINATOR,
    DATA_KEY_FAN,
    DEFAULT_ICON,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistantType, 
    entry: ConfigEntry, 
    async_add_entities: Callable
):
    _LOGGER.debug("async_setup_entry called for platform fan")

    host = entry.data[CONF_HOST]
    model = entry.data[CONF_MODEL]
    name = entry.data[CONF_NAME]

    data = hass.data[DOMAIN][host]

    model_class = model_to_class.get(model)
    if model_class:
        device = model_class(
            data[DATA_KEY_CLIENT],
            data[DATA_KEY_COORDINATOR],
            model=model,
            name=name,
            icon=DEFAULT_ICON
        )
    else:
        _LOGGER.error("Unsupported model: %s", model)
        return

    data[DATA_KEY_FAN] = device
    async_add_entities([device], update_before_add=True)

    def wrapped_async_register(
        domain: str,
        service: str,
        service_func: Callable,
        schema: Optional[vol.Schema] = None,
    ):
        async def service_func_wrapper(service_call):
            service_data = service_call.data.copy()
            entity_id = service_data.pop("entity_id", None)
            devices = [
                d
                for entry in hass.data[DOMAIN].values()
                if (d := entry[DATA_KEY_FAN]).entity_id == entity_id
            ]
            for d in devices:
                device_service_func = getattr(d, service_func.__name__)
                return await device_service_func(**service_data)

        hass.services.async_register(
            domain=domain,
            service=service,
            service_func=service_func_wrapper,
            schema=schema,
        )

    device._register_services(wrapped_async_register)


async def async_setup_platform_old(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: Callable[[List[Entity], bool], None],
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    _LOGGER.debug("async_setup_platform called")

    if discovery_info is None:
        return

    host = discovery_info[CONF_HOST]
    model = discovery_info[CONF_MODEL]
    name = discovery_info[CONF_NAME]
    icon = discovery_info[CONF_ICON]
    data = hass.data[DOMAIN][host]

    model_class = model_to_class.get(model)
    if model_class:
        device = model_class(
            data[DATA_KEY_CLIENT],
            data[DATA_KEY_COORDINATOR],
            model=model,
            name=name,
            icon=icon,
        )
    else:
        _LOGGER.error("Unsupported model: %s", model)
        return

    data[DATA_KEY_FAN] = device
    async_add_entities([device], update_before_add=True)

    def wrapped_async_register(
        domain: str,
        service: str,
        service_func: Callable,
        schema: Optional[vol.Schema] = None,
    ):
        async def service_func_wrapper(service_call):
            service_data = service_call.data.copy()
            entity_id = service_data.pop("entity_id", None)
            devices = [
                d
                for entry in hass.data[DOMAIN].values()
                if (d := entry[DATA_KEY_FAN]).entity_id == entity_id
            ]
            for d in devices:
                device_service_func = getattr(d, service_func.__name__)
                return await device_service_func(**service_data)

        hass.services.async_register(
            domain=domain,
            service=service,
            service_func=service_func_wrapper,
            schema=schema,
        )

    device._register_services(wrapped_async_register)


