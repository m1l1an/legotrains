
import simpleaudio as sa

# Load the sound file (must be a .wav)
wave_obj = sa.WaveObject.from_wave_file("../sounds/moo.wav")

# Play the sound
play_obj = wave_obj.play()

# Wait until sound finishes playing
play_obj.wait_done()

