"""
NexGlow — Blender-side MQTT listener for the tubelight.
------------------------------------------------
Run this INSIDE Blender: Scripting tab -> open this file -> Run Script.
It stays alive (via a timer) for as long as Blender is open, listening
for ON/OFF messages and updating the Emission node's Strength live.

One-time setup: install paho-mqtt into Blender's OWN Python (not your
system Python), e.g.:
    Windows: "C:\\Program Files\\Blender Foundation\\Blender 5.0\\5.0\\python\\bin\\python.exe" -m pip install paho-mqtt
    Linux:   /path/to/blender/5.0/python/bin/python3.11 -m pip install paho-mqtt
    macOS:   /Applications/Blender.app/Contents/Resources/5.0/python/bin/python3.11 -m pip install paho-mqtt
Find the exact path by running this in Blender's Python console:
    import sys; print(sys.executable)

If pip says "Defaulting to user installation" and you STILL get
ModuleNotFoundError inside Blender afterwards, Blender's bundled Python
isn't checking that user folder. Fix without needing admin rights:
    "<python path above>" -m pip install --target="C:\\blender_pylibs" paho-mqtt
then set EXTRA_MODULE_PATH below to that same folder.
"""

import sys
EXTRA_MODULE_PATH = r""  # e.g. r"C:\blender_pylibs" — leave "" if a normal pip install worked
if EXTRA_MODULE_PATH:
    sys.path.append(EXTRA_MODULE_PATH)

import bpy
import queue
import paho.mqtt.client as mqtt

# --- Config: must match pygame_dashboard.py exactly ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "arun/blender/tubelight_9f21"

# --- What to control ---
OBJECT_NAME = "Cylinder"
MATERIAL_NAME = "Material.001"
EMISSION_NODE_NAME = "Emission"
ON_STRENGTH = 4.0
OFF_STRENGTH = 0.0

# MQTT's network thread is NOT the main thread, and bpy data must only
# be touched from Blender's main thread. So the callback just drops
# the message in a queue, and a bpy.app.timers function (which DOES
# run on the main thread) drains it.
_msg_queue = queue.Queue()

def _on_message(client, userdata, msg):
    _msg_queue.put(msg.payload.decode())

def _apply_light_state(state: str):
    obj = bpy.data.objects.get(OBJECT_NAME)
    mat = bpy.data.materials.get(MATERIAL_NAME)
    if not obj or not mat or not mat.node_tree:
        print(f"[tubelight] could not find object '{OBJECT_NAME}' or material '{MATERIAL_NAME}'")
        return
    node = mat.node_tree.nodes.get(EMISSION_NODE_NAME)
    if not node:
        print(f"[tubelight] could not find node '{EMISSION_NODE_NAME}'")
        return
    node.inputs["Strength"].default_value = ON_STRENGTH if state == "ON" else OFF_STRENGTH
    print(f"[tubelight] set to {state}")

def _poll_queue():
    while not _msg_queue.empty():
        _apply_light_state(_msg_queue.get())
    return 0.2  # reschedule: check again in 0.2s

_client = mqtt.Client()
_client.on_message = _on_message
_client.connect(MQTT_BROKER, MQTT_PORT, 60)
_client.subscribe(MQTT_TOPIC)
_client.loop_start()  # background network thread

if not bpy.app.timers.is_registered(_poll_queue):
    bpy.app.timers.register(_poll_queue)

print("[tubelight] MQTT listener running, waiting for ON/OFF commands...")
