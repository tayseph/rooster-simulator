# Hawaiian Roaming Rooster Simulator

An organic simulation of rooster movements and calls, designed to play through a 5.1 surround sound system. Experience the authentic ambiance of Hawaiian free-roaming roosters from the comfort of your home.

## Features

- Real-time simulation of multiple roosters moving in a radial area
- Spatial audio positioning with 5.1 surround sound support
- **Real-time visualization** - see rooster positions and movements on screen
- **Time-of-day based calling behavior** - roosters crow more at dawn, less at night
- Accelerated time simulation to experience full day/night cycles
- Roosters respond to nearby roosters calling
- Configurable movement patterns and calling behavior
- Individual rooster personalities with "sticky" call preferences and curiosity traits
- Distance-based volume attenuation
- Highly parameterized via YAML configuration

## Requirements

- Python 3.8 or higher
- 5.1 surround sound system (or stereo for testing)
- Audio files for rooster calls (WAV format recommended)

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Add rooster call audio files to the `calls/` directory
   - Supported formats: WAV, MP3, OGG, FLAC
   - WAV format (44.1kHz) recommended for best performance
   - **Source suggestions:**
     - Generate AI sounds: [ElevenLabs Sound Effects](https://elevenlabs.io/sound-effects/rooster) (tip: use private/incognito browser to avoid paywall)
     - Create test tones: `python create_test_audio.py`
     - Record your own or use royalty-free libraries

## Usage

### Basic Usage

Run the simulator with default configuration:
```bash
python main.py
```

### With Visualization

Run with real-time visual display of rooster positions:
```bash
python main.py --visualize
```

This opens a matplotlib window showing:
- Rooster positions in real-time
- Movement tracking
- Calling indicators (red = calling, blue = idle)
- Quadrant layout matching your speaker configuration

### Custom Configuration

Use a custom configuration file:
```bash
python main.py -c my_config.yaml
```

### Audio System Test

Test your 5.1 surround sound setup:
```bash
python main.py --test
```

This will play test tones in each quadrant at different distances to verify your speaker configuration.

### List Audio Devices

View available audio output devices:
```bash
python main.py --list-devices
```

### Stop Simulation

Press `Ctrl+C` to stop the simulation at any time.

## Configuration

Edit `config.yaml` to customize the simulation. All parameters are documented in the file.

### Key Configuration Sections

#### Rooster Count and Timing
- `num_roosters`: Number of roosters in the simulation
- `time_unit`: Base time interval for state updates (seconds)
- `time_randomization`: Randomization factor for timing (0.0 - 1.0)

#### Simulation Time
- `start_time`: Starting time of day for the simulation (HH:MM format)
- `time_scale`: Time acceleration factor (60.0 = 1 real minute = 1 simulated hour)

The simulator tracks an accelerated "time of day" that affects rooster behavior. For example, with a time scale of 60x, one real minute equals one simulated hour, allowing you to experience a full day cycle in 24 minutes.

#### Movement Parameters
- `frequency`: How often roosters consider moving
- `chance_to_move`: Probability a rooster will move when checked
- `distance_min/max`: Range of movement distances in meters
- `curiosity`: Individual rooster personality trait affecting movement
  - `min`: Minimum curiosity value (0.5 = less active)
  - `max`: Maximum curiosity value (1.5 = very active)
  - Each rooster gets a random curiosity that multiplies with `chance_to_move`
  - Higher curiosity roosters roam more, lower curiosity roosters stay put

#### Calling Parameters
- `frequency`: Base probability of calling per time unit
- `proximity_response`: Settings for roosters responding to nearby calls
  - `reply_likelihood`: Chance to respond to a nearby calling rooster
  - `trigger_distance`: Distance threshold for proximity response
  - `randomization`: Randomization factor for response behavior

#### Time-of-Day Based Calling
Roosters crow 24/7, but their calling frequency varies by time of day:

- `enabled`: Enable/disable time-of-day effects
- **Dawn Settings** (peak crowing time):
  - `dawn_time`: Time of dawn (HH:MM format)
  - `dawn_duration`: Hours around dawn with peak activity
  - `dawn_multiplier`: Frequency multiplier at dawn (5.0 = very frequent)
- **Daylight Hours**:
  - `daylight_start`: When daylight period begins
  - `daylight_end`: When daylight period ends
  - `daylight_multiplier`: Frequency multiplier during day (1.5 = moderate)
- **Nighttime**:
  - `nighttime_multiplier`: Frequency multiplier at night (0.3 = rare but still happens!)

The base calling frequency is multiplied by these values based on the simulation time, creating authentic diurnal patterns. At dawn, roosters crow almost constantly. During the day, they call frequently. At night (like 2:00 AM), they still crow occasionally.

#### Area Configuration
- `max_radius`: Size of the simulation area in meters
- `distance_steps`: Number of discrete distance levels (for future extensions)

#### Call Audio Settings
- `default_call`: Default rooster sound file
- `variation_probability`: Chance to use a different call
- `stickiness`: Individual rooster call preferences
  - `percentage_sticky_roosters`: Percentage of roosters with call preferences
  - `alternate_call_chance`: Likelihood sticky roosters pick non-default calls
  - `revert_to_default_chance`: Chance they return to default call

#### Audio Output
- `sample_rate`: Audio sample rate (typically 44100)
- `channels`: Number of audio channels (6 for 5.1)
- `volume`: Distance-based volume attenuation settings

## 5.1 Speaker Mapping

The simulator uses a quadrant-based system for spatial audio:

```
         Front
    FL    C    FR
      \   |   /
       \  |  /
        \ | /
    ----------------  Listener (You)
        / | \
       /  |  \
      /   |   \
    RL   LFE   RR
         Rear
```

**Quadrant Assignments:**
- Quadrant 0: Front Right (FR speaker primary)
- Quadrant 1: Rear Right (RR speaker primary)
- Quadrant 2: Rear Left (RL speaker primary)
- Quadrant 3: Front Left (FL speaker primary)

The center (C) channel receives bleed from front quadrants, and the subwoofer (LFE) adds low-frequency presence to all calls.

## Project Structure

```
roosters/
├── main.py              # Command-line interface
├── simulator.py         # Main simulation loop
├── rooster.py          # Rooster model and spatial positioning
├── audio_system.py     # Audio playback and mixing
├── config.yaml         # Configuration file
├── requirements.txt    # Python dependencies
├── calls/             # Directory for rooster call audio files
└── README.md          # This file
```

## How It Works

### Simulation Loop

1. Each rooster has a position in polar coordinates (angle, distance from listener)
2. Simulation tracks accelerated "time of day" (e.g., 1 real minute = 1 simulated hour)
3. At each time step, roosters evaluate whether to move or call
4. Calling frequency is adjusted based on time of day (dawn = peak, night = rare)
5. Movement updates position randomly within configured constraints
6. Calling triggers audio playback with spatial positioning
7. Roosters within proximity distance can trigger response calls
8. Audio is mixed in real-time and output to 5.1 surround system

### Spatial Audio

- Each rooster's position determines which speakers receive audio
- Volume decreases with distance from the listener
- Quadrant-based positioning ensures calls come from appropriate speakers
- Adjacent speakers receive reduced volume for smoother transitions

### Rooster Behavior

- **Movement**: Probabilistic, randomized distance and direction with individual curiosity traits
- **Curiosity/Roaming**: Each rooster has unique activity level - some roam constantly, others stay local
- **Calling**: Base frequency adjusted by time of day, plus proximity responses
- **Circadian Rhythm**: Roosters crow constantly at dawn, frequently during day, rarely at night
- **Personality**: Some roosters develop preferences for specific calls ("stickiness")
- **Responsiveness**: Roosters react to nearby calls, creating organic interactions

## Troubleshooting

### No Audio Output

1. Run `python main.py --list-devices` to check available devices
2. Verify your 5.1 system is connected and set as default output
3. Check that audio files exist in the `calls/` directory
4. Try the audio test: `python main.py --test`

### Audio Files Not Found

- Ensure audio files are in the `calls/` directory
- Check file extensions (.wav, .mp3, .ogg, .flac)
- Verify the `default_call` in config.yaml matches an actual file

### Performance Issues

- Reduce `num_roosters` in configuration
- Use WAV files instead of compressed formats
- Ensure sample rates match your system (44100 Hz typical)

### Wrong Speaker Output

- Run `python main.py --test` to verify speaker positions
- Check your system's 5.1 configuration
- Verify speaker cables are connected correctly

## Tips for Best Experience

1. **Start Simple**: Begin with 3-5 roosters and adjust from there
2. **Experience Dawn**: Start simulation at 05:30 with 60x time scale to experience the dawn chorus
3. **Tune Timing**: Adjust `time_unit` and calling `frequency` for desired density
4. **Collect Audio**: Use multiple varied rooster call recordings for realism
5. **Adjust Volume**: Configure `min_volume` and `max_volume` for your space
6. **Enable Stickiness**: Individual rooster personalities add character
7. **Time Scale**: Try different time scales (30x for slower, 120x for faster day cycles)

## Future Enhancements

Potential features for future versions:
- Real-time visualization of rooster positions
- Web-based control interface
- Recording/playback of simulation sessions
- Support for 7.1 surround sound
- Environmental sound layering (wind, rain, ambient nature sounds)
- Weather effects on rooster behavior

## License

This project is provided as-is for personal use and enjoyment.

## Credits

Created for those who appreciate the unique soundscape of Hawaiian free-roaming roosters.
