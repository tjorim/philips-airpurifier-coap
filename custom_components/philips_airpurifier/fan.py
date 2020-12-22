"""Philips Air Purifier & Humidifier"""
import asyncio
import logging
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
)

from homeassistant.components.fan import (
    FanEntity,
    PLATFORM_SCHEMA,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_ICON,
    CONF_NAME,
)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
import voluptuous as vol

from .aioairctrl.coap_client import CoAPClient
from .const import (
    CONF_MODEL,
    DEFAULT_ICON,
    DEFAULT_NAME,
    MODEL_AC4236,
)
from .const import DOMAIN  # noqa: F401


_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_MODEL): vol.In(
            [
                MODEL_AC4236,
            ]
        ),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_ICON, default=DEFAULT_ICON): cv.icon,
    }
)


async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable[[List[Entity], bool], None],
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    host = config[CONF_HOST]
    model = config[CONF_MODEL]
    name = config[CONF_NAME]
    icon = config[CONF_ICON]

    model_to_class = {
        MODEL_AC4236: PhilipsAC4236,
    }

    model_class = model_to_class.get(model)
    if model_class:
        device = model_class(host=host, model=model, name=name, icon=icon)
        await device.init()
    else:
        _LOGGER.error("Unsupported model: %s", model)
        return False
    async_add_entities([device])


class PhilipsGenericFan(FanEntity):
    def __init__(self, host: str, model: str, name: str, icon: str) -> None:
        self._host = host
        self._model = model
        self._name = name
        self._icon = icon
        self._available = False
        self._state = None
        self._state_attrs = {}
        self._unique_id = None

    async def init(self) -> None:
        pass

    async def async_added_to_hass(self) -> None:
        pass

    async def async_will_remove_from_hass(self) -> None:
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

    @property
    def available(self) -> bool:
        return self._available

    @property
    def is_on(self) -> Optional[bool]:
        return self._state

    @property
    def device_state_attributes(self) -> Optional[Dict[str, Any]]:
        return self._state_attrs


class PhilipsCoAPFan(PhilipsGenericFan):
    async def init(self) -> None:
        self._client = await CoAPClient.create(self._host)
        self._observer_task = None
        try:
            _LOGGER.debug("retrieving initial status")
            status = await self._client.get_status()
            _LOGGER.debug(status)
            device_id = status["DeviceId"]
            self._unique_id = f"{self._model}-{device_id}"
        except Exception as e:
            _LOGGER.error("Failed retrieving unique_id: %s", e)
            raise PlatformNotReady

    async def async_added_to_hass(self) -> None:
        self._observer_task = asyncio.create_task(self._observe_status())

    async def _observe_status(self) -> None:
        async for status in self._client.observe_status():
            _LOGGER.debug(status)
            await self._update_status(status)

    async def _update_status(self, status: dict) -> None:
        pass

    @property
    def should_poll(self) -> bool:
        return False

    async def async_turn_on(self, speed: Optional[str] = None, **kwargs):
        await self._client.set_control_value("pwr", "1")

    async def async_turn_off(self, **kwargs) -> None:
        await self._client.set_control_value("pwr", "0")


class PhilipsAC4236(PhilipsCoAPFan):
    async def _update_status(self, status: dict) -> None:  # noqa: C901
        new_state = None
        new_state_attrs = {}
        for k, v in status.items():
            if k == "pwr" and v == "1":
                new_state = True
            elif k == "pwr" and v != "1":
                new_state = False
            elif k == "pm25":
                new_state_attrs["pm25"] = v
            elif k == "rh":
                new_state_attrs["humidity"] = v
            elif k == "rhset":
                new_state_attrs["target_humidity"] = v
            elif k == "iaql":
                new_state_attrs["allergen_index"] = v
            elif k == "temp":
                new_state_attrs["temperature"] = v
            elif k == "func":
                func_str = {
                    "P": "Purification",
                    "PH": "Purification & Humidification",
                }
                new_state_attrs["function"] = func_str.get(v, v)
            elif k == "mode":
                mode_str = {
                    "P": "Auto Mode",
                    "AG": "Auto Mode",
                    "A": "Allergen Mode",
                    "S": "Sleep Mode",
                    "M": "Manual",
                    "B": "Bacteria",
                    "N": "Night",
                    "T": "Turbo Mode",
                }
                new_state_attrs["mode"] = mode_str.get(v, v)
            elif k == "om":
                om_str = {
                    "0": "Off",
                    "1": "Speed 1",
                    "2": "Speed 2",
                    "3": "Speed 3",
                    "s": "Silent",
                    "t": "Turbo",
                }
                new_state_attrs["fan_speed"] = om_str.get(v, v)
            elif k == "aqil":
                new_state_attrs["light_brightness"] = v
            elif k == "ddp":
                ddp_str = {
                    "0": "IAI",
                    "1": "PM2.5",
                    "2": "Gas",
                    "3": "Humidity",
                }
                new_state_attrs["used_index"] = ddp_str.get(v, v)
            elif k == "wl":
                new_state_attrs["water_level"] = v
            elif k == "cl":
                new_state_attrs["child_lock"] = v
            elif k == "fltsts0":
                new_state_attrs["pre_filter"] = v
            elif k == "fltsts1":
                new_state_attrs["hepa_filter"] = v
            elif k == "fltsts2":
                new_state_attrs["carbon_filter"] = v
            elif k == "wicksts":
                new_state_attrs["wick_filter"] = v
        update_state = False
        if new_state != self._state:
            self._state = new_state
            update_state = True
        if set(new_state_attrs.items()) != set(self._state_attrs.items()):
            self._state_attrs = new_state_attrs
            update_state = True
        if update_state:
            self._available = True
            self.schedule_update_ha_state()
