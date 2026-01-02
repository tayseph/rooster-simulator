# Hawaiian Roaming Rooster Simulator - Development Notes

## Project Overview
A real-time spatial audio simulator that models rooster behavior with 5.1/stereo surround sound support and real-time visualization. Roosters move in a radial area with the listener at the center, with time-of-day based calling patterns.

## Current State (Last Updated: 2026-01-02)

### Working Features
✅ **Core Simulation**
- Multiple roosters with configurable count
- Movement in radial area (listener at center)
- Time-of-day based calling frequency (dawn = peak, night = rare)
- Accelerated time simulation (60x default - 1 real min = 1 sim hour)
- Proximity-based response calling

✅ **Audio System**
- 5.1 surround sound with automatic stereo fallback
- Spatial positioning via quadrant system (4 main speakers)
- Distance-based volume attenuation
- Intelligent stereo downmix when 5.1 unavailable
- Multi-format support: WAV, MP3, FLAC, OGG
- MP3 support via ffmpeg (no pydub needed)
- Audio caching for performance

✅ **Visualization**
- Real-time matplotlib window showing rooster positions
- Color-coded calling indicators (red = calling, blue = idle)
- Numeric rooster IDs
- Quadrant labels matching speaker layout
- Distance circles for spatial reference
- Updates every 0.5 seconds
- Shows simulation time in title

✅ **Configuration**
- YAML-based config system
- All behavior parameters exposed
- Time-of-day calling multipliers
- Movement distances and frequencies
- Call "stickiness" (rooster personalities)

## File Structure
```
roosters/
├── main.py                     # CLI entry point
├── simulator.py                # Main simulation loop, time-of-day logic
├── rooster.py                 # Rooster model, movement, calling logic
├── audio_system.py            # 5.1/stereo audio playback, MP3 support
├── visualization.py           # Matplotlib real-time visualization
├── config.yaml                # Configuration (user modified!)
├── create_test_audio.py       # Generate test tones
├── requirements.txt           # Python dependencies
├── calls/                     # Audio files directory
│   ├── rooster_call_1.wav
│   ├── rooster_call_2.mp3
│   ├── rooster_call_3.mp3
│   └── rooster1.wav
├── project.md                 # Original requirements
├── README.md                  # User documentation
└── DEVELOPMENT_NOTES.md       # This file
```

## Key Implementation Details

### Movement System (rooster.py:120-154)
**CRITICAL FIX APPLIED**: Movement now uses actual distance walked, not angle+radius changes.
- Old bug: Changed angle (±180°) AND radius, causing 50m+ jumps
- Fixed: Convert to cartesian → walk N meters in random direction → convert back to polar
- Config: `distance_min: 2.0`, `distance_max: 10.0` now means actual 2-10m walks

### Calling Indicator (rooster.py:55-60, 197-202)
**CRITICAL FIX APPLIED**: Calling state persists for duration, not single frame.
- `call_duration = 2.0` seconds
- `update_calling_state()` method checks elapsed time
- Simulator calls this every update cycle (simulator.py:181-182)
- Visualization now consistently shows red indicators

### Time-of-Day System (simulator.py:88-173)
- Tracks accelerated simulation time
- Calculates multipliers: dawn=5.0x, day=1.5x, night=0.3x
- Multiplier passed to `rooster.should_call()` method
- Base calling frequency × multiplier (capped at 1.0)

### Audio System Fallback (audio_system.py:139-179)
- Try 6-channel (5.1) first
- Auto-fallback to 2-channel (stereo) on macOS/test systems
- Stereo downmix: Left = FL + 0.7*C + 0.7*RL, Right = FR + 0.7*C + 0.7*RR

### MP3 Support (audio_system.py:98-137)
- Uses ffmpeg subprocess (NOT pydub - Python 3.14 incompatible)
- Converts MP3 → temporary WAV → loads with soundfile
- Auto-converts to mono at target sample rate
- Cached after first load

## Configuration Notes

### User's Current Config
- `time_unit: 10.0` (user changed from default 1.0)
- 5 roosters
- 60x time scale
- Starts at 06:00 (dawn)

### Important Config Parameters
```yaml
simulation_time:
  start_time: "06:00"
  time_scale: 60.0

calling:
  frequency: 0.2  # Base frequency
  time_of_day:
    dawn_multiplier: 5.0
    daylight_multiplier: 1.5
    nighttime_multiplier: 0.3

movement:
  distance_min: 2.0
  distance_max: 10.0
```

## Dependencies & Setup

### Python Requirements
```
numpy>=1.24.0
sounddevice>=0.4.6
soundfile>=0.12.1
PyYAML>=6.0
matplotlib>=3.5.0
```

### System Requirements
- macOS with Homebrew (user's system)
- ffmpeg (via `brew install ffmpeg`) - required for MP3
- Python 3.14 (user's version)

### Installation
```bash
pip install -r requirements.txt
brew install ffmpeg  # For MP3 support
```

## Usage

### Basic Run
```bash
python main.py
```

### With Visualization
```bash
python main.py --visualize
```

### Audio Test
```bash
python main.py --test
```

### Other Options
```bash
python main.py --list-devices    # Show audio devices
python main.py -c custom.yaml    # Custom config
```

## Known Issues & Fixes Applied

### Fixed Issues
1. ✅ **Audio channel fallback** - Stereo fallback for non-5.1 systems
2. ✅ **Movement distance** - Now uses actual walk distance, not geometric jumps
3. ✅ **Calling indicator** - Persists for 2 seconds, not single frame
4. ✅ **MP3 filename typo** - Fixed `rooster_call_2mp3` → `rooster_call_2.mp3`
5. ✅ **MP3 loading** - Uses ffmpeg directly, works with Python 3.14
6. ✅ **Visualization window** - Added TkAgg backend, plt.pause() calls

### No Known Issues
System is stable and working as designed.

## Future Enhancement Ideas (Not Implemented)

From user discussions and README:
- Real-time web dashboard
- Recording/playback of sessions
- 7.1 surround support
- Environmental sounds (wind, rain)
- Weather effects on behavior
- More sophisticated movement patterns (foraging, roosting)
- Variable call duration based on time of day
- Territory/dominance behaviors

## Development Session History

### Session 2026-01-02
1. Built initial simulator with 5.1 audio, spatial positioning
2. Added time-of-day based calling behavior
3. Added real-time matplotlib visualization
4. Fixed audio fallback for stereo systems
5. Fixed movement distance bug (50m+ jumps → actual 2-10m walks)
6. Fixed calling indicator inconsistency (single frame → 2 second duration)
7. Added MP3 support via ffmpeg (bypassing pydub/Python 3.14 issue)
8. Fixed MP3 filename typo

## Important Code Patterns

### Adding New Behavior Parameters
1. Add to `config.yaml` with comments
2. Update README.md configuration section
3. Access in code: `self.config['section']['parameter']`
4. Consider time-of-day multipliers if relevant

### Audio File Support
- Place files in `calls/` directory
- Formats: WAV (fastest), MP3 (ffmpeg), FLAC, OGG
- Mono or stereo (auto-converted to mono)
- Any sample rate (auto-noted, used as-is)

### Visualization Updates
- Called every 0.5s in simulator loop (simulator.py:277-281)
- Reads `rooster.is_calling` state for colors
- Shows simulation time via `_format_time_of_day()`

## Testing Commands

```bash
# Test audio loading
python -c "from audio_system import AudioSystem; import yaml; c=yaml.safe_load(open('config.yaml')); a=AudioSystem(c); print(a.available_calls)"

# Test visualization (quick check)
python -c "from visualization import RoosterVisualizer; v=RoosterVisualizer(100, 5); import time; time.sleep(2)"

# Check ffmpeg
ffmpeg -version

# List audio devices
python main.py --list-devices
```

## Git Status
Not initialized as git repo yet.

## User Notes
- User is processing audio samples (more rooster recordings coming)
- Testing on macOS before deploying to 5.1 system
- User stepped away - project ready for handoff to future session

---

**Last session by**: Claude (Sonnet 4.5)
**Date**: January 2, 2026
**Status**: ✅ Fully functional, no blocking issues
