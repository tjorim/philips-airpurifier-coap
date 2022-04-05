"""Constants for Philips AirPurifier integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    ATTR_STATE_CLASS,
    STATE_CLASS_MEASUREMENT,
)

from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ICON,
    ATTR_TEMPERATURE,
    TEMP_CELSIUS,
    PERCENTAGE,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_TEMPERATURE,
    CONF_ENTITY_CATEGORY,
)

from homeassistant.helpers.entity import EntityCategory


from .model import FilterDescription, SensorDescription, SwitchDescription, LightDescription

DOMAIN = "philips_airpurifier_coap"

DATA_KEY_CLIENT = "client"
DATA_KEY_COORDINATOR = "coordinator"
DATA_KEY_FAN = "fan"

DEFAULT_NAME = "Philips AirPurifier"
DEFAULT_ICON = "mdi:air-purifier"

CONF_MODEL = "model"
CONF_DEVICE_ID = "device_id"

MODEL_AC1214 = "AC1214"
MODEL_AC2729 = "AC2729"
MODEL_AC2889 = "AC2889"
MODEL_AC2939 = "AC2939"
MODEL_AC2958 = "AC2958"
MODEL_AC3033 = "AC3033"
MODEL_AC3059 = "AC3059"
MODEL_AC3829 = "AC3829"
MODEL_AC3858 = "AC3858"
MODEL_AC4236 = "AC4236"

SPEED_1 = "1"
SPEED_2 = "2"
SPEED_3 = "3"
PRESET_MODE_ALLERGEN = "allergen"
PRESET_MODE_AUTO = "auto"
PRESET_MODE_BACTERIA = "bacteria"
PRESET_MODE_GENTLE = "gentle"
PRESET_MODE_NIGHT = "night"
PRESET_MODE_SLEEP = "sleep"
PRESET_MODE_TURBO = "turbo"
SWITCH_ON = "on"
SWITCH_OFF = "off"

FUNCTION_PURIFICATION = "purification"
FUNCTION_PURIFICATION_HUMIDIFICATION = "humidification"

SERVICE_SET_CHILD_LOCK_OFF = "set_child_lock_off"
SERVICE_SET_CHILD_LOCK_ON = "set_child_lock_on"
SERVICE_SET_DISPLAY_BACKLIGHT_OFF = "set_display_backlight_off"
SERVICE_SET_DISPLAY_BACKLIGHT_ON = "set_display_backlight_on"
SERVICE_SET_FUNCTION = "set_function"
SERVICE_SET_HUMIDITY_TARGET = "set_humidity_target"
SERVICE_SET_LIGHT_BRIGHTNESS = "set_light_brightness"

ATTR_AIR_QUALITY_INDEX = "air_quality_index"
ATTR_CHILD_LOCK = "child_lock"
ATTR_DEVICE_ID = "device_id"
ATTR_DEVICE_VERSION = "device_version"
ATTR_DISPLAY_BACKLIGHT = "display_backlight"
ATTR_ERROR_CODE = "error_code"
ATTR_ERROR = "error"
ATTR_RAW = "raw"
ATTR_TOTAL = "total"
ATTR_TIME_REMAINING = "time_remaining"
ATTR_TYPE = "type"
ATTR_FILTER_PRE = "filter_pre"
ATTR_FILTER_HEPA = "filter_hepa"
ATTR_FILTER_ACTIVE_CARBON = "filter_active_carbon"
ATTR_FILTER_WICK = "wick"
ATTR_FUNCTION = "function"
ATTR_HUMIDITY = "humidity"
ATTR_HUMIDITY_TARGET = "humidity_target"
ATTR_INDOOR_ALLERGEN_INDEX = "indoor_allergen_index"
ATTR_LABEL = "label"
ATTR_UNIT = "unit"
ATTR_VALUE = "value"
ATTR_LANGUAGE = "language"
ATTR_LIGHT_BRIGHTNESS = "light_brightness"
ATTR_MODE = "mode"
ATTR_MODEL_ID = "model_id"
ATTR_NAME = "name"
ATTR_PM25 = "pm25"
ATTR_PREFERRED_INDEX = "preferred_index"
ATTR_PRODUCT_ID = "product_id"
ATTR_RUNTIME = "runtime"
ATTR_SOFTWARE_VERSION = "software_version"
ATTR_SPEED = "speed"
ATTR_TOTAL_VOLATILE_ORGANIC_COMPOUNDS = "total_volatile_organic_compounds"
ATTR_TYPE = "type"
ATTR_WATER_LEVEL = "water_level"
ATTR_WIFI_VERSION = "wifi_version"
ATTR_PREFIX = "prefix"
ATTR_POSTFIX = "postfix"

LEVEL = "Level"
INDEX = "Index"
INDOOR_ALLERGEN_INDEX = "IAI"
AIR_QUALITY_INDEX = "AQI"

PHILIPS_AIR_QUALITY_INDEX = "aqit"
PHILIPS_CHILD_LOCK = "cl"
PHILIPS_DEVICE_ID = "DeviceId"
PHILIPS_DEVICE_VERSION = "DeviceVersion"
PHILIPS_DISPLAY_BACKLIGHT = "uil"
PHILIPS_ERROR_CODE = "err"
PHILIPS_FILTER_PREFIX = "flt"
PHILIPS_FILTER_WICK_PREFIX = "wick"
PHILIPS_FILTER_STATUS = "sts"
PHILIPS_FILTER_TOTAL = "total"
PHILIPS_FILTER_TYPE = "t"
PHILIPS_FUNCTION = "func"
PHILIPS_HUMIDITY = "rh"
PHILIPS_HUMIDITY_TARGET = "rhset"
PHILIPS_INDOOR_ALLERGEN_INDEX = "iaql"
PHILIPS_LANGUAGE = "language"
PHILIPS_LIGHT_BRIGHTNESS = "aqil"
PHILIPS_MODE = "mode"
PHILIPS_MODEL_ID = "modelid"
PHILIPS_NAME = "name"
PHILIPS_PM25 = "pm25"
PHILIPS_POWER = "pwr"
PHILIPS_PREFERRED_INDEX = "ddp"
PHILIPS_PRODUCT_ID = "ProductId"
PHILIPS_RUNTIME = "Runtime"
PHILIPS_SOFTWARE_VERSION = "swversion"
PHILIPS_SPEED = "om"
PHILIPS_TEMPERATURE = "temp"
PHILIPS_TOTAL_VOLATILE_ORGANIC_COMPOUNDS = "tvoc"
PHILIPS_TYPE = "type"
PHILIPS_WATER_LEVEL = "wl"
PHILIPS_WIFI_VERSION = "WifiVersion"

PHILIPS_PREFERRED_INDEX_MAP = {
    "0": "Indoor Allergen Index",
    "1": "PM2.5",
    "2": "Gas",
}
PHILIPS_DISPLAY_BACKLIGHT_MAP = {
    "0": False,
    "1": True,
}
PHILIPS_FUNCTION_MAP = {
    "P": "Purification",
    "PH": "Purification and Humidification",
}
PHILIPS_ERROR_CODE_MAP = {
    32768: "no water",
    49153: "pre-filter must be cleaned",
    49155: "pre-filter must be cleaned",
    49408: "no water",
}

SENSOR_TYPES: dict[str, SensorDescription] = {
    # device sensors
    PHILIPS_AIR_QUALITY_INDEX: {
        ATTR_ICON: "mdi:blur",
        ATTR_LABEL: ATTR_AIR_QUALITY_INDEX,
        ATTR_UNIT: AIR_QUALITY_INDEX,
        ATTR_STATE_CLASS: STATE_CLASS_MEASUREMENT,
    },
    PHILIPS_INDOOR_ALLERGEN_INDEX: {
        ATTR_ICON: "mdi:blur",
        ATTR_LABEL: ATTR_INDOOR_ALLERGEN_INDEX,
        ATTR_UNIT: INDOOR_ALLERGEN_INDEX,
        ATTR_STATE_CLASS: STATE_CLASS_MEASUREMENT,
    },
    PHILIPS_PM25: {
        ATTR_ICON: "mdi:blur",
        ATTR_LABEL: "PM2.5",
        ATTR_UNIT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        ATTR_STATE_CLASS: STATE_CLASS_MEASUREMENT,
    },
    PHILIPS_TOTAL_VOLATILE_ORGANIC_COMPOUNDS: {
        ATTR_ICON: "mdi:blur",
        ATTR_LABEL: ATTR_TOTAL_VOLATILE_ORGANIC_COMPOUNDS,
        ATTR_UNIT: LEVEL,
        ATTR_STATE_CLASS: STATE_CLASS_MEASUREMENT,
    },
    PHILIPS_HUMIDITY: {
        ATTR_DEVICE_CLASS: DEVICE_CLASS_HUMIDITY,
        ATTR_LABEL: ATTR_HUMIDITY,
        ATTR_STATE_CLASS: STATE_CLASS_MEASUREMENT,
        ATTR_UNIT: PERCENTAGE,
    },
    PHILIPS_TEMPERATURE: {
        ATTR_DEVICE_CLASS: DEVICE_CLASS_TEMPERATURE,
        ATTR_LABEL: ATTR_TEMPERATURE,
        ATTR_STATE_CLASS: STATE_CLASS_MEASUREMENT,
        ATTR_UNIT: TEMP_CELSIUS,
    },
    # diagnostic information
    PHILIPS_WATER_LEVEL: {
        ATTR_ICON: "mdi:water",
        ATTR_LABEL: ATTR_WATER_LEVEL,
        ATTR_VALUE: lambda value, status: 0 if status.get("err") in [32768, 49408] else value,
        ATTR_STATE_CLASS: STATE_CLASS_MEASUREMENT,
        ATTR_UNIT: PERCENTAGE,
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
    },
}

FILTER_TYPES: dict[str, FilterDescription] = {
    ATTR_FILTER_PRE: {
        ATTR_PREFIX: PHILIPS_FILTER_PREFIX,
        ATTR_POSTFIX: "0",
    },
    ATTR_FILTER_HEPA: {
        ATTR_PREFIX: PHILIPS_FILTER_PREFIX,
        ATTR_POSTFIX: "1",
    },
    ATTR_FILTER_ACTIVE_CARBON: {
        ATTR_PREFIX: PHILIPS_FILTER_PREFIX,
        ATTR_POSTFIX: "2",
    },
    ATTR_FILTER_WICK: {
        ATTR_PREFIX: PHILIPS_FILTER_WICK_PREFIX,
        ATTR_POSTFIX: "",
    },
}

SWITCH_TYPES: dict[str, SwitchDescription] = {
    PHILIPS_CHILD_LOCK: {
        ATTR_ICON: "mdi:account-lock",
        ATTR_LABEL: ATTR_CHILD_LOCK,
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
        SWITCH_ON: True,
        SWITCH_OFF: False,
    },
    # Humidification function
    PHILIPS_FUNCTION: {
        ATTR_ICON: "mdi:air-humidifier",
        ATTR_LABEL: FUNCTION_PURIFICATION_HUMIDIFICATION,
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
        SWITCH_ON: "PH",
        SWITCH_OFF: "P",
    }
}

LIGHT_TYPES: dict[str, LightDescription] = {
    PHILIPS_DISPLAY_BACKLIGHT: {
        ATTR_ICON: "mdi:brightness-7",
        ATTR_LABEL: ATTR_DISPLAY_BACKLIGHT,
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
        SWITCH_ON: "1",
        SWITCH_OFF: "0",
    }
}