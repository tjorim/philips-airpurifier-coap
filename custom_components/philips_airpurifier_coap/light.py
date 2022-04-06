"""Philips Air Purifier & Humidifier Switches"""
from __future__ import annotations

import logging
from typing import Any, Callable, List

from aioairctrl import CoAPClient

from homeassistant.components.light import (
    LightEntity,
    ATTR_BRIGHTNESS,
    COLOR_MODE_BRIGHTNESS,
    COLOR_MODE_ONOFF,
)
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
    DIMMABLE,
    SWITCH_ON,
    SWITCH_OFF,
    CONF_MODEL,
    DATA_KEY_CLIENT,
    DATA_KEY_COORDINATOR,
    DOMAIN,
    PHILIPS_DEVICE_ID,
    LIGHT_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable[[List[Entity], bool], None]
) -> None:
    _LOGGER.debug("async_setup_entry called for platform switch")

    host = entry.data[CONF_HOST]
    model = entry.data[CONF_MODEL]
    name = entry.data[CONF_NAME]

    data = hass.data[DOMAIN][host]

    client = data[DATA_KEY_CLIENT]
    coordinator = data[DATA_KEY_COORDINATOR]

    model_class = model_to_class.get(model)
    if model_class:

        available_lights = []
        
        for cls in reversed(model_class.__mro__):
            cls_available_lights = getattr(cls, "AVAILABLE_LIGHTS", [])          
            available_lights.extend(cls_available_lights)
        
        lights = []

        for light in LIGHT_TYPES:
            if light in available_lights:
                lights.append(PhilipsLight(client, coordinator, name, model, light))

        async_add_entities(lights, update_before_add=False)

    else:
        _LOGGER.error("Unsupported model: %s", model)
        return


class PhilipsLight(PhilipsEntity, LightEntity):
    """Define a Philips AirPurifier light."""

    _attr_is_on: bool | None = False

    def __init__(
        self,
        client: CoAPClient,
        coordinator: Coordinator,
        name: str,
        model: str,
        light: str
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._model = model
        self._description = LIGHT_TYPES[light]
        self._on = self._description.get(SWITCH_ON)
        self._off = self._description.get(SWITCH_OFF)
        self._dimmable = self._description.get(DIMMABLE)
        self._attr_device_class = self._description.get(ATTR_DEVICE_CLASS)
        self._attr_icon = self._description.get(ATTR_ICON)
        self._attr_name = f"{name} {self._description[ATTR_LABEL].replace('_', ' ').title()}"
        self._attr_entity_category = self._description.get(CONF_ENTITY_CATEGORY)

        if self._dimmable == None:
            self._dimmable = False

        if self._dimmable:
            self._attr_color_mode = COLOR_MODE_BRIGHTNESS
            self._attr_supported_color_modes = {COLOR_MODE_BRIGHTNESS}
        else:
            self._attr_color_mode = COLOR_MODE_ONOFF
            self._attr_supported_color_modes = {COLOR_MODE_ONOFF}

        try:
            device_id = self._device_status[PHILIPS_DEVICE_ID]
            self._attr_unique_id = f"{self._model}-{device_id}-{light.lower()}"
        except Exception as e:
            _LOGGER.error("Failed retrieving unique_id: %s", e)
            raise PlatformNotReady
        self._attrs: dict[str, Any] = {}
        self.kind = light


    @property
    def is_on(self) -> bool:
        if self._dimmable:
            return self._device_status.get(self.kind) > 0
        else:
            return self._device_status.get(self.kind) == self._on


    @property
    def brightness(self) -> int | None:
        if self._dimmable:
            brightness = self._device_status.get(self.kind)
            return round(255 *brightness / 100)
        else:
            return None


    async def async_turn_on(self, **kwargs) -> None:
        if self._dimmable:
            value = int(100 * kwargs[ATTR_BRIGHTNESS] / 255)
        else:
            value = self._on

        _LOGGER.debug("async_turn_on, kind: %s - value: %s", self.kind, value)
        await self._client.set_control_value(self.kind, value)


    async def async_turn_off(self, **kwargs) -> None:
        _LOGGER.debug("async_turn_off, kind: %s - value: %s", self.kind, self._off)
        await self._client.set_control_value(self.kind, self._off)


