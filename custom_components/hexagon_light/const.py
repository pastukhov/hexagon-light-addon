"""Constants for the Hexagon Light integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "hexagon_light"

LOCAL_NAMES: tuple[str, ...] = ("Hexagon Light",)

SERVICE_UUID = "0000fff0-0000-1000-8000-00805f9b34fb"
WRITE_UUID = "0000fff3-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID = "0000fff4-0000-1000-8000-00805f9b34fb"

DEVICE_TIMEOUT = 15
STATUS_TIMEOUT = 2
UPDATE_INTERVAL = timedelta(seconds=60)

