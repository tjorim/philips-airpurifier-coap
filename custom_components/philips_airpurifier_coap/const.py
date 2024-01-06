"""Constants for Philips AirPurifier integration."""
from __future__ import annotations

from enum import StrEnum

from homeassistant.components.sensor import (
    ATTR_STATE_CLASS,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ICON,
    ATTR_TEMPERATURE,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    CONF_ENTITY_CATEGORY,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.helpers.entity import EntityCategory

from .model import (
    FilterDescription,
    LightDescription,
    SelectDescription,
    SensorDescription,
    SwitchDescription,
)

DOMAIN = "philips_airpurifier_coap"

DATA_KEY_CLIENT = "client"
DATA_KEY_COORDINATOR = "coordinator"
DATA_KEY_FAN = "fan"

DEFAULT_NAME = "Philips AirPurifier"


class ICON(StrEnum):
    """Custom icons provided by the integration for the interface."""

    POWER_BUTTON = "pap:power_button"
    CHILD_LOCK_BUTTON = "pap:child_lock_button"
    AUTO_MODE_BUTTON = "pap:auto_mode_button"
    FAN_SPEED_BUTTON = "pap:fan_speed_button"
    HUMIDITY_BUTTON = "pap:humidity_button"
    LIGHT_DIMMING_BUTTON = "pap:light_dimming_button"
    TWO_IN_ONE_MODE_BUTTON = "pap:two_in_one_mode_button"
    SLEEP_MODE = "pap:sleep_mode"
    AUTO_MODE = "pap:auto_mode"
    SPEED_1 = "pap:speed_1"
    SPEED_2 = "pap:speed_2"
    SPEED_3 = "pap:speed_3"
    ALLERGEN_MODE = "pap:allergen_mode"
    PURIFICATION_ONLY_MODE = "pap:purification_only_mode"
    TWO_IN_ONE_MODE = "pap:two_in_one_mode"
    BACTERIA_VIRUS_MODE = "pap:bacteria_virus_mode"
    NANOPROTECT_FILTER = "pap:nanoprotect_filter"
    FILTER_REPLACEMENT = "pap:filter_replacement"
    WATER_REFILL = "pap:water_refill"
    PREFILTER_CLEANING = "pap:prefilter_cleaning"
    PREFILTER_WICK_CLEANING = "pap:prefilter_wick_cleaning"
    PM25 = "pap:pm25"
    IAI = "pap:iai"


DATA_EXTRA_MODULE_URL = "frontend_extra_module_url"
LOADER_URL = f"/{DOMAIN}/main.js"
LOADER_PATH = f"custom_components/{DOMAIN}/main.js"
ICONS_URL = f"/{DOMAIN}/icons"
ICONLIST_URL = f"/{DOMAIN}/list"
ICONS_PATH = f"custom_components/{DOMAIN}/icons"

PAP = "pap"
ICONS = "icons"

CONF_MODEL = "model"
CONF_DEVICE_ID = "device_id"

SWITCH_ON = "on"
SWITCH_OFF = "off"
OPTIONS = "options"
DIMMABLE = "dimmable"


class FanModel(StrEnum):
    """Supported fan models."""

    AC0850 = "AC0850"
    AC1214 = "AC1214"
    AC1715 = "AC1715"
    AC2729 = "AC2729"
    AC2889 = "AC2889"
    AC2936 = "AC2936"
    AC2939 = "AC2939"
    AC2958 = "AC2958"
    AC2959 = "AC2959"
    AC3033 = "AC3033"
    AC3036 = "AC3036"
    AC3039 = "AC3039"
    AC3055 = "AC3055"
    AC3059 = "AC3059"
    AC3259 = "AC3259"
    AC3829 = "AC3829"
    AC3854_50 = "AC3854/50"
    AC3854_51 = "AC3854/51"
    AC3858_50 = "AC3858/50"
    AC3858_51 = "AC3858/51"
    AC4236 = "AC4236"
    AC4558 = "AC4558"
    AC5659 = "AC5659"


class PresetMode:
    """Available preset modes."""

    SPEED_1 = "speed 1"
    SPEED_GENTLE_1 = "gentle/speed 1"
    SPEED_2 = "speed 2"
    SPEED_3 = "speed 3"
    ALLERGEN = "allergen"
    AUTO = "auto"
    AUTO_GENERAL = "auto general"
    BACTERIA = "bacteria"
    GENTLE = "gentle"
    NIGHT = "night"
    SLEEP = "sleep"
    SLEEP_ALLERGY = "allergy sleep"
    TURBO = "turbo"
    GAS = "gas"
    POLLUTION = "pollution"

    ICON_MAP = {
        ALLERGEN: ICON.ALLERGEN_MODE,
        AUTO: ICON.AUTO_MODE,
        AUTO_GENERAL: ICON.AUTO_MODE,
        BACTERIA: ICON.BACTERIA_VIRUS_MODE,
        SPEED_GENTLE_1: ICON.SPEED_1,
        SPEED_1: ICON.SPEED_1,
        SPEED_2: ICON.SPEED_2,
        SPEED_3: ICON.SPEED_3,
        # we use the sleep mode icon for all related modes
        GENTLE: ICON.SLEEP_MODE,
        NIGHT: ICON.SLEEP_MODE,
        SLEEP: ICON.SLEEP_MODE,
        # unfortunately, the allergy sleep mode has the same icon as the auto mode on the device
        SLEEP_ALLERGY: ICON.AUTO_MODE,
        # some devices have a gas and a pollution mode, but there doesn't seem to be a Philips icon for that
        POLLUTION: ICON.AUTO_MODE,
        GAS: ICON.AUTO_MODE,
    }


class FanFunction(StrEnum):
    """The function of the fan."""

    PURIFICATION = "purification"
    PURIFICATION_HUMIDIFICATION = "purification_humidification"


class FanService(StrEnum):
    """The service of the fan."""

    CHILD_LOCK_OFF = "set_child_lock_off"
    CHILD_LOCK_ON = "set_child_lock_on"
    DISPLAY_BACKLIGHT_OFF = "set_display_backlight_off"
    DISPLAY_BACKLIGHT_ON = "set_display_backlight_on"
    FUNCTION = "set_function"
    HUMIDITY_TARGET = "set_humidity_target"
    LIGHT_BRIGHTNESS = "set_light_brightness"


class FanAttributes(StrEnum):
    """The attributes of a fan."""

    AIR_QUALITY_INDEX = "air_quality_index"
    CHILD_LOCK = "child_lock"
    DEVICE_ID = "device_id"
    DEVICE_VERSION = "device_version"
    DISPLAY_BACKLIGHT = "display_backlight"
    ERROR_CODE = "error_code"
    ERROR = "error"
    RAW = "raw"
    TOTAL = "total"
    TIME_REMAINING = "time_remaining"
    TYPE = "type"
    FILTER_PRE = "pre_filter"
    FILTER_HEPA = "hepa_filter"
    FILTER_ACTIVE_CARBON = "active_carbon_filter"
    FILTER_WICK = "wick"
    FILTER_NANOPROTECT = "nanoprotect_filter"
    FILTER_NANOPROTECT_CLEAN = "pre_filter"
    FUNCTION = "function"
    HUMIDITY = "humidity"
    HUMIDITY_TARGET = "humidity_target"
    INDOOR_ALLERGEN_INDEX = "indoor_allergen_index"
    LABEL = "label"
    UNIT = "unit"
    VALUE = "value"
    LANGUAGE = "language"
    LIGHT_BRIGHTNESS = "light_brightness"
    MODE = "mode"
    MODEL_ID = "model_id"
    NAME = "name"
    PM25 = "pm25"
    PREFERRED_INDEX = "preferred_index"
    PRODUCT_ID = "product_id"
    RUNTIME = "runtime"
    SOFTWARE_VERSION = "software_version"
    SPEED = "speed"
    TOTAL_VOLATILE_ORGANIC_COMPOUNDS = "total_volatile_organic_compounds"
    WATER_LEVEL = "water_level"
    WIFI_VERSION = "wifi_version"
    PREFIX = "prefix"
    POSTFIX = "postfix"
    WARN_VALUE = "warn_value"
    WARN_ICON = "warn_icon"


class FanUnits(StrEnum):
    """Units used by the fan attributes."""

    LEVEL = "Level"
    INDEX = "Index"
    INDOOR_ALLERGEN_INDEX = "IAI"
    AIR_QUALITY_INDEX = "AQI"


class PhilipsApi:
    """Field names in the Philips API."""

    AIR_QUALITY_INDEX = "aqit"
    CHILD_LOCK = "cl"
    DEVICE_ID = "DeviceId"
    DEVICE_VERSION = "DeviceVersion"
    DISPLAY_BACKLIGHT = "uil"
    ERROR_CODE = "err"
    FILTER_PREFIX = "flt"
    FILTER_WICK_PREFIX = "wick"
    FILTER_STATUS = "sts"
    FILTER_TOTAL = "total"
    FILTER_TYPE = "t"
    FILTER_PRE = "fltsts0"
    FILTER_PRE_TOTAL = "flttotal0"
    FILTER_PRE_TYPE = "fltt0"
    FILTER_HEPA = "fltsts1"
    FILTER_HEPA_TOTAL = "flttotal1"
    FILTER_HEPA_TYPE = "fltt1"
    FILTER_ACTIVE_CARBON = "fltsts2"
    FILTER_ACTIVE_CARBON_TOTAL = "flttotal2"
    FILTER_ACTIVE_CARBON_TYPE = "fltt2"
    FILTER_WICK = "wicksts"
    FILTER_WICK_TOTAL = "wicktotal"
    FILTER_WICK_TYPE = "wickt"
    FILTER_NANOPROTECT_PREFILTER = "D05-13"
    FILTER_NANOPROTECT_CLEAN_TOTAL = "D05-07"
    FILTER_NANOPROTECT = "D05-14"
    FILTER_NANOPROTECT_TOTAL = "D05-08"
    FILTER_NANOPROTECT_TYPE = "D05-02"
    FUNCTION = "func"
    HUMIDITY = "rh"
    HUMIDITY_TARGET = "rhset"
    INDOOR_ALLERGEN_INDEX = "iaql"
    LANGUAGE = "language"
    LIGHT_BRIGHTNESS = "aqil"
    MODE = "mode"
    MODEL_ID = "modelid"
    NAME = "name"
    PM25 = "pm25"
    POWER = "pwr"
    PREFERRED_INDEX = "ddp"
    PRODUCT_ID = "ProductId"
    RUNTIME = "Runtime"
    SOFTWARE_VERSION = "swversion"
    SPEED = "om"
    TEMPERATURE = "temp"
    TOTAL_VOLATILE_ORGANIC_COMPOUNDS = "tvoc"
    TYPE = "type"
    WATER_LEVEL = "wl"
    WIFI_VERSION = "WifiVersion"

    POWER_MAP = {
        SWITCH_ON: "1",
        SWITCH_OFF: "0",
    }
    # the AC1715 seems to follow a new scheme, this should later be refactored
    NEW_NAME = "D01-03"
    NEW_MODEL_ID = "D01-05"
    NEW_LANGUAGE = "D01-07"
    NEW_POWER = "D03-02"
    NEW_DISPLAY_BACKLIGHT = "D03-05"
    NEW_MODE = "D03-12"
    NEW_INDOOR_ALLERGEN_INDEX = "D03-32"
    NEW_PM25 = "D03-33"
    NEW_PREFERRED_INDEX = "D03-42"

    PREFERRED_INDEX_MAP = {
        "0": "Indoor Allergen Index",
        "1": "PM2.5",
        "2": "Gas",
    }
    NEW_PREFERRED_INDEX_MAP = {
        "IAI": "Indoor Allergen Index",
        "PM2.5": "PM2.5",
    }
    DISPLAY_BACKLIGHT_MAP = {
        "0": False,
        "1": True,
    }
    FUNCTION_MAP = {
        "P": ("Purification", ICON.PURIFICATION_ONLY_MODE),
        "PH": ("Purification and Humidification", ICON.TWO_IN_ONE_MODE),
    }
    HUMIDITY_TARGET_MAP = {
        40: ("40%", ICON.HUMIDITY_BUTTON),
        50: ("50%", ICON.HUMIDITY_BUTTON),
        60: ("60%", ICON.HUMIDITY_BUTTON),
        70: ("max", ICON.HUMIDITY_BUTTON),
    }
    ERROR_CODE_MAP = {
        32768: "no water",
        49153: "pre-filter must be cleaned",
        49155: "pre-filter must be cleaned",
        49408: "no water",
    }


SENSOR_TYPES: dict[str, SensorDescription] = {
    # device sensors
    PhilipsApi.AIR_QUALITY_INDEX: {
        ATTR_ICON: "mdi:blur",
        FanAttributes.LABEL: FanAttributes.AIR_QUALITY_INDEX,
        FanAttributes.UNIT: FanUnits.AIR_QUALITY_INDEX,
        ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
    },
    PhilipsApi.INDOOR_ALLERGEN_INDEX: {
        ATTR_ICON: ICON.IAI,
        FanAttributes.LABEL: FanAttributes.INDOOR_ALLERGEN_INDEX,
        FanAttributes.UNIT: FanUnits.INDOOR_ALLERGEN_INDEX,
        ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
    },
    PhilipsApi.NEW_INDOOR_ALLERGEN_INDEX: {
        ATTR_ICON: ICON.IAI,
        FanAttributes.LABEL: FanAttributes.INDOOR_ALLERGEN_INDEX,
        FanAttributes.UNIT: FanUnits.INDOOR_ALLERGEN_INDEX,
        ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
    },
    PhilipsApi.PM25: {
        ATTR_ICON: ICON.PM25,
        FanAttributes.LABEL: "PM2.5",
        FanAttributes.UNIT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
    },
    PhilipsApi.NEW_PM25: {
        ATTR_ICON: ICON.PM25,
        FanAttributes.LABEL: "PM2.5",
        FanAttributes.UNIT: CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
    },
    PhilipsApi.TOTAL_VOLATILE_ORGANIC_COMPOUNDS: {
        ATTR_ICON: "mdi:blur",
        FanAttributes.LABEL: FanAttributes.TOTAL_VOLATILE_ORGANIC_COMPOUNDS,
        FanAttributes.UNIT: FanUnits.LEVEL,
        ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
    },
    PhilipsApi.HUMIDITY: {
        ATTR_DEVICE_CLASS: SensorDeviceClass.HUMIDITY,
        FanAttributes.LABEL: FanAttributes.HUMIDITY,
        ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
        FanAttributes.UNIT: PERCENTAGE,
    },
    PhilipsApi.TEMPERATURE: {
        ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        FanAttributes.LABEL: ATTR_TEMPERATURE,
        ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
        FanAttributes.UNIT: UnitOfTemperature.CELSIUS,
    },
    # diagnostic information
    PhilipsApi.WATER_LEVEL: {
        ATTR_ICON: "mdi:water",
        FanAttributes.LABEL: FanAttributes.WATER_LEVEL,
        FanAttributes.VALUE: lambda value, status: 0
        if status.get("err") in [32768, 49408]
        else value,
        ATTR_STATE_CLASS: SensorStateClass.MEASUREMENT,
        FanAttributes.UNIT: PERCENTAGE,
        CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
        FanAttributes.WARN_VALUE: 10,
        FanAttributes.WARN_ICON: ICON.WATER_REFILL,
    },
}

FILTER_TYPES: dict[str, FilterDescription] = {
    PhilipsApi.FILTER_PRE: {
        ATTR_ICON: "mdi:dots-grid",
        FanAttributes.WARN_ICON: ICON.FILTER_REPLACEMENT,
        FanAttributes.WARN_VALUE: 72,
        FanAttributes.LABEL: FanAttributes.FILTER_PRE,
        FanAttributes.TOTAL: PhilipsApi.FILTER_PRE_TOTAL,
        FanAttributes.TYPE: PhilipsApi.FILTER_PRE_TYPE,
    },
    PhilipsApi.FILTER_HEPA: {
        ATTR_ICON: "mdi:dots-grid",
        FanAttributes.WARN_ICON: ICON.FILTER_REPLACEMENT,
        FanAttributes.WARN_VALUE: 72,
        FanAttributes.LABEL: FanAttributes.FILTER_HEPA,
        FanAttributes.TOTAL: PhilipsApi.FILTER_HEPA_TOTAL,
        FanAttributes.TYPE: PhilipsApi.FILTER_HEPA_TYPE,
    },
    PhilipsApi.FILTER_ACTIVE_CARBON: {
        ATTR_ICON: "mdi:dots-grid",
        FanAttributes.WARN_ICON: ICON.FILTER_REPLACEMENT,
        FanAttributes.WARN_VALUE: 72,
        FanAttributes.LABEL: FanAttributes.FILTER_ACTIVE_CARBON,
        FanAttributes.TOTAL: PhilipsApi.FILTER_ACTIVE_CARBON_TOTAL,
        FanAttributes.TYPE: PhilipsApi.FILTER_ACTIVE_CARBON_TYPE,
    },
    PhilipsApi.FILTER_WICK: {
        ATTR_ICON: "mdi:dots-grid",
        FanAttributes.WARN_ICON: ICON.PREFILTER_WICK_CLEANING,
        FanAttributes.WARN_VALUE: 72,
        FanAttributes.LABEL: FanAttributes.FILTER_WICK,
        FanAttributes.TOTAL: PhilipsApi.FILTER_WICK_TOTAL,
        FanAttributes.TYPE: PhilipsApi.FILTER_WICK_TYPE,
    },
    PhilipsApi.FILTER_NANOPROTECT: {
        ATTR_ICON: ICON.NANOPROTECT_FILTER,
        FanAttributes.WARN_ICON: ICON.FILTER_REPLACEMENT,
        FanAttributes.WARN_VALUE: 10,
        FanAttributes.LABEL: FanAttributes.FILTER_NANOPROTECT,
        FanAttributes.TOTAL: PhilipsApi.FILTER_NANOPROTECT_TOTAL,
        FanAttributes.TYPE: PhilipsApi.FILTER_NANOPROTECT_TYPE,
    },
    PhilipsApi.FILTER_NANOPROTECT_PREFILTER: {
        ATTR_ICON: ICON.NANOPROTECT_FILTER,
        FanAttributes.WARN_ICON: ICON.PREFILTER_CLEANING,
        FanAttributes.WARN_VALUE: 10,
        FanAttributes.LABEL: FanAttributes.FILTER_NANOPROTECT_CLEAN,
        FanAttributes.TOTAL: PhilipsApi.FILTER_NANOPROTECT_CLEAN_TOTAL,
        FanAttributes.TYPE: "",
    },
}

SWITCH_TYPES: dict[str, SwitchDescription] = {
    PhilipsApi.CHILD_LOCK: {
        ATTR_ICON: ICON.CHILD_LOCK_BUTTON,
        FanAttributes.LABEL: FanAttributes.CHILD_LOCK,
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
        SWITCH_ON: True,
        SWITCH_OFF: False,
    },
}

LIGHT_TYPES: dict[str, LightDescription] = {
    PhilipsApi.DISPLAY_BACKLIGHT: {
        ATTR_ICON: ICON.LIGHT_DIMMING_BUTTON,
        FanAttributes.LABEL: FanAttributes.DISPLAY_BACKLIGHT,
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
        SWITCH_ON: "1",
        SWITCH_OFF: "0",
    },
    PhilipsApi.LIGHT_BRIGHTNESS: {
        ATTR_ICON: "mdi:circle-outline",
        FanAttributes.LABEL: FanAttributes.LIGHT_BRIGHTNESS,
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
        SWITCH_ON: 100,
        SWITCH_OFF: 0,
        DIMMABLE: True,
    },
    PhilipsApi.NEW_DISPLAY_BACKLIGHT: {
        ATTR_ICON: ICON.LIGHT_DIMMING_BUTTON,
        FanAttributes.LABEL: FanAttributes.DISPLAY_BACKLIGHT,
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
        SWITCH_ON: 100,
        SWITCH_OFF: 0,
    },
}

SELECT_TYPES: dict[str, SelectDescription] = {
    PhilipsApi.FUNCTION: {
        FanAttributes.LABEL: FanAttributes.FUNCTION,
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
        OPTIONS: PhilipsApi.FUNCTION_MAP,
    },
    PhilipsApi.HUMIDITY_TARGET: {
        FanAttributes.LABEL: FanAttributes.HUMIDITY_TARGET,
        CONF_ENTITY_CATEGORY: EntityCategory.CONFIG,
        OPTIONS: PhilipsApi.HUMIDITY_TARGET_MAP,
    },
}
