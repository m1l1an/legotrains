import pygame
from pathlib import Path
from time import sleep

pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)  # low latency
sound_path = Path(__file__).resolve().parents[1] / "sounds" / "moo.wav"
moo = pygame.mixer.Sound(str(sound_path))

# Non-blocking play
channel = moo.play()  # returns immediately

# Check if still playing
while channel.get_busy():
    sleep(0.01)
