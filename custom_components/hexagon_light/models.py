"""The Hexagon Light integration models."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .device import HexagonLightDevice

type HexagonLightConfigEntry = ConfigEntry[HexagonLightData]


@dataclass
class HexagonLightData:
    """Runtime data for the integration."""

    title: str
    device: HexagonLightDevice
    coordinator: DataUpdateCoordinator[None]

