import time
from pathlib import Path

import simpleaudio as sa


def main() -> None:
    sound_path = Path(__file__).resolve().parents[1] / "sounds" / "moo.wav"
    wave_obj = sa.WaveObject.from_wave_file(str(sound_path))
    play_obj = wave_obj.play()

    # Derive the duration manually instead of calling wait_done(), which
    # crashes on macOS/Python 3.12 via simpleaudio's _is_playing.
    frame_count = len(wave_obj.audio_data) / (
        wave_obj.num_channels * wave_obj.bytes_per_sample
    )
    duration_s = frame_count / wave_obj.sample_rate

    time.sleep(duration_s + 0.1)

    print("done")


if __name__ == "__main__":
    main()
