"""The IoT Explorer integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, DISCOVERY_INTERVAL
from .device import discover_devices, IoTExplorerDevice

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IoT Explorer from a config entry."""
    coordinator = IoTExplorerCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register service
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
    """Class to manage fetching data from the IoT Explorer devices."""

    def __init__(self, hass: HomeAssistant):
        """Initialize global IoT Explorer data updater."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DISCOVERY_INTERVAL),
        )
        self.hass = hass
        self.devices: dict[str, IoTExplorerDevice] = {}

    async def _async_update_data(self):
        """Fetch data from IoT Explorer devices."""
        try:
            # Discover devices
            discovered_devices = await self.hass.async_add_executor_job(
                discover_devices
            )

            device_registry = dr.async_get(self.hass)
            new_devices = False

            # Process discovered devices
            for device_ip, device_info in discovered_devices.items():
                mac = device_info["mac"]
                
                if mac not in self.devices:
                    # New device found
                    self.devices[mac] = IoTExplorerDevice(self.hass, device_info)
                    new_devices = True
                    _LOGGER.info(f"Discovered new device: {device_info['name']} ({mac})")
                else:
                    # Update existing device
                    self.devices[mac].update(device_info)

            # Check for removed devices
            current_macs = {d["mac"] for d in discovered_devices.values()}
            for mac in list(self.devices.keys()):
                if mac not in current_macs:
                    self.devices[mac].mark_unavailable()

            # If new devices were found, reload platforms
            if new_devices:
                _LOGGER.debug("New devices found, reloading platforms")
                await self.hass.config_entries.async_reload(self.config_entry.entry_id)

            return list(self.devices.values())

        except Exception as err:
            raise UpdateFailed(f"Error updating IoT Explorer devices: {err}")