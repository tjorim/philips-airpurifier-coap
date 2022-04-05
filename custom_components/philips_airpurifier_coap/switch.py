"""Philips Air Purifier & Humidifier Switches"""
from __future__ import annotations

import logging
from typing import Any, Callable, List, cast

from aioairctrl import CoAPClient

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ICON,
    CONF_HOST,
    CONF_NAME,
    CONF_ENTITY_CATEGORY,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity, EntityCategory
from homeassistant.helpers.typing import StateType
from homeassistant.config_entries import ConfigEntry

from .philips import Coordinator, PhilipsEntity
from .const import (
    ATTR_LABEL,
    SWITCH_ON,
    SWITCH_OFF,
    CONF_MODEL,
    DATA_KEY_CLIENT,
    DATA_KEY_COORDINATOR,
    DOMAIN,
    PHILIPS_DEVICE_ID,
    SWITCH_TYPES,
)
from .model import DeviceStatus

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

    client = data[DATA_KEY_CLIENT],
    coordinator = data[DATA_KEY_COORDINATOR]
    status = coordinator.status

    switches = []
    for switch in SWITCH_TYPES:
        _LOGGER.debug("testing: %s", switch)
        if switch in status:
            _LOGGER.debug(".. found")
            switches.append(PhilipsSwitch(client, coordinator, name, model, switch))
        else:
            _LOGGER.debug(".. not found in status: %s", status)

    async_add_entities(switches, update_before_add=False)


class PhilipsSwitch(PhilipsEntity, SwitchEntity):
    """Define a Philips AirPurifier switch."""

    _attr_is_on: bool | None = False

    def __init__(
        self,
        client: CoAPClient,
        coordinator: Coordinator,
        name: str,
        model: str,
        switch: str
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._model = model
        self._description = SWITCH_TYPES[switch]
        self._on = self._description.get(SWITCH_ON)
        self._off = self._description.get(SWITCH_OFF)
        self._attr_device_class = self._description.get(ATTR_DEVICE_CLASS)
        self._attr_icon = self._description.get(ATTR_ICON)
        self._attr_name = f"{name} {self._description[ATTR_LABEL].replace('_', ' ').title()}"
        self._attr_entity_category = self._description.get(CONF_ENTITY_CATEGORY)

        try:
            device_id = self._device_status[PHILIPS_DEVICE_ID]
            self._attr_unique_id = f"{self._model}-{device_id}-{switch.lower()}"
        except Exception as e:
            _LOGGER.error("Failed retrieving unique_id: %s", e)
            raise PlatformNotReady
        self._attrs: dict[str, Any] = {}
        self.kind = switch


    @property
    def is_on(self) -> bool:
        return self._device_status.get(self.kind) == self._on


    async def async_turn_on(self) -> None:
        await self._client.set_control_value(self.kind, self._on)
        self._attr_is_on = True


    async def async_turn_on(self) -> None:
        await self._client.set_control_value(self.kind, self._on)
        self._attr_is_on = False
