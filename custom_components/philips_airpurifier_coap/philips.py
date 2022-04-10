from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Union

import logging
import asyncio
from asyncio.tasks import Task
from datetime import timedelta

from aioairctrl import CoAPClient
import voluptuous as vol

from homeassistant.core import CALLBACK_TYPE, callback
from homeassistant.helpers.entity import Entity
from homeassistant.exceptions import ConfigEntryNotReady, PlatformNotReady

from homeassistant.util.percentage import (
    ordered_list_item_to_percentage,
    percentage_to_ordered_list_item,
)

from homeassistant.components.fan import (
    SUPPORT_PRESET_MODE,
    SUPPORT_SET_SPEED,
    FanEntity,
)

from .const import *

_LOGGER = logging.getLogger(__name__)

class Coordinator:
    def __init__(self, client: CoAPClient) -> None:
        self.client = client

        # It's None before the first successful update.
        # Components should call async_first_refresh to make sure the first
        # update was successful. Set type to just DeviceStatus to remove
        # annoying checks that status is not None when it was already checked
        # during setup.
        self.status: DeviceStatus = None  # type: ignore[assignment]

        self._listeners: list[CALLBACK_TYPE] = []
        self._task: Task | None = None

    async def async_first_refresh(self) -> None:
        try:
            self.status = await self.client.get_status()
        except Exception as ex:
            raise ConfigEntryNotReady from ex

    @callback
    def async_add_listener(self, update_callback: CALLBACK_TYPE) -> Callable[[], None]:
        """Listen for data updates."""
        start_observing = not self._listeners

        self._listeners.append(update_callback)

        if start_observing:
            self._start_observing()

        @callback
        def remove_listener() -> None:
            """Remove update listener."""
            self.async_remove_listener(update_callback)

        return remove_listener

    @callback
    def async_remove_listener(self, update_callback) -> None:
        """Remove data update."""
        self._listeners.remove(update_callback)

        if not self._listeners and self._task:
            self._task.cancel()
            self._task = None

    async def _async_observe_status(self) -> None:
        async for status in self.client.observe_status():
            _LOGGER.debug("Status update: %s", status)
            self.status = status
            for update_callback in self._listeners:
                update_callback()

    def _start_observing(self) -> None:
        """Schedule state observation."""
        if self._task:
            self._task.cancel()
            self._task = None
        self._task = asyncio.create_task(self._async_observe_status())


class PhilipsEntity(Entity):
    def __init__(self, coordinator: Coordinator) -> None:
        super().__init__()
        _LOGGER.debug("PhilipsEntity __init__ called")
        _LOGGER.debug(f"coordinator.status is: {coordinator.status}")
        self.coordinator = coordinator
        self._serialNumber = coordinator.status["DeviceId"]
        self._name = coordinator.status["name"]
        self._modelName = coordinator.status["modelid"]
        self._firmware = coordinator.status["WifiVersion"]
        self._manufacturer = "Philips"

    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def device_info(self):
        return {
            "identifiers": {
                (DOMAIN, self._serialNumber)
            },
            "name": self._name,
            "model": self._modelName,
            "manufacturer": self._manufacturer,
            "sw_version": self._firmware,
        }

    @property
    def available(self):
        return self.coordinator.status is not None

    @property
    def _device_status(self) -> dict[str, Any]:
        return self.coordinator.status

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(self.coordinator.async_add_listener(self._handle_coordinator_update))

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class PhilipsGenericFan(PhilipsEntity, FanEntity):
    def __init__(
        self,
        coordinator: Coordinator,
        model: str,
        name: str,
    ) -> None:
        super().__init__(coordinator)
        self._model = model
        self._name = name
        self._unique_id = None

    def _register_services(self, async_register) -> None:
        for cls in reversed(self.__class__.__mro__):
            register_method = getattr(cls, "register_services", None)
            if callable(register_method):
                register_method(self, async_register)

    def register_services(self, async_register) -> None:
        pass

    @property
    def unique_id(self) -> Optional[str]:
        return self._unique_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def icon(self) -> str:
        return self._icon


class PhilipsGenericCoAPFanBase(PhilipsGenericFan):
    AVAILABLE_PRESET_MODES = {}
    AVAILABLE_SPEEDS = {}
    AVAILABLE_ATTRIBUTES = []
    AVAILABLE_SWITCHES = []
    AVAILABLE_LIGHTS = []

    def __init__(
        self,
        client: CoAPClient,
        coordinator: Coordinator,
        model: str,
        name: str,
    ) -> None:
        super().__init__(coordinator, model, name)
        self._client = client

        self._preset_modes = []
        self._available_preset_modes = {}
        self._collect_available_preset_modes()

        self._speeds = []
        self._available_speeds = {}
        self._collect_available_speeds()

        self._available_attributes = []
        self._collect_available_attributes()

        try:
            device_id = self._device_status[PHILIPS_DEVICE_ID]
            self._unique_id = f"{self._model}-{device_id}"
        except Exception as e:
            _LOGGER.error("Failed retrieving unique_id: %s", e)
            raise PlatformNotReady

    def _collect_available_preset_modes(self):
        preset_modes = {}
        for cls in reversed(self.__class__.__mro__):
            cls_preset_modes = getattr(cls, "AVAILABLE_PRESET_MODES", {})
            preset_modes.update(cls_preset_modes)
        self._available_preset_modes = preset_modes
        self._preset_modes = list(self._available_preset_modes.keys())

    def _collect_available_speeds(self):
        speeds = {}
        for cls in reversed(self.__class__.__mro__):
            cls_speeds = getattr(cls, "AVAILABLE_SPEEDS", {})
            speeds.update(cls_speeds)
        self._available_speeds = speeds
        self._speeds = list(self._available_speeds.keys())

    def _collect_available_attributes(self):
        attributes = []
        for cls in reversed(self.__class__.__mro__):
            cls_attributes = getattr(cls, "AVAILABLE_ATTRIBUTES", [])
            attributes.extend(cls_attributes)
        self._available_attributes = attributes

    @property
    def is_on(self) -> bool:
        return self._device_status.get(PHILIPS_POWER) == "1"

    async def async_turn_on(
        self,
        speed: Optional[str] = None,
        percentage: Optional[int] = None,
        preset_mode: Optional[str] = None,
        **kwargs,
    ):
        if preset_mode:
            await self.async_set_preset_mode(preset_mode)
            return
        if percentage:
            await self.async_set_percentage(percentage)
            return
        await self._client.set_control_value(PHILIPS_POWER, "1")

    async def async_turn_off(self, **kwargs) -> None:
        await self._client.set_control_value(PHILIPS_POWER, "0")

    @property
    def supported_features(self) -> int:
        features = SUPPORT_PRESET_MODE
        if self._speeds:
            features |= SUPPORT_SET_SPEED
        return features

    @property
    def preset_modes(self) -> Optional[List[str]]:
        return self._preset_modes

    @property
    def preset_mode(self) -> Optional[str]:
        for preset_mode, status_pattern in self._available_preset_modes.items():
            for k, v in status_pattern.items():
                if self._device_status.get(k) != v:
                    break
            else:
                return preset_mode

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        status_pattern = self._available_preset_modes.get(preset_mode)
        if status_pattern:
            await self._client.set_control_values(data=status_pattern)

    @property
    def speed_count(self) -> int:
        return len(self._speeds)

    @property
    def percentage(self) -> Optional[int]:
        for speed, status_pattern in self._available_speeds.items():
            for k, v in status_pattern.items():
                if self._device_status.get(k) != v:
                    break
            else:
                return ordered_list_item_to_percentage(self._speeds, speed)

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage == 0:
            await self.async_turn_off()
        else:
            speed = percentage_to_ordered_list_item(self._speeds, percentage)
            status_pattern = self._available_speeds.get(speed)
            if status_pattern:
                await self._client.set_control_values(data=status_pattern)

    @property
    def extra_state_attributes(self) -> Optional[Dict[str, Any]]:
        def append(
            attributes: dict,
            key: str,
            philips_key: str,
            value_map: Union[dict, Callable[[Any, Any], Any]] = None,
        ):
            if philips_key in self._device_status:
                value = self._device_status[philips_key]
                if isinstance(value_map, dict) and value in value_map:
                    value = value_map.get(value, "unknown")
                elif callable(value_map):
                    value = value_map(value, self._device_status)
                attributes.update({key: value})

        device_attributes = dict()
        for key, philips_key, *rest in self._available_attributes:
            value_map = rest[0] if len(rest) else None
            append(device_attributes, key, philips_key, value_map)
        return device_attributes

    @property
    def icon(self) -> str:
        if not self.is_on:
            return ICON.POWER_BUTTON

        preset_mode = self.preset_mode
        if preset_mode == None:
            return ICON.FAN_SPEED_BUTTON
        if preset_mode in PRESET_MODE_ICON_MAP:
            return PRESET_MODE_ICON_MAP[preset_mode]
        
        return ICON.FAN_SPEED_BUTTON
        


class PhilipsGenericCoAPFan(PhilipsGenericCoAPFanBase):
    AVAILABLE_PRESET_MODES = {}
    AVAILABLE_SPEEDS = {}

    AVAILABLE_ATTRIBUTES = [
        # device information
        (ATTR_NAME, PHILIPS_NAME),
        (ATTR_TYPE, PHILIPS_TYPE),
        (ATTR_MODEL_ID, PHILIPS_MODEL_ID),
        (ATTR_PRODUCT_ID, PHILIPS_PRODUCT_ID),
        (ATTR_DEVICE_ID, PHILIPS_DEVICE_ID),
        (ATTR_DEVICE_VERSION, PHILIPS_DEVICE_VERSION),
        (ATTR_SOFTWARE_VERSION, PHILIPS_SOFTWARE_VERSION),
        (ATTR_WIFI_VERSION, PHILIPS_WIFI_VERSION),
        (ATTR_ERROR_CODE, PHILIPS_ERROR_CODE),
        (ATTR_ERROR, PHILIPS_ERROR_CODE, PHILIPS_ERROR_CODE_MAP),
        # device configuration
        (ATTR_LANGUAGE, PHILIPS_LANGUAGE),
        (ATTR_PREFERRED_INDEX, PHILIPS_PREFERRED_INDEX, PHILIPS_PREFERRED_INDEX_MAP),
        # device sensors
        (ATTR_RUNTIME, PHILIPS_RUNTIME, lambda x, _: str(timedelta(seconds=round(x / 1000)))),
    ]

    AVAILABLE_LIGHTS = [PHILIPS_DISPLAY_BACKLIGHT, PHILIPS_LIGHT_BRIGHTNESS]

    AVAILABLE_SWITCHES = []
    AVAILABLE_SELECTS = []


class PhilipsHumidifierMixin(PhilipsGenericCoAPFanBase):
    AVAILABLE_SELECTS = [PHILIPS_FUNCTION, PHILIPS_HUMIDITY_TARGET]


# TODO consolidate these classes as soon as we see a proper pattern
class PhilipsAC1214(PhilipsGenericCoAPFan):
    AVAILABLE_PRESET_MODES = {
        PRESET_MODE_ALLERGEN: {PHILIPS_POWER: "1", PHILIPS_MODE: "A"},
        PRESET_MODE_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "P"},
        PRESET_MODE_NIGHT: {PHILIPS_POWER: "1", PHILIPS_MODE: "N"},
    }
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        SPEED_3: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "3"},
        PRESET_MODE_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "T", PHILIPS_SPEED: "t"},
    }


class PhilipsAC2729(
    PhilipsHumidifierMixin,
    PhilipsGenericCoAPFan,
):
    AVAILABLE_PRESET_MODES = {
        PRESET_MODE_ALLERGEN: {PHILIPS_POWER: "1", PHILIPS_MODE: "A"},
        PRESET_MODE_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "P"},
        PRESET_MODE_NIGHT: {PHILIPS_POWER: "1", PHILIPS_MODE: "S", PHILIPS_SPEED: "s"},
    }
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        SPEED_3: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "3"},
        PRESET_MODE_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "t"},
    }
    AVAILABLE_SWITCHES = [PHILIPS_CHILD_LOCK]


class PhilipsAC2889(PhilipsGenericCoAPFan):
    AVAILABLE_PRESET_MODES = {
        PRESET_MODE_ALLERGEN: {PHILIPS_POWER: "1", PHILIPS_MODE: "A"},
        PRESET_MODE_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "P"},
        PRESET_MODE_BACTERIA: {PHILIPS_POWER: "1", PHILIPS_MODE: "B"},
        PRESET_MODE_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "s"},
    }
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        SPEED_3: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "3"},
        PRESET_MODE_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "t"},
    }


class PhilipsAC2936(PhilipsGenericCoAPFan):
    AVAILABLE_PRESET_MODES = {
        PRESET_MODE_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "AG"},
        PRESET_MODE_GENTLE: {PHILIPS_POWER: "1", PHILIPS_MODE: "GT"},
        PRESET_MODE_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "S"},
        PRESET_MODE_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "T"},
    }


class PhilipsAC2939(PhilipsGenericCoAPFan):
    AVAILABLE_PRESET_MODES = {
        PRESET_MODE_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "AG"},
        PRESET_MODE_GENTLE: {PHILIPS_POWER: "1", PHILIPS_MODE: "GT"},
        PRESET_MODE_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "S"},
        PRESET_MODE_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "T"},
    }


class PhilipsAC2958(PhilipsGenericCoAPFan):
    AVAILABLE_PRESET_MODES = {
        PRESET_MODE_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "AG"},
        PRESET_MODE_GENTLE: {PHILIPS_POWER: "1", PHILIPS_MODE: "GT"},
        PRESET_MODE_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "S"},
        PRESET_MODE_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "T"},
    }


class PhilipsAC30xx(PhilipsGenericCoAPFan):
    AVAILABLE_PRESET_MODES = {
        PRESET_MODE_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "AG"},
        PRESET_MODE_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "S", PHILIPS_SPEED: "s"},
    }
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        PRESET_MODE_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "T", PHILIPS_SPEED: "t"},
    }


class PhilipsAC3033(PhilipsAC30xx):
    pass

class PhilipsAC3036(PhilipsAC30xx):
    pass

class PhilipsAC3039(PhilipsAC30xx):
    pass

class PhilipsAC3059(PhilipsAC30xx):
    pass


class PhilipsAC3259(PhilipsGenericCoAPFan):
    AVAILABLE_PRESET_MODES = {
        PRESET_MODE_ALLERGEN: {PHILIPS_POWER: "1", PHILIPS_MODE: "A"},
        PRESET_MODE_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "P"},
        PRESET_MODE_BACTERIA: {PHILIPS_POWER: "1", PHILIPS_MODE: "B"},
        PRESET_MODE_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "s"},
    }
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        SPEED_3: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "3"},
        PRESET_MODE_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "t"},
    }


class PhilipsAC3829(PhilipsHumidifierMixin, PhilipsGenericCoAPFan):
    AVAILABLE_PRESET_MODES = {
        PRESET_MODE_ALLERGEN: {PHILIPS_POWER: "1", PHILIPS_MODE: "A"},
        PRESET_MODE_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "P"},
        PRESET_MODE_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "S", PHILIPS_SPEED: "s"},
    }
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        SPEED_3: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "3"},
        PRESET_MODE_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "t"},
    }
    AVAILABLE_SWITCHES = [PHILIPS_CHILD_LOCK]



class PhilipsAC3858(PhilipsGenericCoAPFan):
    AVAILABLE_PRESET_MODES = {
        PRESET_MODE_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "AG"},
        PRESET_MODE_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "S", PHILIPS_SPEED: "s"},
    }
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        PRESET_MODE_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "T", PHILIPS_SPEED: "t"},
    }


class PhilipsAC4236(PhilipsGenericCoAPFan):
    AVAILABLE_PRESET_MODES = {
        PRESET_MODE_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "AG"},
        PRESET_MODE_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "S", PHILIPS_SPEED: "s"},
    }
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        PRESET_MODE_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "T", PHILIPS_SPEED: "t"},
    }


class PhilipsAC5659(PhilipsGenericCoAPFan):
    AVAILABLE_PRESET_MODES = {
        PRESET_MODE_ALLERGEN: {PHILIPS_POWER: "1", PHILIPS_MODE: "A"},
        PRESET_MODE_BACTERIA: {PHILIPS_POWER: "1", PHILIPS_MODE: "B"},
        PRESET_MODE_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "P"},
        PRESET_MODE_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "s"},
    }
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        SPEED_3: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "3"},
        PRESET_MODE_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "t"},
    }


model_to_class = {
    MODEL_AC1214: PhilipsAC1214,
    MODEL_AC2729: PhilipsAC2729,
    MODEL_AC2889: PhilipsAC2889,
    MODEL_AC2936: PhilipsAC2936,
    MODEL_AC2939: PhilipsAC2939,
    MODEL_AC2958: PhilipsAC2958,
    MODEL_AC3033: PhilipsAC3033,
    MODEL_AC3036: PhilipsAC3036,
    MODEL_AC3039: PhilipsAC3039,
    MODEL_AC3059: PhilipsAC3059,
    MODEL_AC3259: PhilipsAC3259,
    MODEL_AC3829: PhilipsAC3829,
    MODEL_AC3858: PhilipsAC3858,
    MODEL_AC4236: PhilipsAC4236,
    MODEL_AC5659: PhilipsAC5659,
}
