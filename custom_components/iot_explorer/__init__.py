"""The IoT Explorer integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, DISCOVERY_INTERVAL
from .device import IoTExplorerDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IoT Explorer from a config entry."""
    coordinator = IoTExplorerCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

class IoTExplorerCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the IoT Explorer devices."""

    def __init__(self, hass: HomeAssistant):
        """Initialize global IoT Explorer data updater."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DISCOVERY_INTERVAL),
        )
        self.devices: dict[str, IoTExplorerDevice] = {}

    async def _async_update_data(self):
        """Fetch data from IoT Explorer devices."""
        try:
            discovered_devices = await self.hass.async_add_executor_job(
                self._discover_devices
            )

            for _, device_info in discovered_devices.items():
                if device_info["mac"] in self.devices:
                    self.devices[device_info["mac"]].update(device_info)
                else:
                    self.devices[device_info["mac"]] = IoTExplorerDevice(
                        self.hass, device_info
                    )

            current_macs = {device_info["mac"] for device_info in discovered_devices.values()}
            for mac in list(self.devices.keys()):
                if mac not in current_macs:
                    self.devices[mac].mark_unavailable()

            return list(self.devices.values())

        except Exception as err:
            _LOGGER.error("Error updating IoT Explorer devices: %s", err)
            raise

    def _discover_devices(self) -> dict[str, dict]:
        """Discover IoT Explorer devices on the network."""
        from .device import discover_devices
        return discover_devices()