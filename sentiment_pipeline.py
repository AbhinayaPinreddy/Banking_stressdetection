import librosa
import numpy as np

def analyze_audio(audio_file):
    """
    Voice stress: loudness (main) + higher pitch = stressed (e.g. shouting).
    Normal tone -> low score; shouting/raised voice -> high score (0.6-1.0).
    """
    y, sr = librosa.load(audio_file, sr=None)

    rms = librosa.feature.rms(y=y)[0]
    energy = np.mean(rms)
    # Peak loudness in segment (shouting has high peaks)
    energy_max = np.max(rms) if len(rms) > 0 else energy

    f0 = librosa.yin(y, fmin=50, fmax=300)
    pitch = np.nanmean(f0)
    if np.isnan(pitch):
        pitch = 120.0

    # Normalize: normal ~0.03-0.06, somewhat loud ~0.06-0.09, shouting ~0.1+
    # Sensitive so even "somewhat shouting" gets a high score and calming response
    energy_norm = np.clip(energy / 0.09, 0.0, 1.0)
    peak_norm = np.clip(energy_max / 0.15, 0.0, 1.0)
    loudness = max(energy_norm, peak_norm * 0.7)  # loudness from mean + peak

    pitch_min, pitch_max = 80.0, 280.0  # focus on speech range
    pitch_norm = np.clip((pitch - pitch_min) / (pitch_max - pitch_min), 0.0, 1.0)

    # Weight loudness more — shouting = mainly loud
    stress_score = 0.7 * loudness + 0.3 * pitch_norm
    return float(np.clip(stress_score, 0.0, 1.0))