import matplotlib
# Use TkAgg backend for better compatibility on macOS
try:
    matplotlib.use('TkAgg')
except:
    pass  # If TkAgg not available, use default

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from typing import List
from rooster import Rooster


class RoosterVisualizer:
    """Real-time visualization of rooster positions."""

    def __init__(self, max_radius: float, num_roosters: int):
        self.max_radius = max_radius
        self.num_roosters = num_roosters

        # Set up the plot
        plt.ion()  # Interactive mode
        self.fig, self.ax = plt.subplots(figsize=(10, 10))

        # Set window title (method varies by backend)
        try:
            self.fig.canvas.manager.set_window_title('Rooster Simulator - Spatial View')
        except:
            self.fig.canvas.set_window_title('Rooster Simulator - Spatial View')

        # Initialize plot elements
        self._setup_plot()

        # Store plot objects for updating
        self.rooster_scatter = None
        self.rooster_texts = []
        self.calling_indicators = []

        # Force the window to appear
        plt.show(block=False)
        plt.pause(0.001)

    def _setup_plot(self):
        """Set up the initial plot layout."""
        self.ax.clear()
        self.ax.set_xlim(-self.max_radius * 1.1, self.max_radius * 1.1)
        self.ax.set_ylim(-self.max_radius * 1.1, self.max_radius * 1.1)
        self.ax.set_aspect('equal')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlabel('Distance (meters)', fontsize=10)
        self.ax.set_ylabel('Distance (meters)', fontsize=10)
        self.ax.set_title('Hawaiian Rooster Simulator - Spatial View', fontsize=12, fontweight='bold')

        # Draw listener at center
        self.ax.plot(0, 0, 'r*', markersize=20, label='Listener (You)', zorder=10)

        # Draw quadrant boundaries
        self.ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5, linewidth=1)
        self.ax.axvline(x=0, color='gray', linestyle='--', alpha=0.5, linewidth=1)

        # Draw radius circles
        for radius in [self.max_radius * 0.25, self.max_radius * 0.5, self.max_radius * 0.75, self.max_radius]:
            circle = plt.Circle((0, 0), radius, fill=False, color='gray',
                              linestyle=':', alpha=0.3, linewidth=1)
            self.ax.add_patch(circle)

        # Label quadrants
        offset = self.max_radius * 0.85
        self.ax.text(offset, offset, 'Q3: Front Left\n(FL)',
                    ha='center', va='center', fontsize=9, alpha=0.6,
                    bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
        self.ax.text(offset, -offset, 'Q0: Front Right\n(FR)',
                    ha='center', va='center', fontsize=9, alpha=0.6,
                    bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.3))
        self.ax.text(-offset, -offset, 'Q1: Rear Right\n(RR)',
                    ha='center', va='center', fontsize=9, alpha=0.6,
                    bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.3))
        self.ax.text(-offset, offset, 'Q2: Rear Left\n(RL)',
                    ha='center', va='center', fontsize=9, alpha=0.6,
                    bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.3))

        # Add legend
        self.ax.legend(loc='upper right', fontsize=9)

    def update(self, roosters: List[Rooster], sim_time_str: str = ""):
        """Update the visualization with current rooster positions."""
        # Clear previous rooster markers and text
        if self.rooster_scatter:
            self.rooster_scatter.remove()
        for text in self.rooster_texts:
            text.remove()
        for indicator in self.calling_indicators:
            indicator.remove()

        self.rooster_texts = []
        self.calling_indicators = []

        # Collect rooster data
        x_coords = []
        y_coords = []
        colors = []
        sizes = []

        for rooster in roosters:
            x, y = rooster.position.to_cartesian()
            x_coords.append(x)
            y_coords.append(y)

            # Color based on calling state
            if rooster.is_calling:
                colors.append('red')
                sizes.append(200)
            else:
                colors.append('blue')
                sizes.append(100)

        # Plot roosters
        self.rooster_scatter = self.ax.scatter(x_coords, y_coords, c=colors, s=sizes,
                                              alpha=0.7, edgecolors='black', linewidths=1.5,
                                              zorder=5)

        # Add rooster ID labels
        for i, rooster in enumerate(roosters):
            x, y = rooster.position.to_cartesian()

            # Label with ID
            text = self.ax.text(x, y, str(rooster.id), ha='center', va='center',
                              fontsize=10, fontweight='bold', color='white', zorder=6)
            self.rooster_texts.append(text)

            # Add calling indicator (ring around calling roosters)
            if rooster.is_calling:
                circle = plt.Circle((x, y), self.max_radius * 0.03, fill=False,
                                  color='red', linestyle='-', linewidth=2, alpha=0.8, zorder=4)
                self.ax.add_patch(circle)
                self.calling_indicators.append(circle)

        # Update title with simulation time
        if sim_time_str:
            self.ax.set_title(f'Hawaiian Rooster Simulator - Spatial View | Time: {sim_time_str}',
                            fontsize=12, fontweight='bold')

        # Refresh the plot
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()
        plt.pause(0.001)  # Small pause to ensure window updates

    def close(self):
        """Close the visualization window."""
        plt.close(self.fig)


class MinimalVisualizer:
    """Minimal text-based visualization for when matplotlib is not available."""

    def __init__(self, max_radius: float, num_roosters: int):
        self.max_radius = max_radius
        self.num_roosters = num_roosters
        print("\n" + "="*60)
        print("TEXT-BASED SPATIAL VIEW")
        print("="*60)

    def update(self, roosters: List[Rooster], sim_time_str: str = ""):
        """Print a simple text representation."""
        # This is a fallback - we won't call it frequently to avoid spam
        pass

    def close(self):
        """No-op for text mode."""
        pass
