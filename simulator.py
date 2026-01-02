import time
import yaml
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from rooster import Rooster, Position
from audio_system import AudioSystem


class RoosterSimulator:
    """Main simulator class that manages the rooster simulation."""

    def __init__(self, config_path: str = "config.yaml", enable_visualization: bool = False):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Initialize audio system
        self.audio_system = AudioSystem(self.config)

        # Initialize roosters
        self.roosters: List[Rooster] = []
        self._initialize_roosters()

        # Simulation state
        self.running = False
        self.start_time = 0.0
        self.current_time = 0.0

        # Simulation time tracking (time of day)
        self.sim_start_time_of_day = self._parse_time(
            self.config.get('simulation_time', {}).get('start_time', '06:00')
        )
        self.time_scale = self.config.get('simulation_time', {}).get('time_scale', 60.0)

        # Visualization
        self.visualizer: Optional[object] = None
        if enable_visualization:
            try:
                from visualization import RoosterVisualizer
                print("Initializing visualization...")
                self.visualizer = RoosterVisualizer(
                    max_radius=self.config['area']['max_radius'],
                    num_roosters=self.config['num_roosters']
                )
                print("✓ Visualization window opened")
            except ImportError:
                print("✗ Warning: matplotlib not available. Install with: pip install matplotlib")
                print("  Continuing without visualization.")
            except Exception as e:
                print(f"✗ Warning: Could not initialize visualization: {e}")
                import traceback
                traceback.print_exc()
                print("  Continuing without visualization.")

        # Statistics
        self.stats = {
            'total_calls': 0,
            'total_moves': 0,
            'proximity_responses': 0
        }

    def _initialize_roosters(self):
        """Create all roosters for the simulation."""
        num_roosters = self.config['num_roosters']
        max_radius = self.config['area']['max_radius']
        available_calls = self.audio_system.available_calls

        print(f"Initializing {num_roosters} roosters...")

        for i in range(num_roosters):
            rooster = Rooster(
                rooster_id=i,
                config=self.config,
                max_radius=max_radius,
                available_calls=available_calls
            )
            self.roosters.append(rooster)
            print(f"  Rooster {i}: position (angle={rooster.position.angle:.2f}, "
                  f"distance={rooster.position.distance:.1f}m), "
                  f"quadrant={rooster.position.get_quadrant()}, "
                  f"curiosity={rooster.curiosity:.2f}, "
                  f"sticky={rooster.is_sticky}")

    def _get_nearby_calling_roosters(self, rooster: Rooster) -> List[Rooster]:
        """
        Find roosters that are currently calling and within proximity range.
        """
        trigger_distance = self.config['calling']['proximity_response']['trigger_distance']
        nearby_calling = []

        for other in self.roosters:
            if other.id == rooster.id:
                continue

            if other.is_calling:
                distance = rooster.position.distance_to(other.position)
                if distance <= trigger_distance:
                    nearby_calling.append(other)

        return nearby_calling

    def _parse_time(self, time_str: str) -> timedelta:
        """Parse time string (HH:MM) to timedelta from midnight."""
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 else 0
        return timedelta(hours=hours, minutes=minutes)

    def _get_simulation_time_of_day(self) -> timedelta:
        """Get current simulation time of day based on elapsed real time."""
        elapsed_real = self.current_time - self.start_time
        elapsed_sim = elapsed_real * self.time_scale  # Scale up time
        current_sim_time = self.sim_start_time_of_day + timedelta(seconds=elapsed_sim)

        # Wrap around 24 hours
        total_seconds = current_sim_time.total_seconds()
        seconds_in_day = 24 * 60 * 60
        wrapped_seconds = total_seconds % seconds_in_day

        return timedelta(seconds=wrapped_seconds)

    def _format_time_of_day(self, td: timedelta) -> str:
        """Format timedelta as HH:MM:SS time of day."""
        total_seconds = int(td.total_seconds())
        hours = (total_seconds // 3600) % 24
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def _get_time_of_day_multiplier(self) -> float:
        """
        Calculate the calling frequency multiplier based on time of day.
        Dawn = peak calling time, day = moderate, night = low (but still happen!)
        """
        tod_config = self.config.get('calling', {}).get('time_of_day', {})

        if not tod_config.get('enabled', True):
            return 1.0

        current_time = self._get_simulation_time_of_day()

        # Parse configuration times
        dawn_time = self._parse_time(tod_config.get('dawn_time', '06:00'))
        dawn_duration = tod_config.get('dawn_duration', 1.0) * 3600  # Convert hours to seconds
        dawn_multiplier = tod_config.get('dawn_multiplier', 5.0)

        daylight_start = self._parse_time(tod_config.get('daylight_start', '07:00'))
        daylight_end = self._parse_time(tod_config.get('daylight_end', '18:00'))
        daylight_multiplier = tod_config.get('daylight_multiplier', 1.5)

        nighttime_multiplier = tod_config.get('nighttime_multiplier', 0.3)

        # Check if we're in dawn period
        dawn_start = dawn_time - timedelta(seconds=dawn_duration / 2)
        dawn_end = dawn_time + timedelta(seconds=dawn_duration / 2)

        # Handle wrapping around midnight
        current_seconds = current_time.total_seconds()
        dawn_start_seconds = dawn_start.total_seconds() % (24 * 3600)
        dawn_end_seconds = dawn_end.total_seconds() % (24 * 3600)

        # Check dawn period
        if dawn_start_seconds <= current_seconds <= dawn_end_seconds:
            return dawn_multiplier

        # Check daylight period
        daylight_start_seconds = daylight_start.total_seconds()
        daylight_end_seconds = daylight_end.total_seconds()

        if daylight_start_seconds <= current_seconds <= daylight_end_seconds:
            return daylight_multiplier

        # Otherwise, nighttime
        return nighttime_multiplier

    def _update_roosters(self):
        """Update all roosters' states."""
        # Get time-of-day multiplier for this update
        tod_multiplier = self._get_time_of_day_multiplier()

        # First pass: update calling states (check if calls have finished)
        for rooster in self.roosters:
            rooster.update_calling_state(self.current_time)

        # Second pass: check for movements
        for rooster in self.roosters:
            if rooster.should_move(self.current_time):
                old_pos = rooster.position
                rooster.move()
                self.stats['total_moves'] += 1

                if self.stats['total_moves'] % 10 == 0:  # Log every 10th move
                    print(f"  Rooster {rooster.id} moved: "
                          f"Q{old_pos.get_quadrant()} ({old_pos.distance:.1f}m) -> "
                          f"Q{rooster.position.get_quadrant()} ({rooster.position.distance:.1f}m)")

        # Third pass: check for calls
        # We do this separately to allow roosters to respond to calls that happen in this timestep
        calling_roosters = []

        for rooster in self.roosters:
            # Check if rooster should call
            nearby_calling = self._get_nearby_calling_roosters(rooster)
            should_call = rooster.should_call(self.current_time, nearby_calling, tod_multiplier)

            if should_call:
                calling_roosters.append((rooster, len(nearby_calling) > 0))

        # Fourth pass: execute calls
        for rooster, is_response in calling_roosters:
            call_filename = rooster.start_call(self.current_time)
            speaker_volumes = rooster.get_speaker_volumes()

            # Play the sound
            sound_id = self.audio_system.play_sound(call_filename, speaker_volumes)

            self.stats['total_calls'] += 1
            if is_response:
                self.stats['proximity_responses'] += 1

            # Log the call
            print(f"  Rooster {rooster.id} calling: {call_filename} "
                  f"(Q{rooster.position.get_quadrant()}, {rooster.position.distance:.1f}m, "
                  f"vol={rooster.get_volume_for_distance():.2f}"
                  f"{', RESPONSE' if is_response else ''})")

    def _print_status(self):
        """Print current simulation status."""
        elapsed = self.current_time - self.start_time
        active_sounds = self.audio_system.get_active_sound_count()
        sim_time = self._get_simulation_time_of_day()
        sim_time_str = self._format_time_of_day(sim_time)
        tod_multiplier = self._get_time_of_day_multiplier()

        print(f"\n[{elapsed:.1f}s | Sim Time: {sim_time_str}] Status: {len(self.roosters)} roosters, "
              f"{active_sounds} active sounds")
        print(f"  Stats: {self.stats['total_calls']} calls "
              f"({self.stats['proximity_responses']} responses), "
              f"{self.stats['total_moves']} moves")
        print(f"  Time of day multiplier: {tod_multiplier:.2f}x")

    def run(self):
        """Run the simulation continuously."""
        print("\n" + "="*60)
        print("Hawaiian Roaming Rooster Simulator")
        print("="*60)
        print(f"Configuration: {self.config['num_roosters']} roosters, "
              f"{self.config['area']['max_radius']:.0f}m radius")
        print(f"Audio: {len(self.audio_system.available_calls)} call files available")
        print(f"Time of day: Starts at {self._format_time_of_day(self.sim_start_time_of_day)}, "
              f"time scale {self.time_scale:.1f}x")
        print("Press Ctrl+C to stop the simulation")
        print("="*60 + "\n")

        # Start audio stream
        self.audio_system.start_stream()

        # Initialize timing
        self.running = True
        self.start_time = time.time()
        self.current_time = self.start_time
        last_status_time = self.start_time
        last_viz_update_time = self.start_time

        status_interval = 10.0  # Print status every 10 seconds
        viz_update_interval = 0.5  # Update visualization every 0.5 seconds

        try:
            while self.running:
                # Update current time
                self.current_time = time.time()

                # Update all roosters
                self._update_roosters()

                # Print status periodically
                if self.current_time - last_status_time >= status_interval:
                    self._print_status()
                    last_status_time = self.current_time

                # Update visualization periodically
                if self.visualizer and self.current_time - last_viz_update_time >= viz_update_interval:
                    sim_time = self._get_simulation_time_of_day()
                    sim_time_str = self._format_time_of_day(sim_time)
                    self.visualizer.update(self.roosters, sim_time_str)
                    last_viz_update_time = self.current_time

                # Sleep for a short interval (main simulation tick)
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\nShutting down simulation...")

        finally:
            self.stop()

    def stop(self):
        """Stop the simulation and clean up resources."""
        self.running = False
        self.audio_system.stop_stream()

        # Close visualization if active
        if self.visualizer:
            self.visualizer.close()

        print("\nFinal Statistics:")
        print(f"  Total runtime: {self.current_time - self.start_time:.1f} seconds")
        print(f"  Total calls: {self.stats['total_calls']}")
        print(f"  Proximity responses: {self.stats['proximity_responses']}")
        print(f"  Total moves: {self.stats['total_moves']}")
        print("\nSimulation stopped.")

    def print_rooster_positions(self):
        """Print current positions of all roosters."""
        print("\nCurrent Rooster Positions:")
        print("-" * 60)
        for rooster in self.roosters:
            x, y = rooster.position.to_cartesian()
            print(f"  Rooster {rooster.id}: "
                  f"Quadrant {rooster.position.get_quadrant()}, "
                  f"Distance {rooster.position.distance:.1f}m, "
                  f"Cartesian ({x:.1f}, {y:.1f}), "
                  f"Volume {rooster.get_volume_for_distance():.2f}")
        print("-" * 60)


def main():
    """Main entry point."""
    import sys

    config_file = "config.yaml"
    if len(sys.argv) > 1:
        config_file = sys.argv[1]

    try:
        simulator = RoosterSimulator(config_file)
        simulator.print_rooster_positions()
        print()
        simulator.run()
    except FileNotFoundError as e:
        print(f"Error: Configuration file not found: {config_file}")
        print("Please ensure config.yaml exists in the current directory.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
