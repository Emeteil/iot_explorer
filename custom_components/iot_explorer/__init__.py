from __future__ import annotations

import logging
import json
import os
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
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

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:    
    hass.data.setdefault(DOMAIN, {})
    
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
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    await _register_services(hass)
    
    return True

async def _register_services(hass: HomeAssistant) -> None:
    async def discover_devices(call) -> None:
        from .discovery import discover
        
        devices = await discover(hass)
        if devices:
            config_path = os.path.join(hass.config.path(STORAGE_DIR), CONFIG_FILE)
            with open(config_path, "w", encoding="utf-8") as file:
                json.dump(devices, file, indent=4)
            
            await hass.services.async_call("homeassistant", "reload_config_entry", {"entry_id": call.data["entry_id"]})
    
    hass.services.async_register(DOMAIN, "discover_devices", discover_devices)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok