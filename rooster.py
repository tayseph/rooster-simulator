import random
import math
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class Position:
    """Represents a position in 2D space using polar coordinates."""
    angle: float  # Angle in radians (0 to 2*pi)
    distance: float  # Distance from origin in meters

    def to_cartesian(self) -> Tuple[float, float]:
        """Convert polar coordinates to cartesian (x, y)."""
        x = self.distance * math.cos(self.angle)
        y = self.distance * math.sin(self.angle)
        return x, y

    def get_quadrant(self) -> int:
        """
        Get the quadrant (0-3) based on angle.
        Quadrant mapping for 5.1 surround:
        0: Front Right (0 to π/2)
        1: Rear Right (π/2 to π)
        2: Rear Left (π to 3π/2)
        3: Front Left (3π/2 to 2π)
        """
        normalized_angle = self.angle % (2 * math.pi)
        quadrant = int(normalized_angle / (math.pi / 2))
        return quadrant % 4

    def distance_to(self, other: 'Position') -> float:
        """Calculate distance to another position."""
        x1, y1 = self.to_cartesian()
        x2, y2 = other.to_cartesian()
        return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)


class Rooster:
    """Represents a single rooster in the simulation."""

    def __init__(self, rooster_id: int, config: dict, max_radius: float, available_calls: list):
        self.id = rooster_id
        self.config = config
        self.max_radius = max_radius
        self.available_calls = available_calls

        # Initialize random position
        self.position = self._random_position()

        # Movement state
        self.last_move_time = 0.0
        self.next_move_check = self._calculate_next_check()

        # Movement personality - curiosity/roaming tendency
        curiosity_config = config['movement'].get('curiosity', {'min': 0.5, 'max': 1.5})
        self.curiosity = random.uniform(curiosity_config['min'], curiosity_config['max'])

        # Calling state
        self.last_call_time = 0.0
        self.next_call_check = self._calculate_next_check()
        self.is_calling = False
        self.call_start_time = 0.0
        self.call_duration = 2.0  # Assume rooster calls last ~2 seconds

        # Call preference (stickiness)
        self.is_sticky = random.random() < config['calls']['stickiness']['percentage_sticky_roosters']
        self.preferred_call = None
        if self.is_sticky:
            # Sticky roosters might prefer non-default calls
            if random.random() < config['calls']['stickiness']['alternate_call_chance']:
                self.preferred_call = self._choose_call()
            else:
                self.preferred_call = config['calls']['default_call']

    def _random_position(self) -> Position:
        """Generate a random position within the simulation area."""
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, self.max_radius)
        return Position(angle, distance)

    def _calculate_next_check(self) -> float:
        """Calculate next check time with randomization."""
        base_time = self.config['time_unit']
        randomization = self.config['time_randomization']
        variation = random.uniform(-randomization, randomization)
        return base_time * (1 + variation)

    def _choose_call(self) -> str:
        """Choose which call sound to use."""
        if not self.available_calls:
            return self.config['calls']['default_call']

        # Sticky roosters prefer their chosen call
        if self.is_sticky and self.preferred_call:
            # Small chance to revert to default or change
            if random.random() < self.config['calls']['stickiness']['revert_to_default_chance']:
                return self.config['calls']['default_call']
            else:
                return self.preferred_call

        # Non-sticky or first-time choice
        if random.random() < self.config['calls']['variation_probability']:
            return random.choice(self.available_calls)
        else:
            return self.config['calls']['default_call']

    def should_move(self, current_time: float) -> bool:
        """
        Determine if the rooster should move at this time.
        Takes into account the rooster's curiosity personality trait.
        """
        if current_time < self.next_move_check:
            return False

        # Update next check time
        self.next_move_check = current_time + self._calculate_next_check()

        # Apply curiosity multiplier to chance_to_move
        # High curiosity (>1.0) = more likely to move
        # Low curiosity (<1.0) = more sedentary
        adjusted_chance = self.config['movement']['chance_to_move'] * self.curiosity
        adjusted_chance = min(1.0, adjusted_chance)  # Cap at 100%

        # Check movement probability with curiosity adjustment
        if random.random() > adjusted_chance:
            return False

        if random.random() < self.config['movement']['frequency']:
            return True

        return False

    def move(self):
        """Move the rooster to a new position."""
        # Calculate actual movement distance (how far the rooster walks)
        min_dist = self.config['movement']['distance_min']
        max_dist = self.config['movement']['distance_max']
        move_distance = random.uniform(min_dist, max_dist)

        # Get current cartesian position
        x, y = self.position.to_cartesian()

        # Pick a random direction to walk (0 to 360 degrees)
        walk_direction = random.uniform(0, 2 * math.pi)

        # Calculate new position by walking in that direction
        new_x = x + move_distance * math.cos(walk_direction)
        new_y = y + move_distance * math.sin(walk_direction)

        # Convert back to polar coordinates
        new_distance = math.sqrt(new_x**2 + new_y**2)
        new_angle = math.atan2(new_y, new_x)

        # Keep within max radius boundary
        if new_distance > self.max_radius:
            # Scale back to boundary
            scale = self.max_radius / new_distance
            new_x *= scale
            new_y *= scale
            new_distance = self.max_radius
            new_angle = math.atan2(new_y, new_x)

        # Ensure angle is positive (0 to 2π)
        if new_angle < 0:
            new_angle += 2 * math.pi

        self.position = Position(new_angle, new_distance)

    def should_call(self, current_time: float, nearby_roosters: list = None,
                    time_of_day_multiplier: float = 1.0) -> bool:
        """
        Determine if the rooster should call at this time.
        Takes into account proximity to other calling roosters and time of day.
        """
        if current_time < self.next_call_check:
            return False

        # Update next check time
        self.next_call_check = current_time + self._calculate_next_check()

        # Check for proximity response to nearby calling roosters
        if nearby_roosters:
            reply_likelihood = self.config['calling']['proximity_response']['reply_likelihood']
            randomization = self.config['calling']['proximity_response']['randomization']

            # Add randomization to reply likelihood
            adjusted_likelihood = reply_likelihood * (1 + random.uniform(-randomization, randomization))
            adjusted_likelihood = max(0, min(1, adjusted_likelihood))

            if random.random() < adjusted_likelihood:
                return True

        # Base calling frequency adjusted by time of day
        adjusted_frequency = self.config['calling']['frequency'] * time_of_day_multiplier
        # Cap at 1.0 to keep it as a valid probability
        adjusted_frequency = min(1.0, adjusted_frequency)

        if random.random() < adjusted_frequency:
            return True

        return False

    def start_call(self, current_time: float) -> str:
        """Start a call and return the call sound filename."""
        self.is_calling = True
        self.call_start_time = current_time
        return self._choose_call()

    def update_calling_state(self, current_time: float):
        """Update whether the rooster is still calling based on elapsed time."""
        if self.is_calling:
            elapsed = current_time - self.call_start_time
            if elapsed > self.call_duration:
                self.is_calling = False

    def get_volume_for_distance(self) -> float:
        """Calculate volume based on distance from listener."""
        min_dist = self.config['audio']['volume']['min_distance']
        max_dist = self.config['audio']['volume']['max_distance']
        min_vol = self.config['audio']['volume']['min_volume']
        max_vol = self.config['audio']['volume']['max_volume']

        # Linear interpolation based on distance
        if self.position.distance <= min_dist:
            return max_vol
        elif self.position.distance >= max_dist:
            return min_vol
        else:
            # Linear falloff
            ratio = (self.position.distance - min_dist) / (max_dist - min_dist)
            return max_vol - (ratio * (max_vol - min_vol))

    def get_speaker_volumes(self) -> Tuple[float, float, float, float, float, float]:
        """
        Calculate volume for each speaker in 5.1 setup.
        Returns tuple: (FL, FR, C, LFE, RL, RR)
        FL=Front Left, FR=Front Right, C=Center, LFE=Subwoofer, RL=Rear Left, RR=Rear Right
        """
        base_volume = self.get_volume_for_distance()
        quadrant = self.position.get_quadrant()

        # Initialize all channels to zero
        fl = fr = c = lfe = rl = rr = 0.0

        # Assign volume to primary speakers based on quadrant
        # We'll also add some bleed to adjacent speakers for smoother transitions
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

        # Add slight low frequency to subwoofer for all calls
        lfe = base_volume * 0.15

        return (fl, fr, c, lfe, rl, rr)
