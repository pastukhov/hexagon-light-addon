"""BLE protocol implementation for Hexagon Light (MeRGBW/TG609)."""

from __future__ import annotations

import asyncio
import colorsys
from collections.abc import Callable
from contextlib import suppress
import logging

from bleak import BleakClient
from bleak.backends.device import BLEDevice

from homeassistant.core import CALLBACK_TYPE

from .const import DEVICE_TIMEOUT, NOTIFY_UUID, SERVICE_UUID, STATUS_TIMEOUT, WRITE_UUID

_LOGGER = logging.getLogger(__name__)


class HexagonLightError(RuntimeError):
    """Raised for protocol/connection errors."""


SCENES_TG609: dict[str, int] = {
    "symphony": 2,
    "energy": 3,
    "jump": 4,
    "vitality": 7,
    "accumulation": 16,
    "chase": 23,
    "space-time": 45,
    "space_time": 45,
    "ephemeral": 35,
    "flow": 55,
    "forest": 13,
    "neon_lights": 48,
    "neon-lights": 48,
    "green_jade": 71,
    "green-jade": 71,
    "running": 91,
    "pink_light": 109,
    "pink-light": 109,
    "alarm": 113,
    "aurora": 59,
    "rainbow": 26,
    "melody": 32,
}


def _clamp_int(value: int, lo: int, hi: int) -> int:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def _checksum_ff(sum_without_checksum: int) -> int:
    return (0xFF - (sum_without_checksum & 0xFF)) & 0xFF


def _build_command(cmd: int, payload: bytes | None) -> bytes:
    if payload is None:
        payload = b""
    cmd = cmd & 0xFF
    seq = 0xFF
    length = 5 + len(payload)
    if length > 0xFF:
        raise ValueError(f"Command too long: {length} bytes")
    frame = bytearray(length)
    frame[0] = 0x55
    frame[1] = cmd
    frame[2] = seq
    frame[3] = length & 0xFF
    frame[4 : 4 + len(payload)] = payload
    frame[-1] = _checksum_ff(sum(frame[:-1]))
    return bytes(frame)


def _u16_be(value: int) -> bytes:
    value = value & 0xFFFF
    return bytes([(value >> 8) & 0xFF, value & 0xFF])


def _rgb_to_hue_sat_payload(r: int, g: int, b: int) -> bytes:
    r = _clamp_int(r, 0, 255)
    g = _clamp_int(g, 0, 255)
    b = _clamp_int(b, 0, 255)
    h, s, _v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    hue_deg = int(h * 360.0) % 360
    sat_1000 = _clamp_int(int(s * 1000.0), 0, 1000)
    return _u16_be(hue_deg) + _u16_be(sat_1000)


class HexagonLightDevice:
    """Async controller for Hexagon Light."""

    def __init__(self, ble_device: BLEDevice) -> None:
        self.address = ble_device.address
        self.name = ble_device.name or self.address
        self._ble_device = ble_device

        self._client: BleakClient | None = None
        self._write_response: bool | None = None

        self._callbacks: set[Callable[[], None]] = set()
        self._notify_event = asyncio.Event()
        self._last_notify: bytes | None = None

        self.is_on: bool | None = None
        self.brightness_percent: int | None = None
        self.rgb: tuple[int, int, int] | None = None
        self.effect: str | None = None

    def set_ble_device_and_advertisement_data(self, ble_device: BLEDevice, _adv: object) -> None:
        """Update the BLEDevice reference from bluetooth callbacks."""
        self._ble_device = ble_device

    def register_callback(self, callback: Callable[[], None]) -> CALLBACK_TYPE:
        """Register a callback to be called when state updates."""
        self._callbacks.add(callback)

        def _remove() -> None:
            self._callbacks.discard(callback)

        return _remove

    def _call_callbacks(self) -> None:
        for cb in list(self._callbacks):
            with suppress(Exception):
                cb()

    def _on_disconnect(self, _client: BleakClient) -> None:
        self._client = None
        self._write_response = None
        self._notify_event.clear()

    def _handle_notify(self, _sender: int, data: bytearray) -> None:
        raw = bytes(data)
        self._last_notify = raw
        self._notify_event.set()
        self._parse_state(raw)
        self._call_callbacks()

    async def async_stop(self) -> None:
        """Disconnect the device."""
        client = self._client
        self._client = None
        self._write_response = None
        if client is not None:
            with suppress(Exception):
                await client.disconnect()

    async def _ensure_connected(self) -> BleakClient:
        client = self._client
        if client is not None and client.is_connected:
            return client

        client = BleakClient(
            self._ble_device,
            timeout=float(DEVICE_TIMEOUT),
            disconnected_callback=self._on_disconnect,
        )
        await client.connect()

        with suppress(Exception):
            await client.start_notify(NOTIFY_UUID, self._handle_notify)

        with suppress(Exception):
            svcs = await client.get_services()
            svc = svcs.get_service(SERVICE_UUID) if svcs else None
            ch = svc.get_characteristic(WRITE_UUID) if svc else None
            props = set(ch.properties or []) if ch else set()
            self._write_response = "write-without-response" not in props

        self._client = client
        return client

    async def _write_frame(self, frame: bytes) -> None:
        client = await self._ensure_connected()

        response = self._write_response
        if response is None:
            response = False

        try:
            await client.write_gatt_char(WRITE_UUID, frame, response=response)
        except Exception:
            if response is False:
                await client.write_gatt_char(WRITE_UUID, frame, response=True)
                self._write_response = True
            else:
                raise

    def _parse_state(self, raw: bytes | None) -> None:
        if not raw or len(raw) < 6:
            return
        if (sum(raw) & 0xFF) != 0xFF:
            return

        brightness_percent: int | None = None

        if raw[0] == 0x55:
            length = raw[3]
            if length != len(raw):
                return
            is_on = raw[4] != 0
            if len(raw) >= 7:
                b = int(raw[5]) - 5
                if 0 <= b <= 100:
                    brightness_percent = b
            self.is_on = is_on
            self.brightness_percent = brightness_percent
            return

        if raw[0] != 0x56:
            return

        is_on = raw[4] != 0
        if len(raw) >= 8:
            value = (raw[5] << 8) | raw[6]
            b = (value // 10) - 5
            if 0 <= b <= 100:
                brightness_percent = b
        self.is_on = is_on
        self.brightness_percent = brightness_percent

    async def async_update(self) -> None:
        """Request a sync/status frame and update best-effort state."""
        self._notify_event.clear()
        await self._ensure_connected()
        await self._write_frame(_build_command(0x00, None))
        try:
            await asyncio.wait_for(self._notify_event.wait(), timeout=float(STATUS_TIMEOUT))
        except TimeoutError:
            _LOGGER.debug("%s: no status notification received", self.address)

    async def async_turn_on(self) -> None:
        await self._write_frame(_build_command(0x01, bytes([0x01])))
        self.is_on = True
        self._call_callbacks()

    async def async_turn_off(self) -> None:
        await self._write_frame(_build_command(0x01, bytes([0x00])))
        self.is_on = False
        self._call_callbacks()

    async def async_set_brightness_percent(self, percent: int) -> None:
        percent = _clamp_int(int(percent), 0, 100)
        value = (percent + 5) * 10
        await self._write_frame(_build_command(0x05, _u16_be(value)))
        self.brightness_percent = percent
        self._call_callbacks()

    async def async_set_rgb(self, r: int, g: int, b: int) -> None:
        r_i = _clamp_int(int(r), 0, 255)
        g_i = _clamp_int(int(g), 0, 255)
        b_i = _clamp_int(int(b), 0, 255)
        await self._write_frame(_build_command(0x03, _rgb_to_hue_sat_payload(r_i, g_i, b_i)))
        self.rgb = (r_i, g_i, b_i)
        self.effect = None
        self._call_callbacks()

    async def async_set_scene(self, scene: int, *, speed: int | None = None) -> None:
        scene = _clamp_int(int(scene), 0, 0xFFFF)
        await self._write_frame(_build_command(0x06, _u16_be(scene)))
        if speed is not None:
            speed_b = _clamp_int(int(speed), 0, 255) & 0xFF
            await self._write_frame(_build_command(0x0F, bytes([speed_b])))
        self.effect = None
        self._call_callbacks()

    async def async_set_scene_by_name(self, name: str, *, speed: int | None = None) -> None:
        key = name.strip().lower().replace(" ", "_")
        scene = SCENES_TG609.get(key)
        if scene is None:
            key2 = key.replace("_", "-")
            scene = SCENES_TG609.get(key2)
        if scene is None:
            raise HexagonLightError(f"Unknown scene name: {name!r}")
        await self.async_set_scene(scene, speed=speed)
        self.effect = key
