from homeassistant.const import Platform

DOMAIN = "iot_explorer"
PLATFORMS = [Platform.SWITCH, Platform.SENSOR]

CONF_DEVICES = "devices"
CONF_DEVICE_TYPES = "device_types"
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 15

DEVICE_CONFIGS = {
    "esp8266_led_on_board": {
        "imgs": {
            "светодиод": "/static/images/esp8266_led_on_board.png"
        },
        "status": {
            "route": "/api/led",
            "method": "GET",
            "status_in_response": "led_on"
        },
        "buttons": {
            "toggle": {
                "route": "/api/led/toggle",
                "method": "GET",
                "status_in_response": "led_on"
            }
        }
    },
    "relay": {
        "imgs": {
            "реле": "/static/images/relay.png",
            "розетка": "/static/images/socket.png"
        },
        "status": {
            "route": "/api/relay",
            "method": "GET",
            "status_in_response": "relay_on"
        },
        "buttons": {
            "toggle": {
                "route": "/api/relay/toggle",
                "method": "GET",
                "status_in_response": "relay_on"
            }
        }
    },
    "servo": {
        "imgs": {
            "серво": "/static/images/esp8266_led_on_board.png",
            "чайник": "/static/images/kettle.png"
        },
        "status": {
            "route": "/api/servo",
            "method": "GET",
            "status_in_response": "servo_status"
        },
        "buttons": {
            "toggle": {
                "route": "/api/servo/on",
                "method": "GET",
                "status_in_response": "servo_status"
            }
        }
    }
}