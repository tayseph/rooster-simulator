import os
import numpy as np
import sounddevice as sd
import soundfile as sf
from typing import Dict, Optional, Tuple
from threading import Lock
import subprocess
import tempfile


class AudioSystem:
    """Manages audio playback for 5.1 surround sound system."""

    def __init__(self, config: dict, calls_dir: str = "calls"):
        self.config = config
        self.calls_dir = calls_dir
        self.sample_rate = config['audio']['sample_rate']
        self.requested_channels = config['audio']['channels']  # 6 for 5.1
        self.channels = self.requested_channels  # Will be adjusted if needed
        self.is_stereo_mode = False

        # Audio cache: filename -> (audio_data, sample_rate)
        self.audio_cache: Dict[str, Tuple[np.ndarray, int]] = {}

        # Currently playing sounds with their parameters
        # Structure: {sound_id: {'data': array, 'position': int, 'volumes': tuple}}
        self.active_sounds: Dict[int, dict] = {}
        self.next_sound_id = 0
        self.lock = Lock()

        # Output stream
        self.stream: Optional[sd.OutputStream] = None

        # Load available audio files
        self.available_calls = self._discover_calls()

    def _discover_calls(self) -> list:
        """Discover available call audio files in the calls directory."""
        if not os.path.exists(self.calls_dir):
            print(f"Warning: Calls directory '{self.calls_dir}' not found. Creating it.")
            os.makedirs(self.calls_dir, exist_ok=True)
            return []

        audio_extensions = ['.wav', '.mp3', '.ogg', '.flac']
        calls = []

        for filename in os.listdir(self.calls_dir):
            if any(filename.lower().endswith(ext) for ext in audio_extensions):
                calls.append(filename)

        if not calls:
            print(f"Warning: No audio files found in '{self.calls_dir}' directory.")
            print("Simulation will run without audio. Add .wav files to enable sound.")

        return calls

    def load_audio(self, filename: str) -> Optional[Tuple[np.ndarray, int]]:
        """Load an audio file and cache it. Returns (audio_data, sample_rate)."""
        if filename in self.audio_cache:
            return self.audio_cache[filename]

        filepath = os.path.join(self.calls_dir, filename)

        if not os.path.exists(filepath):
            print(f"Warning: Audio file not found: {filepath}")
            return None

        # Try soundfile first (supports WAV, FLAC, OGG)
        try:
            data, file_sample_rate = sf.read(filepath, dtype='float32')

            # Convert to mono if stereo/multi-channel
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)

            # Resample if necessary (simple approach - for production use scipy.signal.resample)
            if file_sample_rate != self.sample_rate:
                print(f"Note: {filename} sample rate ({file_sample_rate}) differs from config ({self.sample_rate})")
                # For simplicity, we'll just use it as-is and adjust playback
                # In production, proper resampling would be needed

            self.audio_cache[filename] = (data, file_sample_rate)
            return (data, file_sample_rate)

        except Exception as e:
            # If soundfile fails and it's an MP3, try ffmpeg
            if filename.lower().endswith('.mp3'):
                try:
                    return self._load_mp3_with_ffmpeg(filepath, filename)
                except Exception as e2:
                    print(f"Error loading MP3 file {filepath}: {e2}")
                    print(f"Tip: Convert {filename} to WAV format for better compatibility.")
                    return None
            else:
                print(f"Error loading audio file {filepath}: {e}")
                return None

    def _load_mp3_with_ffmpeg(self, filepath: str, filename: str) -> Tuple[np.ndarray, int]:
        """Load an MP3 file using ffmpeg to convert to WAV."""
        try:
            # Create a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
                tmp_wav_path = tmp_wav.name

            # Use ffmpeg to convert MP3 to WAV
            # -i: input file
            # -ac 1: convert to mono
            # -ar: output sample rate
            # -f wav: output format
            result = subprocess.run([
                'ffmpeg', '-i', filepath,
                '-ac', '1',  # Mono
                '-ar', str(self.sample_rate),  # Target sample rate
                '-f', 'wav',
                '-y',  # Overwrite output file
                tmp_wav_path
            ], capture_output=True, text=True, check=True)

            # Load the converted WAV file
            data, file_sample_rate = sf.read(tmp_wav_path, dtype='float32')

            # Clean up temporary file
            os.unlink(tmp_wav_path)

            print(f"Loaded MP3: {filename} (converted to {self.sample_rate}Hz mono)")

            self.audio_cache[filename] = (data, file_sample_rate)
            return (data, file_sample_rate)

        except subprocess.CalledProcessError as e:
            print(f"ffmpeg error: {e.stderr}")
            raise
        except Exception as e:
            # Clean up temp file if it exists
            if 'tmp_wav_path' in locals() and os.path.exists(tmp_wav_path):
                os.unlink(tmp_wav_path)
            raise

    def start_stream(self):
        """Start the audio output stream with automatic fallback to stereo."""
        if self.stream is not None:
            return

        # Try requested channels first (e.g., 6 for 5.1)
        try:
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=self._audio_callback,
                blocksize=1024
            )
            self.stream.start()
            print(f"Audio stream started: {self.sample_rate}Hz, {self.channels} channels")
            if self.channels == 6:
                print("  Mode: 5.1 Surround Sound")
            return
        except Exception as e:
            if self.channels > 2:
                print(f"Unable to open {self.channels}-channel audio stream: {e}")
                print(f"Falling back to stereo (2 channels)...")

                # Try stereo fallback
                try:
                    self.channels = 2
                    self.is_stereo_mode = True
                    self.stream = sd.OutputStream(
                        samplerate=self.sample_rate,
                        channels=self.channels,
                        callback=self._audio_callback,
                        blocksize=1024
                    )
                    self.stream.start()
                    print(f"Audio stream started: {self.sample_rate}Hz, 2 channels (stereo)")
                    print("  Mode: Stereo (spatial audio adapted)")
                    return
                except Exception as e2:
                    print(f"Error starting stereo audio stream: {e2}")
                    print("Simulation will continue without audio output.")
            else:
                print(f"Error starting audio stream: {e}")
                print("Simulation will continue without audio output.")

    def stop_stream(self):
        """Stop the audio output stream."""
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def _audio_callback(self, outdata: np.ndarray, frames: int, time_info, status):
        """
        Audio callback function called by sounddevice.
        Mixes all active sounds into the output buffer.
        """
        if status:
            print(f"Audio callback status: {status}")

        # Initialize output buffer with silence
        outdata.fill(0)

        with self.lock:
            sounds_to_remove = []

            for sound_id, sound_info in self.active_sounds.items():
                audio_data = sound_info['data']
                position = sound_info['position']
                volumes = sound_info['volumes']  # (FL, FR, C, LFE, RL, RR)

                # Calculate how many frames we can read
                remaining_frames = len(audio_data) - position
                frames_to_read = min(frames, remaining_frames)

                if frames_to_read > 0:
                    # Get the audio segment
                    segment = audio_data[position:position + frames_to_read]

                    if self.is_stereo_mode:
                        # Downmix 5.1 to stereo
                        # volumes = (FL, FR, C, LFE, RL, RR)
                        fl, fr, c, lfe, rl, rr = volumes
                        left = fl + 0.7 * c + 0.7 * rl
                        right = fr + 0.7 * c + 0.7 * rr

                        outdata[:frames_to_read, 0] += segment * left   # Left channel
                        outdata[:frames_to_read, 1] += segment * right  # Right channel
                    else:
                        # Apply volume and distribute to channels
                        # Channel order: FL, FR, C, LFE, RL, RR
                        for i, volume in enumerate(volumes):
                            if i < self.channels:
                                outdata[:frames_to_read, i] += segment * volume

                    # Update position
                    sound_info['position'] += frames_to_read

                # Mark for removal if finished
                if sound_info['position'] >= len(audio_data):
                    sounds_to_remove.append(sound_id)

            # Remove completed sounds
            for sound_id in sounds_to_remove:
                del self.active_sounds[sound_id]

    def play_sound(self, filename: str, speaker_volumes: Tuple[float, float, float, float, float, float]) -> Optional[int]:
        """
        Play a sound with specified volume for each speaker.
        Returns sound_id if successful, None otherwise.
        """
        audio_data = self.load_audio(filename)
        if audio_data is None:
            return None

        data, file_sr = audio_data

        with self.lock:
            sound_id = self.next_sound_id
            self.next_sound_id += 1

            self.active_sounds[sound_id] = {
                'data': data,
                'position': 0,
                'volumes': speaker_volumes
            }

        return sound_id

    def get_active_sound_count(self) -> int:
        """Return the number of currently playing sounds."""
        with self.lock:
            return len(self.active_sounds)

    def create_test_tone(self, frequency: float = 440.0, duration: float = 1.0) -> np.ndarray:
        """Create a test tone for debugging (when no audio files are available)."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        tone = np.sin(frequency * 2 * np.pi * t) * 0.3  # Reduced amplitude
        # Apply fade in/out to avoid clicks
        fade_length = int(0.05 * self.sample_rate)  # 50ms fade
        fade_in = np.linspace(0, 1, fade_length)
        fade_out = np.linspace(1, 0, fade_length)
        tone[:fade_length] *= fade_in
        tone[-fade_length:] *= fade_out
        return tone.astype('float32')

    def play_test_tone(self, quadrant: int, distance: float):
        """Play a test tone in a specific quadrant (for testing without audio files)."""
        tone = self.create_test_tone(frequency=440 + (quadrant * 100), duration=0.5)

        # Calculate volumes similar to rooster
        max_radius = self.config['area']['max_radius']
        min_dist = self.config['audio']['volume']['min_distance']
        max_dist = self.config['audio']['volume']['max_distance']
        min_vol = self.config['audio']['volume']['min_volume']
        max_vol = self.config['audio']['volume']['max_volume']

        # Calculate base volume
        if distance <= min_dist:
            base_volume = max_vol
        elif distance >= max_dist:
            base_volume = min_vol
        else:
            ratio = (distance - min_dist) / (max_dist - min_dist)
            base_volume = max_vol - (ratio * (max_vol - min_vol))

        # Assign to speakers based on quadrant
        fl = fr = c = lfe = rl = rr = 0.0
        if quadrant == 0:  # Front Right
            fr = base_volume * 0.8
            c = base_volume * 0.2
        elif quadrant == 1:  # Rear Right
            rr = base_volume * 0.8
            fr = base_volume * 0.2
        elif quadrant == 2:  # Rear Left
            rl = base_volume * 0.8
            fl = base_volume * 0.2
        elif quadrant == 3:  # Front Left
            fl = base_volume * 0.8
            c = base_volume * 0.2

        lfe = base_volume * 0.15

        with self.lock:
            sound_id = self.next_sound_id
            self.next_sound_id += 1
            self.active_sounds[sound_id] = {
                'data': tone,
                'position': 0,
                'volumes': (fl, fr, c, lfe, rl, rr)
            }

        return sound_id
