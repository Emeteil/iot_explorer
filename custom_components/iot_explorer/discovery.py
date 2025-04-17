from __future__ import annotations

import logging
import socket
import asyncio
from typing import List, Dict, Any

from homeassistant.helpers import device_registry as dr

_LOGGER = logging.getLogger(__name__)

DISCOVERY_PORT = 3795
REQUEST_PACKET = b'IOTEXPLR_Q_V1'
RESPONSE_PACKET = b'IOTEXPLR_A_V1'
PACKET_SIZE = len(RESPONSE_PACKET)
TIMEOUT = 2.0

async def discover_and_register_devices(hass, domain: str) -> None:
    """Discover devices on the network and register them in Home Assistant."""
    devices = await discover(hass)
    if not devices:
        _LOGGER.info("No devices discovered.")
        return

    device_registry = dr.async_get(hass)

    for device in devices:
        mac = device.get("mac")
        if not mac:
            _LOGGER.warning("Device %s is missing MAC address, skipping.", device)
            continue

        # Check if the device is already registered
        existing_device = device_registry.async_get_device(
            identifiers={(domain, mac)},
            connections={(dr.CONNECTION_NETWORK_MAC, mac)},
        )

        if existing_device:
            # Update IP if changed
            if existing_device.configuration_url != f"http://{device['server']}":
                _LOGGER.info("Updating IP for device %s", mac)
                device_registry.async_update_device(
                    existing_device.id,
                    configuration_url=f"http://{device['server']}",
                )
        else:
            # Register new device
            _LOGGER.info("Registering new device: %s", mac)
            device_registry.async_get_or_create(
                config_entry_id=None,  # ConfigEntry ID can be provided if needed
                identifiers={(domain, mac)},
                connections={(dr.CONNECTION_NETWORK_MAC, mac)},
                name=device.get("name"),
                manufacturer="IoT Explorer",
                model=device.get("type"),
                configuration_url=f"http://{device['server']}",
            )

async def discover(hass) -> List[Dict[str, Any]]:
    """Discover devices on the network."""
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
    """Get broadcast addresses for the local network."""
    import ipaddress

    local_ip = await hass.async_add_executor_job(
        lambda: socket.gethostbyname(socket.gethostname())
    )

    network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
    return [str(network.broadcast_address)]

async def _get_device_info(ip: str) -> Dict[str, Any] | None:
    """Get detailed information for a device."""
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
                        "mac": data.get("mac", None),  # Ensure MAC address is provided
                        "main_command": data["main_command"],
                    }
    except ClientError as ex:
        _LOGGER.warning("Error getting device info from %s: %s", ip, str(ex))

    return None