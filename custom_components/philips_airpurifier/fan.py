"""Philips Air Purifier & Humidifier"""
import logging
import asyncio
from typing import Optional

import voluptuous as vol

from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.exceptions import PlatformNotReady
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PROTOCOL,
)
from homeassistant.components.fan import (
    FanEntity,
    PLATFORM_SCHEMA,
)
from .aioairctrl.coap_client import CoAPClient


_LOGGER = logging.getLogger(__name__)

__version__ = "0.2.0"

DOMAIN = "philips_airpurifier"
VERSION = __version__
ICON = "mdi:air-purifier"

PROTOCOL_HTTP = "http"
PROTOCOL_COAP = "coap"
PROTOCOL_COAP_PLAIN = "coap_plain"

DEFAULT_NAME = "Philips AirPurifier"
DEFAULT_PROTOCOL = PROTOCOL_HTTP

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_PROTOCOL, default=DEFAULT_PROTOCOL):
            vol.All(cv.string, vol.In([PROTOCOL_HTTP, PROTOCOL_COAP, PROTOCOL_COAP_PLAIN])),
    }
)

async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    host = config.get(CONF_HOST)
    name = config.get(CONF_NAME)
    protocol = config.get(CONF_PROTOCOL)

    _LOGGER.info("Initializing with host: %s protocol: %s", host, protocol)
    client = None
    if protocol == PROTOCOL_COAP:
        client = await CoAPClient.create(host)
    else:
        _LOGGER.error("Unsupported protocol: %s", protocol)
        return False

    unique_id = None
    try:
        status = await client.get_status()
        device_type = status["type"]
        device_id = status["DeviceId"]
        unique_id = "{}-{}".format(device_type.lower(), device_id)
    except Exception as e:
        raise PlatformNotReady

    device = PhilipsAirPurifierFan(name, client, unique_id)
    async_add_devices([device])


class PhilipsAirPurifierFan(FanEntity):
    def __init__(self, name, client, unique_id):
        self._name = name
        self._client = client
        self._observer_task = None
        self._unique_id = unique_id
        self._available = False
        self._state = None
        self._state_attrs = {}

    async def async_added_to_hass(self):
        self._observer_task = asyncio.create_task(self._observe_status())

    async def _observe_status(self):
        async for s in self._client.observe_status():
            await self._update_state(s)

    async def _update_state(self, state):
        new_state = None
        new_state_attrs = {}
        for k, v in state.items():
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

    @property
    def should_poll(self):
        return False

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def name(self):
        return self._name

    @property
    def icon(self):
        return ICON

    @property
    def available(self):
        return self._available

    @property
    def is_on(self):
        return self._state

    @property
    def device_state_attributes(self):
        return self._state_attrs

    async def async_turn_on(self, speed: Optional[str] = None, **kwargs):
        await self._client.set_control_value("pwr", "1")

    async def async_turn_off(self, **kwargs) -> None:
        await self._client.set_control_value("pwr", "0")

#  {
#      "name": "Bedroom",
#      "type": "AC4236",
#      "modelid": "AC4236/10",
#      "swversion": "Ms4106",
#      "language": "EN",
#      "DeviceVersion": "0.0.0",
#      "om": "1",
#      "pwr": "1",
#      "cl": false,
#      "aqil": 10,
#      "uil": "1",
#      "uaset": "A",
#      "mode": "AG",
#      "pm25": 3,
#      "iaql": 1,
#      "aqit": 4,
#      "tvoc": 1,
#      "ddp": "1",
#      "rddp": "1",
#      "err": 0,
#      "fltt1": "A3",
#      "fltt2": "none",
#      "fltsts0": 330,
#      "fltsts1": 4800,
#      "fltsts2": 65535,
#      "filna": "AC3036",
#      "filid": "AC30360123456789012",
#      "ota": "no",
#      "Runtime": 73417110,
#      "WifiVersion": "AWS_Philips_AIR@59",
#      "ProductId": "ffffffffffffffffffffffffffffffff",
#      "DeviceId": "62877962421511ebae870ee1d2dccf14",
#      "StatusType": "localcontrol",
#      "ConnectType": "Localcontrol"
#  }
