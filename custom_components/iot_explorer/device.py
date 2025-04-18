"""Representation of an IoT Explorer device."""
from __future__ import annotations

import logging
import requests
import socket
from typing import Any

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    DEVICE_TYPES,
    DEFAULT_PORT,
    REQUEST_TIMEOUT,
    HTTP_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)

def discover_devices() -> dict[str, dict]:
    """Discover IoT Explorer devices on the network."""
    devices = {}
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(REQUEST_TIMEOUT)
    
    broadcast_addresses = _get_broadcast_addresses()
    discovery_packet = b'IOTEXPLR_Q_V1'
    
    for addr in broadcast_addresses:
        try:
            sock.sendto(discovery_packet, (addr, 3795))
        except socket.error:
            continue
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if data == b'IOTEXPLR_A_V1':
                ip = addr[0]
                try:
                    device_info = _get_device_info(ip)
                    if device_info:
                        devices[ip] = device_info
                except Exception as e:
                    _LOGGER.warning(f"Error getting device info from {ip}: {e}")
        except socket.timeout:
            break
    
    sock.close()
    return devices

def _get_broadcast_addresses() -> list[str]:
    """Get all broadcast addresses on all interfaces."""
    import netifaces
    broadcast_addrs = []
    
    for interface in netifaces.interfaces():
        try:
            addrs = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addrs:
                for addr_info in addrs[netifaces.AF_INET]:
                    if 'broadcast' in addr_info:
                        broadcast_addrs.append(addr_info['broadcast'])
        except (ValueError, OSError):
            continue
    
    return broadcast_addrs

def _get_device_info(ip: str) -> dict[str, Any] | None:
    """Get device info from a discovered IP."""
    try:
        mac = _get_mac_address(ip)
        if not mac:
            return None
        
        url = f"http://{ip}:{DEFAULT_PORT}/api/device"
        response = requests.get(url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        if data["status"] != "successful":
            return None
        
        return {
            "ip": ip,
            "mac": mac,
            "name": data["device_name"],
            "type": data["device_type"],
            "server": data["server"],
            "main_command": data["main_command"],
            "model": data["device_type"],
            "manufacturer": "IoT Explorer",
            "sw_version": "1.0",
            "available": True,
            "device_data": data
        }
    except requests.exceptions.RequestException as e:
        _LOGGER.warning(f"Error getting device info from {ip}: {e}")
        return None

def _get_mac_address(ip: str) -> str | None:
    """Get MAC address from IP using ARP. 
    If not found in ARP cache, sends an ARP request (using arping or ping)."""
    import subprocess
    import re

    def _parse_mac_from_arp_output(output: str, ip: str) -> str | None:
        """Helper to parse MAC from arp command output."""
        for line in output.split('\n'):
            if ip in line:
                parts = re.split(r'\s+', line.strip())
                if len(parts) >= 3:
                    mac = parts[2]
                    if re.match(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$', mac):
                        return mac.lower()
        return None

    try:
        arp_output = subprocess.run(["arp", "-n", ip], 
                                   capture_output=True, 
                                   text=True).stdout
        mac = _parse_mac_from_arp_output(arp_output, ip)
        if mac:
            return mac

        try:
            subprocess.run(["arping", "-c", "1", ip], 
                          capture_output=True, 
                          timeout=2)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            subprocess.run(["ping", "-c", "1", ip], 
                          capture_output=True, 
                          timeout=2)

        arp_output = subprocess.run(["arp", "-n", ip], 
                                   capture_output=True, 
                                   text=True).stdout
        return _parse_mac_from_arp_output(arp_output, ip)

    except Exception:
        return None

class IoTExplorerDevice:
    """Representation of an IoT Explorer device."""
    
    def __init__(self, hass, device_info: dict[str, Any]):
        """Initialize the device."""
        self.hass = hass
        self._device_info = device_info
        self._available = True
        self._unique_id = device_info["mac"]
        
    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._unique_id)},
            name=self._device_info["name"],
            manufacturer=self._device_info["manufacturer"],
            model=self._device_info["model"],
            sw_version=self._device_info["sw_version"],
        )
    
    @property
    def available(self) -> bool:
        """Return True if device is available."""
        return self._available
    
    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id
    
    @property
    def name(self) -> str:
        """Return the name of the device."""
        return self._device_info["name"]
    
    @property
    def device_type(self) -> str:
        """Return the device type."""
        return self._device_info["type"]
    
    @property
    def ip_address(self) -> str:
        """Return the IP address of the device."""
        return self._device_info["ip"]
    
    def to_dict(self):
        """Convert device to dict for storage."""
        return {
            "ip": self._device_info["ip"],
            "mac": self._unique_id,
            "name": self._device_info["name"],
            "type": self._device_info["type"],
            "available": self._available
        }
    
    def update(self, device_info: dict[str, Any]):
        """Update the device info."""
        self._device_info = device_info
        self._available = True
    
    def mark_unavailable(self):
        """Mark the device as unavailable."""
        self._available = False
        self._device_info["ip"] = None
    
    async def async_turn_on(self):
        """Turn the device on."""
        device_type = DEVICE_TYPES.get(self.device_type)
        if not device_type:
            _LOGGER.error(f"Unknown device type: {self.device_type}")
            return False
        
        try:
            url = f"http://{self.ip_address}:{DEFAULT_PORT}{device_type['buttons']['toggle']['route']}"
            response = await self.hass.async_add_executor_job(
                requests.get, url, {"timeout": HTTP_TIMEOUT}
            )
            data = response.json()
            return data.get(device_type['buttons']['toggle']['status_in_response'], False)
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error turning on device {self.name}: {e}")
            self._available = False
            return False
    
    async def async_turn_off(self):
        """Turn the device off."""
        return await self.async_turn_on()
    
    async def async_update_status(self):
        """Update the status of the device."""
        device_type = DEVICE_TYPES.get(self.device_type)
        if not device_type:
            _LOGGER.error(f"Unknown device type: {self.device_type}")
            return None
        
        try:
            url = f"http://{self.ip_address}:{DEFAULT_PORT}{device_type['status']['route']}"
            response = await self.hass.async_add_executor_job(
                requests.get, url, {"timeout": HTTP_TIMEOUT}
            )
            data = response.json()
            self._available = True
            return data.get(device_type['status']['status_in_response'])
        except requests.exceptions.RequestException as e:
            self._available = False
            return None