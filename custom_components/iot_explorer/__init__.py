from __future__ import annotations

import logging
import os
import json
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import async_get_registry
from homeassistant.helpers.storage import STORAGE_DIR

from .const import (
    DOMAIN,
    PLATFORMS,
    CONF_DEVICES,
    CONF_DEVICE_TYPES,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_TYPES_FILE,
    CONFIG_FILE,
)
from .discovery import discover_and_register_devices

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up IoT Explorer from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Load device types
    device_types_path = os.path.join(hass.config.path(STORAGE_DIR), DEVICE_TYPES_FILE)
    if not os.path.exists(device_types_path):
        _LOGGER.error("Device types file not found: %s", device_types_path)
        return False
    
    try:
        with open(device_types_path, "r", encoding="utf-8") as file:
            device_types = json.load(file)
    except Exception as e:
        _LOGGER.error("Error loading device types: %s", str(e))
        return False
    
    # Load devices
    config_path = os.path.join(hass.config.path(STORAGE_DIR), CONFIG_FILE)
    if not os.path.exists(config_path):
        devices = []
    else:
        try:
            with open(config_path, "r", encoding="utf-8") as file:
                devices = json.load(file)
        except Exception as e:
            _LOGGER.error("Error loading devices config: %s", str(e))
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