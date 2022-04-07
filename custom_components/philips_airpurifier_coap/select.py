"""Philips Air Purifier & Humidifier Selects"""
from __future__ import annotations

import logging
from typing import Any, Callable, List

from aioairctrl import CoAPClient

from homeassistant.components.select import SelectEntity
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ICON,
    CONF_HOST,
    CONF_NAME,
    CONF_ENTITY_CATEGORY,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry

from .philips import Coordinator, PhilipsEntity, model_to_class
from .const import (
    ATTR_LABEL,
    OPTIONS,
    CONF_MODEL,
    DATA_KEY_CLIENT,
    DATA_KEY_COORDINATOR,
    DOMAIN,
    PHILIPS_DEVICE_ID,
    SELECT_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable[[List[Entity], bool], None]
) -> None:
    _LOGGER.debug("async_setup_entry called for platform select")

    host = entry.data[CONF_HOST]
    model = entry.data[CONF_MODEL]
    name = entry.data[CONF_NAME]

    data = hass.data[DOMAIN][host]

    client = data[DATA_KEY_CLIENT]
    coordinator = data[DATA_KEY_COORDINATOR]

    model_class = model_to_class.get(model)
    if model_class:

        available_selects = []
        
        for cls in reversed(model_class.__mro__):
            cls_available_selects = getattr(cls, "AVAILABLE_SELECTS", [])          
            available_selects.extend(cls_available_selects)

        selects = []

        for select in SELECT_TYPES:
            if select in available_selects:
                selects.append(PhilipsSelect(client, coordinator, name, model, select))

        async_add_entities(selects, update_before_add=False)

    else:
        _LOGGER.error("Unsupported model: %s", model)
        return


class PhilipsSelect(PhilipsEntity, SelectEntity):
    """Define a Philips AirPurifier select."""

    _attr_is_on: bool | None = False

    def __init__(
        self,
        client: CoAPClient,
        coordinator: Coordinator,
        name: str,
        model: str,
        select: str
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._model = model
        self._description = SELECT_TYPES[select]
        self._attr_device_class = self._description.get(ATTR_DEVICE_CLASS)
        self._attr_name = f"{name} {self._description[ATTR_LABEL].replace('_', ' ').title()}"
        self._attr_entity_category = self._description.get(CONF_ENTITY_CATEGORY)

        self._attr_options = []
        self._icons = {}
        self._options = {}
        options = self._description.get(OPTIONS)
        _LOGGER.debug(f"select found options: {options}")
        for key, option_tuple in options.items():
            _LOGGER.debug(f"option is: {option_tuple}")
            option_name, icon = option_tuple
            _LOGGER.debug(f"  option_name: {option_name}")
            _LOGGER.debug(f"  icon: {icon}")
            self._attr_options.append(option_name)
            self._icons[option_tuple] = icon
            self._options[key] = option_name

        try:
            device_id = self._device_status[PHILIPS_DEVICE_ID]
            self._attr_unique_id = f"{self._model}-{device_id}-{select.lower()}"
        except Exception as e:
            _LOGGER.error("Failed retrieving unique_id: %s", e)
            raise PlatformNotReady
        self._attrs: dict[str, Any] = {}
        self.kind = select


    @property
    def current_option(self) -> str:
        option = self._device_status.get(self.kind)
        if option in self._options:
            return self._options[option]
        return None


    async def async_select_option(self, option: str) -> None:
        try:
            option_key = next(key for key, value in self._options.items() if value == option)
            _LOGGER.debug("async_selection_option, kind: %s - option: %s - value: %s", self.kind, option, option_key)
            await self._client.set_control_value(self.kind, option_key)
        except Exception as e:
            _LOGGER.error(f"Failed setting option: '{option}' with error: {e}")


    @property
    def icon(self) -> str:
        return self._icons.get(self.current_option)