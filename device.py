from __future__ import annotations

import logging
import aiohttp
import async_timeout
from typing import Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.device_registry import format_mac

from .const import (
    ATTR_SERVER,
    ATTR_TYPE,
    ATTR_NAME,
    ATTR_STATUS,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

class IoTExplorerDevice:
    def __init__(self, hass, device_config: dict, device_types: dict) -> None:
        self.hass = hass
        self._config = device_config
        self._types = device_types
        self._name = device_config["name"]
        self._type = device_config["type"]
        self._server = device_config["server"]
        self._status = None
        self._available = False
        
        self._device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self._name,
            manufacturer="IoT Explorer",
            model=self._type,
        )
    
    @property
    def unique_id(self) -> str:
        return f"{self._type}_{self._name}_{self._server.replace(':', '_')}"
    
    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info
    
    @property
    def status(self) -> Any:
        return self._status
    
    @property
    def available(self) -> bool:
        return self._available
    
    async def async_update(self) -> None:
        try:
            status_config = self._types[self._type]["status"]
            url = f"http://{self._server}{status_config['route']}"
            
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        status_config["method"],
                        url
                    ) as response:
                        data = await response.json()
                        self._status = data[status_config["status_in_response"]]
                        self._available = True
        
        except Exception as ex:
            _LOGGER.warning("Error updating %s: %s", self._name, str(ex))
            self._available = False
    
    async def async_send_command(self, command: str) -> bool:
        try:
            button_config = self._types[self._type]["buttons"][command]
            url = f"http://{self._server}{button_config['route']}"
            
            async with async_timeout.timeout(10):
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        button_config["method"],
                        url
                    ) as response:
                        data = await response.json()
                        if data["status"] == "successful":
                            self._status = data[button_config["status_in_response"]]
                            return True
            
            return False
        
        except Exception as ex:
            _LOGGER.warning("Error sending command to %s: %s", self._name, str(ex))
            return False