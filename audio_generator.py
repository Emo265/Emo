import numpy as np
import soundfile as sf

def generate_audio(frequency=440, duration=1, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    audio_data = 0.5 * np.sin(2 * np.pi * frequency * t)
    sf.write('output.wav', audio_data, sample_rate)

if __name__ == '__main__':
    generate_audio()