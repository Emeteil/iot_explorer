"""Switch platform for IoT Explorer."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .device import IoTExplorerDevice

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up IoT Explorer switches from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    devices = coordinator.data

    entities = []
    for device in devices:
        entities.append(IoTExplorerSwitch(coordinator, device))

    async_add_entities(entities)

class IoTExplorerSwitch(SwitchEntity):
    """Representation of an IoT Explorer switch."""

    def __init__(self, coordinator, device: IoTExplorerDevice):
        """Initialize the switch."""
        self._coordinator = coordinator
        self._device = device
        self._attr_name = device.name
        self._attr_unique_id = f"{device.unique_id}_switch"
        self._attr_device_info = device.device_info
        self._attr_is_on = False

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._device.available

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        result = await self._device.async_turn_on()
        if result is not None:
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        result = await self._device.async_turn_off()
        if result is not None:
            self._attr_is_on = False
            self.async_write_ha_state()

    async def async_update(self) -> None:
        """Update the switch state."""
        status = await self._device.async_update_status()
        if status is not None:
            self._attr_is_on = status