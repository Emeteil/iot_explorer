from homeassistant.const import Platform

DOMAIN = "iot_explorer"
PLATFORMS = [Platform.SWITCH, Platform.SENSOR]

CONF_DEVICES = "devices"
CONF_DEVICE_TYPES = "device_types"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 15

DEVICE_TYPES_FILE = "device_types.json"
CONFIG_FILE = "iot_explorer_devices.json"

ATTR_SERVER = "server"
ATTR_TYPE = "type"
ATTR_NAME = "name"
ATTR_STATUS = "status"