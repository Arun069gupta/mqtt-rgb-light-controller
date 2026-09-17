# NexGlow — Blender Tubelight Remote Control

Controls a Blender Emission material's ON/OFF state from a Pygame dashboard
on any device, using MQTT as the link between them.

## Project structure

```
NexGlow/
├── pygame_dashboard.py        # dashboard UI — run on any PC/laptop
├── blender_light_control.py   # standalone script — run manually via Blender's Text Editor
├── tubelight_mqtt_addon.py    # same listener, packaged as an auto-starting Blender add-on
└── README.md
```

Use `blender_light_control.py` for testing/development, then switch to
`tubelight_mqtt_addon.py` once it's working so it starts with Blender
automatically — you don't need both running at once.

---

## 1. Prerequisites

- Blender 5.0 installed
- Python 3 installed on the machine running the dashboard
- Internet access on both machines (they talk over a public MQTT broker)

## 2. Install dependencies for the dashboard

On the machine that will run `pygame_dashboard.py`:

```bash
pip install pygame paho-mqtt
```

## 3. Install `paho-mqtt` into Blender's own Python

Blender ships its own Python — a system-wide `pip install` won't reach it.

1. Open Blender → Scripting tab → Python Console (bottom right panel)
2. Run:
   ```python
   import sys; print(sys.executable)
   ```
3. Copy that path, then in a terminal run:
   ```bash
   "<path from step 2>" -m pip install paho-mqtt
   ```
   Example (Windows): `"C:\Program Files\Blender Foundation\Blender 5.0\5.0\python\bin\python.exe" -m pip install paho-mqtt`

If pip says **"Defaulting to user installation"**, Blender's bundled Python
won't see it there even afterward. Instead run (no admin needed):
```bash
"<path from step 2>" -m pip install --target="C:\blender_pylibs" paho-mqtt
```
Both `blender_light_control.py` and `tubelight_mqtt_addon.py` already have
an `EXTRA_MODULE_PATH` variable near the top for exactly this case — set it
to the same folder you installed to (e.g. `r"C:\blender_pylibs"`).

## 4. Check the names in the script match your scene

Open your `.blend` file and confirm these match (Outliner / Shading tab):

| Variable | Should equal |
|---|---|
| `OBJECT_NAME` | Your light object's name (default: `Cylinder`) |
| `MATERIAL_NAME` | Its material's name (default: `Material.001`) |
| `EMISSION_NODE_NAME` | The Emission node's name (default: `Emission`) |

Edit the values at the top of `blender_light_control.py` (and
`tubelight_mqtt_addon.py` if you use it) if yours differ.

**Save this `.blend` file** (Ctrl+S) before continuing. If it's still
"Untitled" and Blender ever restarts, you'll land on an empty default scene
with no Cylinder — and the listener will report it can't find the object.

## 5. Test it manually first

1. In Blender, go to the **Scripting** tab
2. Open `blender_light_control.py` (Text Editor → Open)
3. Click **Run Script** (▶)
4. Check the System Console (Window → Toggle System Console) for:
   ```
   [tubelight] MQTT listener running, waiting for ON/OFF commands...
   ```
5. Switch the 3D viewport's shading mode to **Material Preview** or
   **Rendered** (4 sphere icons, top-right of the viewport) — Emission glow
   is invisible in Solid mode, so you won't see anything change otherwise.

## 6. Run the dashboard

On any device, in a terminal:

```bash
python pygame_dashboard.py
```

Click the button. Within ~0.2s, Blender's System Console should print
`[tubelight] set to ON` / `OFF`, and the object's glow should visibly
change (as long as you're in Material Preview / Rendered shading).

## 7. Install as an add-on (auto-start)

Once step 6 works, switch to `tubelight_mqtt_addon.py` so it starts
automatically with Blender instead of needing manual Run Script each
session:

1. Edit → Preferences → **Add-ons** tab
2. Click the small **▾** dropdown near the top-right of the list (or the
   top-level **Install...** button, depending on your Blender version) →
   **Install from Disk...**
3. Select `tubelight_mqtt_addon.py`
4. Search "NexGlow" in the list and enable its checkbox
5. Check the System Console for `[tubelight] add-on enabled, MQTT listener
   running`

To stop it (e.g. before editing the script), disable that checkbox —
`unregister()` disconnects MQTT and stops the timer cleanly.

## 8. Troubleshooting

| Symptom | Likely cause |
|---|---|
| `ModuleNotFoundError: paho` in Blender | Installed to the wrong Python — repeat step 3 with the exact path from `sys.executable` |
| Still `ModuleNotFoundError`, and pip said "Defaulting to user installation" | Use the `--target` install + `EXTRA_MODULE_PATH` fix in step 3 |
| Console prints `set to ON`/`OFF` but nothing visibly changes | Viewport is in Solid shading mode — switch to Material Preview or Rendered (step 5) |
| `could not find object/material/node` in console | Either the names in step 4 don't match your scene, or this `.blend` was never saved and Blender reopened to an empty default scene |
| Dashboard runs but nothing happens in Blender at all | `MQTT_TOPIC` strings don't match exactly between the dashboard and the Blender-side file |
| Nothing connects at all | Port 1883 blocked by a firewall/network — try a different network, or switch broker (see step 9) |

## 9. Before relying on this long-term

`broker.hivemq.com` is a free public test broker — anyone could publish to
your topic if they guess it. For anything beyond testing/demo use, switch
`MQTT_BROKER`/`MQTT_PORT` (and add credentials) to a private broker, e.g.
HiveMQ Cloud's free tier or Adafruit IO.
