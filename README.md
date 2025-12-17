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

## Troubleshooting / Отладка

Если светильник работает, но в Home Assistant иногда отображается неправильный статус, включите debug‑логи интеграции и проверьте входящие notify‑кадры.

1. Включите логирование в `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.hexagon_light: debug
```

2. Перезапустите Home Assistant и посмотрите логи.

Ожидаемое поведение:
- Статус устройства берётся только из notify‑кадров с `cmd=0x00` (в логах это строки вида `HEXAGON_NOTIFY ... data=5600ff...`).
- Другие notify‑кадры (например `...data=5601...`, `...data=560e...`) — это ответы на команды и они не должны менять state в HA.
