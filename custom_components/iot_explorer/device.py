"""Representation of an IoT Explorer device."""
from __future__ import annotations

import logging
import requests
import socket
from typing import Any

from homeassistant.helpers.entity import DeviceInfo

_LOGGER = logging.getLogger(__name__)

def discover_devices() -> dict[str, dict]:
    """Discover IoT Explorer devices on the network."""
    devices = {}
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(2.5)
    
    discovery_packet = b'IOTEXPLR_Q_V1'
    sock.sendto(discovery_packet, ('255.255.255.255', 3795))
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if data == b'IOTEXPLR_A_V1':
                ip = addr[0]
                try:
                    device_info = get_device_info(ip)
                    if device_info:
                        devices[ip] = device_info
                except Exception as e:
                    _LOGGER.warning(f"Error getting device info from {ip}: {e}")
        except socket.timeout:
            break
    
    sock.close()
    return devices

def get_device_info(ip: str) -> dict[str, Any] | None:
    """Get device info from discovered IP."""
    try:
        mac = get_mac_address(ip)
        if not mac:
            return None
        
        url = f"http://{ip}:3796/api/device"
        response = requests.get(url, timeout=5)
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

def get_mac_address(ip: str) -> str | None:
    """Improved MAC address detection with multiple fallbacks"""
    import subprocess
    import netifaces
    from scapy.all import ARP, Ether, srp
    
    try:
        pid = subprocess.Popen(["arp", "-n", ip], stdout=subprocess.PIPE)
        output = pid.communicate()[0].decode()
        for line in output.split('\n'):
            if ip in line:
                parts = line.split()
                mac = parts[2] if len(parts) > 2 else None
                if mac and len(mac.split(':')) == 6:
                    return mac.lower()
    except:
        pass
    
    try:
        ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip), timeout=2, verbose=0)
        for snd, rcv in ans:
            return rcv.sprintf(r"%Ether.src%").lower()
    except:
        pass
    
    try:
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            if netifaces.AF_LINK in addrs:
                for link in addrs[netifaces.AF_LINK]:
                    if 'addr' in link:
                        return link['addr'].lower()
    except:
        pass
    
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
            identifiers={("iot_explorer", self._unique_id)},
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
    
    def update(self, device_info: dict[str, Any]):
        """Update the device info."""
        self._device_info = device_info
        self._available = True
    
    def mark_unavailable(self):
        """Mark the device as unavailable."""
        self._available = False
    
    async def async_turn_on(self):
        """Turn the device on."""
        try:
            url = f"http://{self.ip_address}:3796/api/{self._device_info['device_data']['device_api_route']}/on"
            response = await self.hass.async_add_executor_job(
                requests.get, url, {"timeout": 5}
            )
            data = response.json()
            return data.get(self._device_info['device_data']['status_in_response'], False)
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error turning on device {self.name}: {e}")
            self._available = False
            return False
    
    async def async_turn_off(self):
        """Turn the device off."""
        try:
            url = f"http://{self.ip_address}:3796/api/{self._device_info['device_data']['device_api_route']}/off"
            response = await self.hass.async_add_executor_job(
                requests.get, url, {"timeout": 5}
            )
            data = response.json()
            return data.get(self._device_info['device_data']['status_in_response'], False)
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error turning off device {self.name}: {e}")
            self._available = False
            return False
    
    async def async_update_status(self):
        """Update the status of the device."""
        try:
            url = f"http://{self.ip_address}:3796/api/{self._device_info['device_data']['device_api_route']}"
            response = await self.hass.async_add_executor_job(
                requests.get, url, {"timeout": 5}
            )
            data = response.json()
            self._available = True
            return data.get(self._device_info['device_data']['status_in_response'])
        except requests.exceptions.RequestException as e:
            _LOGGER.error(f"Error updating status for device {self.name}: {e}")
            self._available = False
            return None