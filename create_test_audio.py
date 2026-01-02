#!/usr/bin/env python3
"""
Create test audio files for the rooster simulator.
This script generates simple sine wave tones that can be used for testing
before you have actual rooster call recordings.
"""

import numpy as np
import soundfile as sf
import os


def create_test_call(filename, frequency, duration=2.0, sample_rate=44100):
    """Create a test audio file with varying frequency (pseudo rooster call)."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)

    # Create a frequency-modulated tone that vaguely resembles a rooster call
    # Start high, dip, then go high again
    freq_mod = np.sin(2 * np.pi * 2 * t) * 100  # Frequency modulation
    signal = np.sin(2 * np.pi * (frequency + freq_mod) * t)

    # Apply amplitude envelope (fade in/out and shape)
    envelope = np.ones_like(t)

    # Quick fade in
    fade_in_len = int(0.05 * sample_rate)
    envelope[:fade_in_len] = np.linspace(0, 1, fade_in_len)

    # Fade out
    fade_out_len = int(0.3 * sample_rate)
    envelope[-fade_out_len:] = np.linspace(1, 0, fade_out_len)

    # Apply envelope
    signal = signal * envelope * 0.3  # Reduce amplitude

    # Convert to float32
    signal = signal.astype('float32')

    # Save as WAV file
    sf.write(filename, signal, sample_rate)
    print(f"Created: {filename}")


def main():
    # Create calls directory if it doesn't exist
    calls_dir = "calls"
    os.makedirs(calls_dir, exist_ok=True)

    print("Creating test audio files...")
    print("These are simple test tones - replace with real rooster recordings for best experience.\n")

    # Create several test calls with different frequencies
    test_calls = [
        ("rooster_call_1.wav", 600),  # Default call
        ("rooster_call_2.wav", 550),
        ("rooster_call_3.wav", 650),
        ("rooster_call_4.wav", 580),
        ("rooster_call_5.wav", 620),
    ]

    for filename, freq in test_calls:
        filepath = os.path.join(calls_dir, filename)
        create_test_call(filepath, freq)

    print(f"\nCreated {len(test_calls)} test audio files in '{calls_dir}/' directory")
    print("You can now run the simulator with: python main.py")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
