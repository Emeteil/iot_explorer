"""Constants for the IoT Explorer integration."""
from typing import Final, TypedDict

DOMAIN: Final = "iot_explorer"
DISCOVERY_INTERVAL: Final = 100 
FAST_DISCOVERY_INTERVAL: Final = 30
MAX_MISSED_UPDATES: Final = 3
REQUEST_TIMEOUT: Final = 2.5
HTTP_TIMEOUT: Final = 5

class DeviceType(TypedDict):
    """Device type definition."""
    status: dict
    buttons: dict
    imgs: dict

DEVICE_TYPES: Final[dict[str, DeviceType]] = {
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

DEFAULT_PORT: Final = 3796