"""Light platform for Hexagon Light integration."""

from __future__ import annotations

from typing import Any, cast

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityFeature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .device import SCENES_TG609, HexagonLightDevice
from .models import HexagonLightConfigEntry


async def async_setup_entry(
    hass: HomeAssistant,
    entry: HexagonLightConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the light platform for Hexagon Light."""
    data = entry.runtime_data
    async_add_entities([HexagonLightEntity(data.coordinator, data.device, entry.title)])


class HexagonLightEntity(CoordinatorEntity[DataUpdateCoordinator[None]], LightEntity):
    """Representation of a Hexagon Light device."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_color_modes = {ColorMode.RGB}
    _attr_color_mode = ColorMode.RGB
    _attr_supported_features = LightEntityFeature.EFFECT

    def __init__(
        self, coordinator: DataUpdateCoordinator[None], device: HexagonLightDevice, name: str
    ) -> None:
        super().__init__(coordinator)
        self._device = device
        self._attr_unique_id = device.address
        self._attr_device_info = DeviceInfo(
            name=name,
            manufacturer="MeRGBW",
            model="TG609",
            connections={(dr.CONNECTION_BLUETOOTH, device.address)},
        )
        self._attr_effect_list = sorted(set(SCENES_TG609.keys()))
        self._async_update_attrs()

    @callback
    def _async_update_attrs(self) -> None:
        device = self._device
        if device.is_on is None:
            self._attr_is_on = bool(self._attr_brightness)
        else:
            self._attr_is_on = device.is_on
        if device.brightness_percent is not None:
            self._attr_brightness = round(device.brightness_percent / 100 * 255)
        if device.rgb is not None:
            self._attr_rgb_color = device.rgb
        self._attr_effect = (
            device.effect if device.effect in (self._attr_effect_list or []) else None
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        brightness = cast(int, kwargs.get(ATTR_BRIGHTNESS, self.brightness or 255))
        brightness_pct = round(brightness / 255 * 100)

        if effect := kwargs.get(ATTR_EFFECT):
            await self._device.async_turn_on()
            await self._device.async_set_scene_by_name(effect)
            await self._device.async_set_brightness_percent(brightness_pct)
            return

        if ATTR_RGB_COLOR in kwargs:
            rgb = kwargs[ATTR_RGB_COLOR]
            await self._device.async_turn_on()
            await self._device.async_set_rgb(rgb[0], rgb[1], rgb[2])
            await self._device.async_set_brightness_percent(brightness_pct)
            return

        if ATTR_BRIGHTNESS in kwargs:
            await self._device.async_turn_on()
            await self._device.async_set_brightness_percent(brightness_pct)
            return

        await self._device.async_turn_on()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._device.async_turn_off()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._async_update_attrs()
        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(self._device.register_callback(self._handle_device_update))
        return await super().async_added_to_hass()

    @callback
    def _handle_device_update(self) -> None:
        self._async_update_attrs()
        self.async_write_ha_state()
