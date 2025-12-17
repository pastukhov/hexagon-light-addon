# Hexagon Light (MeRGBW / TG609) — Home Assistant (HACS)

Кастомная интеграция Home Assistant для управления BLE‑светильником **Hexagon Light** (приложение **MeRGBW**, протокол TG609).

## Установка (HACS)

1. HACS → Integrations → ⋮ → Custom repositories
2. Добавьте репозиторий как **Integration**
3. Установите и перезапустите Home Assistant

## Настройка

- Settings → Devices & services → Add integration → `Hexagon Light`
- Или дождитесь обнаружения по Bluetooth (если включён Bluetooth в HA).

## Возможности

- Включение/выключение
- Яркость
- Цвет (RGB)
- Встроенные сцены/эффекты (как `effect`)

## Требования

- Home Assistant с Bluetooth (локальный адаптер или Bluetooth Proxy)
- Устройство в зоне действия

