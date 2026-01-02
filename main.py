#!/usr/bin/env python3
"""
Hawaiian Roaming Rooster Simulator
Main command-line interface
"""

import argparse
import sys
import os
from simulator import RoosterSimulator


def main():
    parser = argparse.ArgumentParser(
        description='Hawaiian Roaming Rooster Simulator - Spatial audio rooster simulation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          Run with default config.yaml
  %(prog)s -c custom_config.yaml    Run with custom configuration
  %(prog)s --visualize              Run with real-time visualization
  %(prog)s --test                   Run audio test (test tones in each quadrant)
  %(prog)s --list-devices           List available audio devices

Press Ctrl+C to stop the simulation.
        """
    )

    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )

    parser.add_argument(
        '--visualize',
        action='store_true',
        help='Enable real-time visualization of rooster positions'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Run audio system test with test tones'
    )

    parser.add_argument(
        '--list-devices',
        action='store_true',
        help='List available audio output devices'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # List audio devices
    if args.list_devices:
        try:
            import sounddevice as sd
            print("Available audio output devices:")
            print(sd.query_devices())
        except Exception as e:
            print(f"Error querying audio devices: {e}")
        return 0

    # Check if config file exists
    if not os.path.exists(args.config):
        print(f"Error: Configuration file '{args.config}' not found.")
        print("\nPlease create a configuration file or use the default config.yaml")
        return 1

    # Run audio test
    if args.test:
        print("Running audio system test...")
        print("You should hear test tones in each quadrant of your surround system.\n")
        run_audio_test(args.config)
        return 0

    # Run main simulation
    try:
        simulator = RoosterSimulator(args.config, enable_visualization=args.visualize)
        simulator.print_rooster_positions()
        print()
        simulator.run()
        return 0

    except KeyboardInterrupt:
        print("\nSimulation interrupted by user.")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def run_audio_test(config_path: str):
    """Run a simple audio test to verify 5.1 setup."""
    import time
    import yaml
    from audio_system import AudioSystem

    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    audio = AudioSystem(config)
    audio.start_stream()

    quadrant_names = [
        "Front Right (Quadrant 0)",
        "Rear Right (Quadrant 1)",
        "Rear Left (Quadrant 2)",
        "Front Left (Quadrant 3)"
    ]

    try:
        print("Playing test tones in each quadrant...")
        print("(Press Ctrl+C to stop)\n")

        for i, name in enumerate(quadrant_names):
            print(f"Playing: {name}")

            # Test at different distances
            distances = [10, 30, 70]
            for dist in distances:
                print(f"  Distance: {dist}m")
                audio.play_test_tone(quadrant=i, distance=dist)
                time.sleep(1.5)

            time.sleep(0.5)

        print("\nTest complete!")
        print("If you heard tones moving around your speakers, the system is working correctly.")

    except KeyboardInterrupt:
        print("\nTest interrupted.")

    finally:
        audio.stop_stream()


if __name__ == "__main__":
    sys.exit(main())
