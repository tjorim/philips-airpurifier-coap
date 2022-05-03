"""Philips Air Purifier & Humidifier"""
from __future__ import annotations

import logging

from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.config_entries import ConfigEntry


from .philips import model_to_class
from .const import (
    CONF_MODEL,
    DATA_KEY_COORDINATOR,
    DATA_KEY_FAN,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistantType, 
    entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback,
):
    _LOGGER.debug("async_setup_entry called for platform fan")

    host = entry.data[CONF_HOST]
    model = entry.data[CONF_MODEL]
    name = entry.data[CONF_NAME]

    data = hass.data[DOMAIN][host]
    coordinator = data[DATA_KEY_COORDINATOR]

    model_class = model_to_class.get(model)
    if model_class:
        device = model_class(
            coordinator,
            model=model,
            name=name,
        )
    else:
        _LOGGER.error("Unsupported model: %s", model)
        return

    data[DATA_KEY_FAN] = device
    async_add_entities([device], update_before_add=True)