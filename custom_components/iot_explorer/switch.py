import logging
from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN, CONF_DEVICES
from .device import IoTExplorerDevice

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the IoT Explorer switches."""
    devices = hass.data[DOMAIN][config_entry.entry_id][CONF_DEVICES]
    device_types = hass.data[DOMAIN][config_entry.entry_id][CONF_DEVICE_TYPES]
    switches = []

    for device_config in devices:
        if device_config["type"] in device_types:
            device = IoTExplorerDevice(hass, device_config, device_types)
            switches.append(IoTExplorerSwitch(device))

    async_add_entities(switches, update_before_add=True)

class IoTExplorerSwitch(SwitchEntity):
    """Representation of a switch controlled through IoT Explorer."""

    def __init__(self, device: IoTExplorerDevice) -> None:
        self._device = device

    @property
    def unique_id(self):
        return self._device.unique_id

    @property
    def name(self):
        return self._device._name

    @property
    def is_on(self):
        return self._device.status

    @property
    def available(self):
        return self._device.available

    async def async_turn_on(self, **kwargs):
        await self._device.async_send_command("toggle")

    async def async_turn_off(self, **kwargs):
        await self._device.async_send_command("toggle")

    async def async_update(self):
        await self._device.async_update()