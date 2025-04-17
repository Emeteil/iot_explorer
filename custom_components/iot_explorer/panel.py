from flask import Flask, render_template, jsonify, request
from homeassistant.helpers import device_registry as dr
from .discovery import discover_and_register_devices


def create_panel(hass, domain):
    """Create a Flask-based panel for IoT Explorer."""
    app = Flask(__name__)

    @app.route("/")
    def index():
        """Render the main UI."""
        devices = _get_registered_devices(hass, domain)
        return render_template("index.html", devices=devices)

    @app.route("/discover", methods=["POST"])
    def discover():
        """Trigger device discovery."""
        hass.async_create_task(discover_and_register_devices(hass, domain))
        return jsonify({"status": "Discovery started"})

    @app.route("/send_command", methods=["POST"])
    def send_command():
        """Send a command to a specific device."""
        data = request.get_json()
        device_id = data.get("device_id")
        command = data.get("command")

        if not device_id or not command:
            return jsonify({"error": "Invalid input"}), 400

        # Logic to send command to the device
        # Example: hass.services.call(...)
        return jsonify({"status": f"Command {command} sent to {device_id}"})

    return app


def _get_registered_devices(hass, domain):
    """Retrieve devices registered in the Home Assistant device registry."""
    device_registry = dr.async_get(hass)
    devices = []

    for device in device_registry.devices.values():
        if domain in device.identifiers:
            devices.append({
                "id": device.id,
                "name": device.name,
                "manufacturer": device.manufacturer,
                "model": device.model,
                "configuration_url": device.configuration_url,
            })

    return devices