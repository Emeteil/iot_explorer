# Configuration for IoT Explorer devices
class DeviceTypes:
    ESP8266_LED_ON_BOARD = {
        "imgs": {"светодиод": "/static/images/esp8266_led_on_board.png"},
        "status": {
            "route": "/api/led",
            "method": "GET",
            "status_in_response": "led_on",
        },
        "buttons": {
            "toggle": {
                "route": "/api/led/toggle",
                "method": "GET",
                "status_in_response": "led_on",
            }
        },
    }

    RELAY = {
        "imgs": {"реле": "/static/images/relay.png", "розетка": "/static/images/socket.png"},
        "status": {
            "route": "/api/relay",
            "method": "GET",
            "status_in_response": "relay_on",
        },
        "buttons": {
            "toggle": {
                "route": "/api/relay/toggle",
                "method": "GET",
                "status_in_response": "relay_on",
            }
        },
    }

    SERVO = {
        "imgs": {"серво": "/static/images/esp8266_led_on_board.png", "чайник": "/static/images/kettle.png"},
        "status": {
            "route": "/api/servo",
            "method": "GET",
            "status_in_response": "servo_status",
        },
        "buttons": {
            "toggle": {
                "route": "/api/servo/on",
                "method": "GET",
                "status_in_response": "servo_status",
            }
        },
    }

    @staticmethod
    def get_all_types():
        return {
            "esp8266_led_on_board": DeviceTypes.ESP8266_LED_ON_BOARD,
            "relay": DeviceTypes.RELAY,
            "servo": DeviceTypes.SERVO,
        }