"""
NexGlow — Dashboard (runs on any PC/laptop, not inside Blender)
-----------------------------------------------------------------
A Pygame window with an ON/OFF button. Clicking it publishes the
new state over MQTT so any subscriber (e.g. Blender) picks it up
instantly, from anywhere with internet access.

Install once:
    pip install pygame paho-mqtt
"""

import pygame
import paho.mqtt.client as mqtt

# --- Config: must match blender_light_control.py exactly ---
MQTT_BROKER = "broker.hivemq.com"   # free public broker, fine for testing
MQTT_PORT = 1883
MQTT_TOPIC = "arun/blender/tubelight_9f21"  # make this unique to avoid clashing with strangers

# --- MQTT setup ---
client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()  # background thread handles network I/O

def publish_state(is_on: bool):
    client.publish(MQTT_TOPIC, "ON" if is_on else "OFF", retain=True)
    # retain=True: a Blender instance that connects later immediately
    # gets the last known state instead of waiting for the next click.

# --- Pygame UI ---
pygame.init()
screen = pygame.display.set_mode((320, 220))
pygame.display.set_caption("NexGlow Control")
font = pygame.font.SysFont(None, 40)

light_on = False
button_rect = pygame.Rect(60, 80, 200, 70)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(event.pos):
            light_on = not light_on
            publish_state(light_on)

    screen.fill((25, 25, 25))
    pygame.draw.rect(screen, (0, 200, 0) if light_on else (90, 90, 90), button_rect, border_radius=10)
    label = font.render("ON" if light_on else "OFF", True, (0, 0, 0))
    screen.blit(label, label.get_rect(center=button_rect.center))
    status = font.render(f"Light: {'ON' if light_on else 'OFF'}", True, (200, 200, 200))
    screen.blit(status, (60, 30))
    pygame.display.flip()

client.loop_stop()
pygame.quit()
