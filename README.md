# Bluetti Charger 2 for Home Assistant

Local Bluetooth control of the **Bluetti Charger 2** (the alternator / solar
DC-DC charger): live readings and a **charging on/off switch**. No cloud and
no Bluetti account needed.

> **Unofficial and experimental.** Not affiliated with or endorsed by Bluetti.
> Tested on a single Charger 2 feeding an Elite 300. Use at your own risk.

## What you get

| Entity | What it shows |
|---|---|
| **Charging** (switch) | Turns charging on and off |
| Starter battery voltage | Vehicle battery, as the charger sees it |
| Alternator current / power | What is being drawn from the alternator |
| DC input voltage / current / power | The solar / DC input |
| Output voltage / current / power | What is going to the power station |

Readings refresh every 60 seconds, and again 10 and 30 seconds after you use
the switch so you see charging ramp up or down.

## Before you start

You need:

1. **Home Assistant** with [HACS](https://hacs.xyz) installed. Developed and
   tested on 2026.9; it should work on 2025.1 or newer.
2. **Bluetooth within a few metres of the charger.** Either a Bluetooth
   adapter on the Home Assistant machine, or an
   [ESPHome Bluetooth proxy](https://esphome.github.io/bluetooth-proxies/)
   (a generic ESP32 board is enough) placed near the charger.
3. **The Bluetti app closed** on any phone near the charger. The charger
   accepts one Bluetooth connection at a time, and the app holds on to it.
4. **No other Bluetti Bluetooth integration set up for this charger**
   (for example Bluetti BT). Two integrations talking to the charger at once
   scramble each other and you get nonsense readings. Remove the charger from
   the other integration first.

## Install

### With HACS (recommended)

1. In Home Assistant open **HACS**.
2. Open the three-dot menu (top right) and choose **Custom repositories**.
3. Paste `https://github.com/haaaarps/hass-bluetti-charger2`, choose type
   **Integration**, and select **Add**.
4. Find **Bluetti Charger 2 Control** in HACS and select **Download**.
5. **Restart Home Assistant.**

### By hand

Copy the `custom_components/bluetti_charger2` folder from this repository into
the `custom_components` folder of your Home Assistant configuration, then
restart Home Assistant.

## Set up

1. Close the Bluetti app.
2. Go to **Settings → Devices & services → Add integration**.
3. Search for **Bluetti Charger 2 Control**.
4. Enter the charger's Bluetooth address. If Home Assistant can already see a
   device whose name starts with `CHARGER`, the address is filled in for you.
5. Select **Submit**. A device called **Charger 2** appears with the switch
   and sensors.

To find the address yourself: **Settings → Devices & services → Bluetooth →
Configure → Advertisement monitor**, and look for the device named
`CHARGER 2…`.

## Add it to a dashboard

A simple card to get started:

```yaml
type: entities
title: Charger 2
entities:
  - entity: switch.charger_2_charging
  - entity: sensor.charger_2_starter_battery_voltage
  - entity: sensor.charger_2_alternator_power
  - entity: sensor.charger_2_dc_input_power
  - entity: sensor.charger_2_output_power
```

## Limits

- **Standard mode only.** The switch only sends values the charger has been
  observed using in standard mode. If the charger is in silent mode the
  switch refuses and asks you to use the Bluetti app.
- **Switching takes 5–10 seconds.** Each command makes a fresh encrypted
  connection, so the charger stays free for the Bluetti app the rest of the
  time.
- **No other settings yet.** Charging voltage, power limit, model preset and
  silent mode are read-only knowledge at this point; they are not exposed.
- **Depends on upstream work that is not merged yet.** Charger 2 decoding
  comes from the `ha-deployment` branch of
  [sidieje/bluetti-bt-lib](https://github.com/sidieje/bluetti-bt-lib)
  (see [bluetti-bt-lib #104](https://github.com/Patrick762/bluetti-bt-lib/pull/104)).
  Home Assistant installs it automatically. If that branch is renamed or
  removed before the work is merged, new installs will fail until this
  integration is updated.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| "Could not connect to the Charger 2" | The Bluetti app is open on a phone nearby, or the charger is out of Bluetooth range |
| Entities go unavailable for a few minutes | Same as above; the last readings are kept through three missed polls first |
| Wildly wrong readings (thousands of volts or watts) | Another Bluetti integration is also connected to the charger. Remove one of them and restart Home Assistant |
| "…in a state this switch does not handle yet" | The charger is in silent mode. Switch to standard mode in the Bluetti app |
| Integration fails to load after install | Home Assistant could not download the library. Check its internet access and restart |

## How it works

Every poll opens one encrypted Bluetooth session using
[bluetti-bt-lib](https://github.com/Patrick762/bluetti-bt-lib), reads the live
values (registers 15530–15549) and the settings block (15600–15609), then
disconnects.

Register 15600 is a 16-bit value made of 2-bit flags, where `10` means off and
`01` means on. Bits 0–1 are the charging switch and bits 2–3 are the mode
(standard / silent). The switch writes that register once, with a normal
single-register write in the same encrypted session:

| Value | Meaning |
|---|---|
| `0xAA2A` | charging off, standard mode |
| `0x5529` | charging on, standard mode |

The charger echoes the write and the readings follow within a few seconds.

## Credits

- [Patrick762](https://github.com/Patrick762) for bluetti-bt-lib and its
  encrypted Bluetooth handshake.
- [sidieje](https://github.com/sidieje) for the Charger 2 register map that
  this builds on.

## Licence

MIT. See [LICENSE](LICENSE).
