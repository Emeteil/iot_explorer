from __future__ import annotations

import logging
import socket
import asyncio
from typing import List, Dict, Any

_LOGGER = logging.getLogger(__name__)

DISCOVERY_PORT = 3795
REQUEST_PACKET = b'IOTEXPLR_Q_V1'
RESPONSE_PACKET = b'IOTEXPLR_A_V1'
PACKET_SIZE = len(RESPONSE_PACKET)
TIMEOUT = 2.0

async def discover(hass) -> List[Dict[str, Any]]:
    devices = []
    
    broadcast_addrs = await _get_broadcast_addresses(hass)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setblocking(False)
    
    try:
        for addr in broadcast_addrs:
            try:
                sock.sendto(REQUEST_PACKET, (addr, DISCOVERY_PORT))
            except Exception as ex:
                _LOGGER.warning("Error sending to %s: %s", addr, str(ex))
        
        loop = asyncio.get_event_loop()
        responses = set()
        
        while True:
            try:
                data, addr = await loop.sock_recvfrom(sock, 1024)
                if len(data) == PACKET_SIZE and data == RESPONSE_PACKET:
                    ip = addr[0]
                    if ip not in responses:
                        responses.add(ip)
                        
                        device_info = await _get_device_info(ip)
                        if device_info:
                            devices.append(device_info)
            except (socket.timeout, BlockingIOError):
                break
            except Exception as ex:
                _LOGGER.warning("Error receiving response: %s", str(ex))
                break
    
    finally:
        sock.close()
    
    return devices

async def _get_broadcast_addresses(hass) -> List[str]:
    import ipaddress
    
    local_ip = await hass.async_add_executor_job(
        lambda: socket.gethostbyname(socket.gethostname())
    )
    
    network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
    return [str(network.broadcast_address)]

async def _get_device_info(ip: str) -> Dict[str, Any] | None:
    import aiohttp
    from aiohttp.client_exceptions import ClientError
    
    url = f"http://{ip}:3796/api/device"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                data = await response.json()
                if data["status"] == "successful":
                    return {
                        "name": data["device_name"],
                        "type": data["device_type"],
                        "server": data["server"],
                        "main_command": data["main_command"]
                    }
    except ClientError as ex:
        _LOGGER.warning("Error getting device info from %s: %s", ip, str(ex))
    
    return None