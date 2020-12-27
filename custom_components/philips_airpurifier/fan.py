"""Philips Air Purifier & Humidifier"""
import asyncio
import logging
from datetime import timedelta
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Union,
)

from homeassistant.components.fan import (
    FanEntity,
    PLATFORM_SCHEMA,
    SPEED_OFF,
    SUPPORT_SET_SPEED,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
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
    ATTR_AIR_QUALITY_INDEX,
    ATTR_CHILD_LOCK,
    ATTR_DEVICE_ID,
    ATTR_DEVICE_VERSION,
    ATTR_DISPLAY_BACKLIGHT,
    ATTR_FILTER_ACTIVE_CARBON_REMAINING,
    ATTR_FILTER_ACTIVE_CARBON_TYPE,
    ATTR_FILTER_HEPA_REMAINING,
    ATTR_FILTER_HEPA_TYPE,
    ATTR_FILTER_PRE_REMAINING,
    ATTR_FILTER_WICK_REMAINING,
    ATTR_HUMIDITY,
    ATTR_INDOOR_ALLERGEN_INDEX,
    ATTR_LANGUAGE,
    ATTR_LIGHT_BRIGHTNESS,
    ATTR_MODEL_ID,
    ATTR_NAME,
    ATTR_PM25,
    ATTR_PREFERRED_INDEX,
    ATTR_PRODUCT_ID,
    ATTR_RUNTIME,
    ATTR_SOFTWARE_VERSION,
    ATTR_TOTAL_VOLATILE_ORGANIC_COMPOUNDS,
    ATTR_TYPE,
    ATTR_WIFI_VERSION,
    CONF_MODEL,
    DATA_KEY,
    DEFAULT_ICON,
    DEFAULT_NAME,
    DOMAIN,
    MODEL_AC1214,
    MODEL_AC2729,
    MODEL_AC2889,
    MODEL_AC3059,
    MODEL_AC3829,
    MODEL_AC3858,
    MODEL_AC4236,
    PHILIPS_AIR_QUALITY_INDEX,
    PHILIPS_CHILD_LOCK,
    PHILIPS_DEVICE_ID,
    PHILIPS_DEVICE_VERSION,
    PHILIPS_DISPLAY_BACKLIGHT,
    PHILIPS_DISPLAY_BACKLIGHT_MAP,
    PHILIPS_FILTER_ACTIVE_CARBON_REMAINING,
    PHILIPS_FILTER_ACTIVE_CARBON_TYPE,
    PHILIPS_FILTER_HEPA_REMAINING,
    PHILIPS_FILTER_HEPA_TYPE,
    PHILIPS_FILTER_PRE_REMAINING,
    PHILIPS_FILTER_WICK_REMAINING,
    PHILIPS_HUMIDITY,
    PHILIPS_INDOOR_ALLERGEN_INDEX,
    PHILIPS_LANGUAGE,
    PHILIPS_LIGHT_BRIGHTNESS,
    PHILIPS_MODE,
    PHILIPS_MODEL_ID,
    PHILIPS_NAME,
    PHILIPS_PM25,
    PHILIPS_POWER,
    PHILIPS_PREFERRED_INDEX,
    PHILIPS_PREFERRED_INDEX_MAP,
    PHILIPS_PRODUCT_ID,
    PHILIPS_RUNTIME,
    PHILIPS_SOFTWARE_VERSION,
    PHILIPS_SPEED,
    PHILIPS_TEMPERATURE,
    PHILIPS_TOTAL_VOLATILE_ORGANIC_COMPOUNDS,
    PHILIPS_TYPE,
    PHILIPS_WIFI_VERSION,
    SERVICE_SET_CHILD_LOCK_OFF,
    SERVICE_SET_CHILD_LOCK_ON,
    SERVICE_SET_DISPLAY_BACKLIGHT_OFF,
    SERVICE_SET_DISPLAY_BACKLIGHT_ON,
    SPEED_1,
    SPEED_2,
    SPEED_3,
    SPEED_ALLERGEN,
    SPEED_AUTO,
    SPEED_BACTERIA,
    SPEED_NIGHT,
    SPEED_SLEEP,
    SPEED_TURBO,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_MODEL): vol.In(
            [
                MODEL_AC1214,
                MODEL_AC2729,
                MODEL_AC2889,
                MODEL_AC3059,
                MODEL_AC3829,
                MODEL_AC3858,
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
        MODEL_AC1214: PhilipsAC1214,
        MODEL_AC2729: PhilipsAC2729,
        MODEL_AC2889: PhilipsAC2889,
        MODEL_AC3059: PhilipsAC3059,
        MODEL_AC3829: PhilipsAC3829,
        MODEL_AC3858: PhilipsAC3858,
        MODEL_AC4236: PhilipsAC4236,
    }

    model_class = model_to_class.get(model)
    if model_class:
        device = model_class(host=host, model=model, name=name, icon=icon)
        await device.init()
    else:
        _LOGGER.error("Unsupported model: %s", model)
        return False

    if DATA_KEY not in hass.data:
        hass.data[DATA_KEY] = []
    hass.data[DATA_KEY].append(device)
    async_add_entities([device])

    def wrapped_async_register(
        domain: str,
        service: str,
        service_func: Callable,
        schema: Optional[vol.Schema] = None,
    ):
        async def service_func_wrapper(service_call):
            service_data = service_call.data.copy()
            entity_id = service_data.pop("entity_id", None)
            devices = [d for d in hass.data[DATA_KEY] if d.entity_id == entity_id]
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


class PhilipsGenericFan(FanEntity):
    def __init__(self, host: str, model: str, name: str, icon: str) -> None:
        self._host = host
        self._model = model
        self._name = name
        self._icon = icon
        self._available = False
        self._state = None
        self._unique_id = None

    async def init(self) -> None:
        pass

    async def async_added_to_hass(self) -> None:
        pass

    async def async_will_remove_from_hass(self) -> None:
        pass

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

    @property
    def available(self) -> bool:
        return self._available


class PhilipsGenericCoAPFanBase(PhilipsGenericFan):
    AVAILABLE_SPEEDS = {}
    AVAILABLE_ATTRIBUTES = []

    def __init__(self, host: str, model: str, name: str, icon: str) -> None:
        super().__init__(host, model, name, icon)
        self._device_status = {}

        self._speed_list = []
        self._available_speeds = {}
        self._collect_available_speeds()

        self._available_attributes = []
        self._collect_available_attributes()

    async def init(self) -> None:
        self._client = await CoAPClient.create(self._host)
        self._observer_task = None
        try:
            status = await self._client.get_status()
            device_id = status[PHILIPS_DEVICE_ID]
            self._unique_id = f"{self._model}-{device_id}"
        except Exception as e:
            _LOGGER.error("Failed retrieving unique_id: %s", e)
            raise PlatformNotReady

    def _collect_available_speeds(self):
        speeds = {}
        for cls in reversed(self.__class__.__mro__):
            cls_speeds = getattr(cls, "AVAILABLE_SPEEDS", {})
            speeds.update(cls_speeds)
        self._available_speeds = speeds
        self._speed_list = list(self._available_speeds.keys())

    def _collect_available_attributes(self):
        attributes = []
        for cls in reversed(self.__class__.__mro__):
            cls_attributes = getattr(cls, "AVAILABLE_ATTRIBUTES", [])
            attributes.extend(cls_attributes)
        self._available_attributes = attributes

    async def async_added_to_hass(self) -> None:
        self._observer_task = asyncio.create_task(self._observe_status())

    async def async_will_remove_from_hass(self) -> None:
        self._observer_task.cancel()
        await self._observer_task
        await self._client.shutdown()

    async def _observe_status(self) -> None:
        async for status in self._client.observe_status():
            await self._update_status(status)

    async def _update_status(self, status: dict) -> None:
        self._available = True
        self._state = status.get(PHILIPS_POWER) == "1"
        self._device_status = status
        self.schedule_update_ha_state()

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def is_on(self) -> bool:
        return self._state

    async def async_turn_on(self, speed: Optional[str] = None, **kwargs):
        if speed is None:
            await self._client.set_control_value(PHILIPS_POWER, "1")
        elif speed == SPEED_OFF:
            await self.async_turn_off()
        else:
            await self.async_set_speed(speed)

    async def async_turn_off(self, **kwargs) -> None:
        await self._client.set_control_value(PHILIPS_POWER, "0")

    @property
    def supported_features(self) -> int:
        return SUPPORT_SET_SPEED

    @property
    def speed_list(self) -> list:
        return self._speed_list

    @property
    def speed(self) -> str:
        for speed, status_pattern in self._available_speeds.items():
            for k, v in status_pattern.items():
                if self._device_status.get(k) != v:
                    break
            else:
                return speed

    async def async_set_speed(self, speed: str) -> None:
        status_pattern = self._available_speeds.get(speed)
        if status_pattern:
            await self._client.set_control_values(data=status_pattern)

    @property
    def device_state_attributes(self) -> Optional[Dict[str, Any]]:
        def append(
            attributes: dict,
            key: str,
            philips_key: str,
            value_map: Union[dict, Callable[[Any], Any]] = None,
        ):
            if philips_key in self._device_status:
                value = self._device_status[philips_key]
                if isinstance(value_map, dict) and value in value_map:
                    value = value_map[value]
                elif callable(value_map):
                    value = value_map(value)
                attributes.update({key: value})

        device_attributes = dict()
        for key, philips_key, *rest in self._available_attributes:
            value_map = rest[0] if len(rest) else None
            append(device_attributes, key, philips_key, value_map)
        return device_attributes


class PhilipsGenericCoAPFan(PhilipsGenericCoAPFanBase):
    AVAILABLE_SPEEDS = {
        SPEED_OFF: {PHILIPS_POWER: "0"},
    }

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
        # device configuration
        (ATTR_LANGUAGE, PHILIPS_LANGUAGE),
        (ATTR_CHILD_LOCK, PHILIPS_CHILD_LOCK),
        (ATTR_LIGHT_BRIGHTNESS, PHILIPS_LIGHT_BRIGHTNESS),
        (ATTR_DISPLAY_BACKLIGHT, PHILIPS_DISPLAY_BACKLIGHT, PHILIPS_DISPLAY_BACKLIGHT_MAP),
        (ATTR_PREFERRED_INDEX, PHILIPS_PREFERRED_INDEX, PHILIPS_PREFERRED_INDEX_MAP),
        # filter information
        (
            ATTR_FILTER_PRE_REMAINING,
            PHILIPS_FILTER_PRE_REMAINING,
            lambda x: str(timedelta(hours=x)),
        ),
        (ATTR_FILTER_HEPA_TYPE, PHILIPS_FILTER_HEPA_TYPE),
        (
            ATTR_FILTER_HEPA_REMAINING,
            PHILIPS_FILTER_HEPA_REMAINING,
            lambda x: str(timedelta(hours=x)),
        ),
        (ATTR_FILTER_ACTIVE_CARBON_TYPE, PHILIPS_FILTER_ACTIVE_CARBON_TYPE),
        (
            ATTR_FILTER_ACTIVE_CARBON_REMAINING,
            PHILIPS_FILTER_ACTIVE_CARBON_REMAINING,
            lambda x: str(timedelta(hours=x)),
        ),
        # device sensors
        (ATTR_RUNTIME, PHILIPS_RUNTIME, lambda x: str(timedelta(seconds=round(x / 1000)))),
        (ATTR_AIR_QUALITY_INDEX, PHILIPS_AIR_QUALITY_INDEX),
        (ATTR_INDOOR_ALLERGEN_INDEX, PHILIPS_INDOOR_ALLERGEN_INDEX),
        (ATTR_PM25, PHILIPS_PM25),
    ]

    def register_services(self, async_register):
        async_register(
            domain=DOMAIN,
            service=SERVICE_SET_CHILD_LOCK_ON,
            service_func=self.async_set_child_lock_on,
        )
        async_register(
            domain=DOMAIN,
            service=SERVICE_SET_CHILD_LOCK_OFF,
            service_func=self.async_set_child_lock_off,
        )
        async_register(
            domain=DOMAIN,
            service=SERVICE_SET_DISPLAY_BACKLIGHT_ON,
            service_func=self.async_set_display_backlight_on,
        )
        async_register(
            domain=DOMAIN,
            service=SERVICE_SET_DISPLAY_BACKLIGHT_OFF,
            service_func=self.async_set_display_backlight_off,
        )

    async def async_set_child_lock_on(self):
        await self._client.set_control_value(PHILIPS_CHILD_LOCK, True)

    async def async_set_child_lock_off(self):
        await self._client.set_control_value(PHILIPS_CHILD_LOCK, False)

    async def async_set_display_backlight_on(self):
        await self._client.set_control_value(PHILIPS_DISPLAY_BACKLIGHT, "1")

    async def async_set_display_backlight_off(self):
        await self._client.set_control_value(PHILIPS_DISPLAY_BACKLIGHT, "0")


class PhilipsTVOCMixin(PhilipsGenericCoAPFanBase):
    AVAILABLE_ATTRIBUTES = [
        (ATTR_TOTAL_VOLATILE_ORGANIC_COMPOUNDS, PHILIPS_TOTAL_VOLATILE_ORGANIC_COMPOUNDS),
    ]


class PhilipsFilterWickMixin(PhilipsGenericCoAPFanBase):
    AVAILABLE_ATTRIBUTES = [
        (
            ATTR_FILTER_WICK_REMAINING,
            PHILIPS_FILTER_WICK_REMAINING,
            lambda x: str(timedelta(hours=x)),
        ),
    ]


class PhilipsHumidifierMixin(PhilipsGenericCoAPFanBase):
    AVAILABLE_ATTRIBUTES = [
        (ATTR_TEMPERATURE, PHILIPS_TEMPERATURE),
        (ATTR_HUMIDITY, PHILIPS_HUMIDITY),
    ]


# TODO consolidate these classes as soon as we see a proper pattern
class PhilipsAC1214(PhilipsGenericCoAPFan):
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        SPEED_3: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "3"},
        SPEED_ALLERGEN: {PHILIPS_POWER: "1", PHILIPS_MODE: "A"},
        SPEED_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "P"},
        SPEED_NIGHT: {PHILIPS_POWER: "1", PHILIPS_MODE: "N"},
        SPEED_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "T", PHILIPS_SPEED: "t"},
    }


class PhilipsAC2729(PhilipsHumidifierMixin, PhilipsFilterWickMixin, PhilipsGenericCoAPFan):
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        SPEED_3: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "3"},
        SPEED_ALLERGEN: {PHILIPS_POWER: "1", PHILIPS_MODE: "A"},
        SPEED_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "P"},
        SPEED_NIGHT: {PHILIPS_POWER: "1", PHILIPS_MODE: "S", PHILIPS_SPEED: "s"},
        SPEED_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "t"},
    }


class PhilipsAC2889(PhilipsHumidifierMixin, PhilipsGenericCoAPFan):
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        SPEED_3: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "3"},
        SPEED_ALLERGEN: {PHILIPS_POWER: "1", PHILIPS_MODE: "A"},
        SPEED_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "P"},
        SPEED_BACTERIA: {PHILIPS_POWER: "1", PHILIPS_MODE: "B"},
        SPEED_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "s"},
        SPEED_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "t"},
    }


class PhilipsAC3059(PhilipsTVOCMixin, PhilipsGenericCoAPFan):
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        SPEED_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "AG"},
        SPEED_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "S", PHILIPS_SPEED: "s"},
        SPEED_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "T", PHILIPS_SPEED: "t"},
    }


class PhilipsAC3829(PhilipsHumidifierMixin, PhilipsFilterWickMixin, PhilipsGenericCoAPFan):
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        SPEED_3: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "3"},
        SPEED_ALLERGEN: {PHILIPS_POWER: "1", PHILIPS_MODE: "A"},
        SPEED_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "P"},
        SPEED_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "S", PHILIPS_SPEED: "s"},
        SPEED_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "t"},
    }


class PhilipsAC3858(PhilipsTVOCMixin, PhilipsGenericCoAPFan):
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        SPEED_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "AG"},
        SPEED_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "S", PHILIPS_SPEED: "s"},
        SPEED_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "T", PHILIPS_SPEED: "t"},
    }


class PhilipsAC4236(PhilipsTVOCMixin, PhilipsGenericCoAPFan):
    AVAILABLE_SPEEDS = {
        SPEED_1: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "1"},
        SPEED_2: {PHILIPS_POWER: "1", PHILIPS_MODE: "M", PHILIPS_SPEED: "2"},
        SPEED_AUTO: {PHILIPS_POWER: "1", PHILIPS_MODE: "AG"},
        SPEED_SLEEP: {PHILIPS_POWER: "1", PHILIPS_MODE: "S", PHILIPS_SPEED: "s"},
        SPEED_TURBO: {PHILIPS_POWER: "1", PHILIPS_MODE: "T", PHILIPS_SPEED: "t"},
    }
