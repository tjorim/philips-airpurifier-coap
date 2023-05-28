"""Philips Air Purifier & Humidifier Sensors"""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any, Callable, List, cast

from homeassistant.components.sensor import ATTR_STATE_CLASS, SensorEntity
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ICON,
    CONF_HOST,
    CONF_NAME,
    CONF_ENTITY_CATEGORY,
    PERCENTAGE,
    TIME_HOURS,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity, EntityCategory
from homeassistant.helpers.typing import StateType
from homeassistant.config_entries import ConfigEntry

from .philips import Coordinator, PhilipsEntity
from .const import (
    ATTR_LABEL,
    ATTR_TIME_REMAINING,
    ATTR_TOTAL,
    ATTR_TYPE,
    ATTR_UNIT,
    ATTR_VALUE,
    ATTR_WARN_ICON,
    ATTR_WARN_VALUE,
    CONF_MODEL,
    DATA_KEY_COORDINATOR,
    DOMAIN,
    FILTER_TYPES,
    PHILIPS_DEVICE_ID,
    SENSOR_TYPES,
)
from .model import DeviceStatus

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: Callable[[List[Entity], bool], None]
) -> None:
    _LOGGER.debug("async_setup_entry called for platform sensor")

    host = entry.data[CONF_HOST]
    model = entry.data[CONF_MODEL]
    name = entry.data[CONF_NAME]

    data = hass.data[DOMAIN][host]

    coordinator = data[DATA_KEY_COORDINATOR]
    status = coordinator.status

    sensors = []
    
    for sensor in SENSOR_TYPES:
        if sensor in status:
            sensors.append(PhilipsSensor(coordinator, name, model, sensor))

    for filter in FILTER_TYPES:
        if filter in status:
            sensors.append(PhilipsFilterSensor(coordinator, name, model, filter))

    async_add_entities(sensors, update_before_add=False)


class PhilipsSensor(PhilipsEntity, SensorEntity):
    """Define a Philips AirPurifier sensor."""

    def __init__(self, coordinator: Coordinator, name: str, model: str, kind: str) -> None:
        super().__init__(coordinator)
        self._model = model
        self._description = SENSOR_TYPES[kind]
        self._warn_icon = self._description.get(ATTR_WARN_ICON)
        self._warn_value = self._description.get(ATTR_WARN_VALUE)
        self._norm_icon = self._description.get(ATTR_ICON)
        self._attr_state_class = self._description.get(ATTR_STATE_CLASS)
        self._attr_device_class = self._description.get(ATTR_DEVICE_CLASS)
        self._attr_entity_category = self._description.get(CONF_ENTITY_CATEGORY)
        self._attr_name = f"{name} {self._description[ATTR_LABEL].replace('_', ' ').title()}"
        self._attr_native_unit_of_measurement = self._description.get(ATTR_UNIT)

        try:
            device_id = self._device_status[PHILIPS_DEVICE_ID]
            self._attr_unique_id = f"{self._model}-{device_id}-{kind.lower()}"
        except Exception as e:
            _LOGGER.error("Failed retrieving unique_id: %s", e)
            raise PlatformNotReady
        self._attrs: dict[str, Any] = {}
        self.kind = kind

    @property
    def native_value(self) -> StateType:
        value = self._device_status[self.kind]
        convert = self._description.get(ATTR_VALUE)
        if convert:
            value = convert(value, self._device_status)
        return cast(StateType, value)

    @property
    def icon(self) -> str:
        if self._warn_value and self._warn_value >= int(self.native_value):
            return self._warn_icon
        else:
            return self._norm_icon


class PhilipsFilterSensor(PhilipsEntity, SensorEntity):
    """Define a Philips AirPurifier filter sensor."""

    def __init__(self, coordinator: Coordinator, name: str, model: str, kind: str) -> None:
        super().__init__(coordinator)
        self._model = model
        self._description = FILTER_TYPES[kind]
        self._warn_icon = self._description[ATTR_WARN_ICON]
        self._warn_value = self._description[ATTR_WARN_VALUE]
        self._norm_icon = self._description[ATTR_ICON]
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_name = f"{name} {self._description[ATTR_LABEL].replace('_', ' ').title()}"

        self._value_key = kind
        self._total_key = self._description[ATTR_TOTAL]
        self._type_key = self._description[ATTR_TYPE]

        if self._has_total:
            self._attr_native_unit_of_measurement = PERCENTAGE
        else:
            self._attr_native_unit_of_measurement = TIME_HOURS

        try:
            device_id = self._device_status[PHILIPS_DEVICE_ID]
            self._attr_unique_id = f"{self._model}-{device_id}-{self._description[ATTR_LABEL]}"
        except Exception as e:
            _LOGGER.error("Failed retrieving unique_id: %s", e)
            raise PlatformNotReady
        self._attrs: dict[str, Any] = {}

    @property
    def native_value(self) -> StateType:
        if self._has_total:
            return self._percentage
        else:
            return self._time_remaining

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        if self._type_key in self._device_status:
            self._attrs[ATTR_TYPE] = self._device_status[self._type_key]
        # self._attrs[ATTR_RAW] = self._value
        if self._has_total:
            self._attrs[ATTR_TOTAL] = self._total
            self._attrs[ATTR_TIME_REMAINING] = self._time_remaining
        return self._attrs

    @property
    def _has_total(self) -> bool:
        return self._total_key in self._device_status

    @property
    def _percentage(self) -> float:
        return round(100.0 * self._value / self._total)

    @property
    def _time_remaining(self) -> str:
        return str(round(timedelta(hours=self._value) / timedelta(hours=1)))

    @property
    def _value(self) -> int:
        return self._device_status[self._value_key]

    @property
    def _total(self) -> int:
        return self._device_status[self._total_key]

    @property
    def icon(self) -> str:
        if self._warn_value and self._warn_value >= int(self.native_value):
            return self._warn_icon
        else:
            return self._norm_icon