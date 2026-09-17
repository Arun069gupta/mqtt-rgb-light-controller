bl_info = {
    "name": "NexGlow - Tubelight MQTT Control",
    "author": "Arun",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "N/A - background listener, no UI panel",
    "description": "NexGlow: listens for MQTT ON/OFF messages and updates a light's Emission strength live",
    "category": "System",
}

"""
Same MQTT listener as blender_light_control.py, wrapped as an installable
add-on so it starts automatically every time Blender opens (instead of
needing to be run manually from the Scripting tab each session).

Install: Edit > Preferences > Add-ons > Install from Disk... > pick this
file > enable the "Tubelight MQTT Control" checkbox.
"""

import sys
EXTRA_MODULE_PATH = r"C:\blender_pylibs"  # set to "" if a normal pip install worked for you
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

_msg_queue = queue.Queue()
_client = None  # created in register(), torn down in unregister()

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

def register():
    global _client
    _client = mqtt.Client()
    _client.on_message = _on_message
    _client.connect(MQTT_BROKER, MQTT_PORT, 60)
    _client.subscribe(MQTT_TOPIC)
    _client.loop_start()
    if not bpy.app.timers.is_registered(_poll_queue):
        bpy.app.timers.register(_poll_queue)
    print("[tubelight] add-on enabled, MQTT listener running")

def unregister():
    global _client
    if bpy.app.timers.is_registered(_poll_queue):
        bpy.app.timers.unregister(_poll_queue)
    if _client is not None:
        _client.loop_stop()
        _client.disconnect()
        _client = None
    print("[tubelight] add-on disabled, MQTT listener stopped")

# Lets you still hit "Run Script" in the Text Editor to test without
# installing it as an add-on first.
if __name__ == "__main__":
    register()
