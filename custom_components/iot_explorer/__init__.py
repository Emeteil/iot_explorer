"""The IoT Explorer integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, DISCOVERY_INTERVAL, FAST_DISCOVERY_INTERVAL, MAX_MISSED_UPDATES
from .device import discover_devices, IoTExplorerDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IoT Explorer from a config entry."""
    coordinator = IoTExplorerCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def async_handle_scan(call):
        """Handle service call."""
        await coordinator.async_request_refresh()

    hass.services.async_register(DOMAIN, "scan", async_handle_scan)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

class IoTExplorerCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DISCOVERY_INTERVAL),
        )
        self._fast_mode = False
        self._missed_updates = 0

    async def _async_update_data(self):
        try:
            discovered = await self.hass.async_add_executor_job(discover_devices)
            current_macs = {d["mac"] for d in discovered.values()}
            
            for mac, device in list(self.devices.items()):
                if mac in current_macs:
                    device.update(discovered[mac])
                else:
                    self._missed_updates += 1
                    if self._missed_updates >= MAX_MISSED_UPDATES:
                        device.mark_unavailable()
            
            new_devices = False
            for ip, info in discovered.items():
                if info["mac"] not in self.devices:
                    self.devices[info["mac"]] = IoTExplorerDevice(self.hass, info)
                    new_devices = True
            
            if new_devices or self._missed_updates > 0:
                self._fast_mode = True
                self.update_interval = timedelta(seconds=FAST_DISCOVERY_INTERVAL)
            else:
                self._fast_mode = False
                self.update_interval = timedelta(seconds=DISCOVERY_INTERVAL)
                self._missed_updates = 0
            
            return list(self.devices.values())
            
        except Exception as err:
            self._missed_updates += 1
            raise UpdateFailed(f"Error updating devices: {err}")