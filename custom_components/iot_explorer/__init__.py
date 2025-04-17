from __future__ import annotations
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS, CONF_DEVICES, CONF_DEVICE_TYPES, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DEVICE_CONFIGS
from .discovery import discover_and_register_devices

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IoT Explorer from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Load device types directly from Python configuration
    device_types = DEVICE_CONFIGS

    # Initialize devices (empty list by default)
    devices = []

    hass.data[DOMAIN][entry.entry_id] = {
        CONF_DEVICES: devices,
        CONF_DEVICE_TYPES: device_types,
        CONF_SCAN_INTERVAL: entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    }
    
    # Forward the entry setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Start the discovery process and register devices
    hass.async_create_task(discover_and_register_devices(hass, DOMAIN))
    
    await _register_services(hass)
    
    return True

async def _register_services(hass: HomeAssistant) -> None:
    """Register custom services."""
    async def discover_devices_service(call) -> None:
        """Service to manually trigger device discovery."""
        await discover_and_register_devices(hass, DOMAIN)
    
    hass.services.async_register(DOMAIN, "discover_devices", discover_devices_service)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok