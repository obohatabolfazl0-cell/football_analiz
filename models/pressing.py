"""
Pressing analysis models.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from .utils.constants import PITCH_LENGTH, PITCH_WIDTH


class PressingAnalyzer:
    """
    Analyzes pressing behavior and effectiveness.
    """

    def __init__(self, pitch_length: float = PITCH_LENGTH, pitch_width: float = PITCH_WIDTH):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width

    def analyze_pressing_phases(self,
                              team_positions: pd.DataFrame,
                              opponent_positions: pd.DataFrame,
                              ball_position: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze different phases of pressing.

        Args:
            team_positions: DataFrame with team player positions
            opponent_positions: DataFrame with opponent player positions
            ball_position: DataFrame with ball positions

        Returns:
            Dictionary with pressing phase analysis.
        """
        # We'll simplify by calculating pressing intensity in different zones
        # Defensive third, middle third, attacking third

        # Normalize positions to 0-1 pitch coordinates
        team_norm = self._normalize_positions(team_positions)
        opp_norm = self._normalize_positions(opponent_positions)
        ball_norm = self._normalize_positions(ball_position)

        # Define pitch thirds (assuming y=0 is own goal, y=1 is opponent goal)
        defensive_third = (team_norm['y'] < 0.33)
        middle_third = ((team_norm['y'] >= 0.33) & (team_norm['y'] < 0.66))
        attacking_third = (team_norm['y'] >= 0.66)

        # Calculate pressing intensity in each third
        # Pressing intensity = average distance of opponents to ball in that third
        # Lower distance = more intense pressing

        results = {}

        for third_name, mask in [('defensive', defensive_third),
                                ('middle', middle_third),
                                ('attacking', attacking_third)]:
            # Get opponents in this third
            opp_in_third = opp_norm[mask]
            ball_in_third = ball_norm[mask]

            if len(opp_in_third) > 0 and len(ball_in_third) > 0:
                # Calculate average distance of opponents to ball in this third
                # We'll simplify by taking the mean position of opponents and ball in the third
                opp_mean = opp_in_third[['x', 'y']].mean().values
                ball_mean = ball_in_third[['x', 'y']].mean().values
                dist_to_ball = np.linalg.norm(opp_mean - ball_mean)

                # Normalize by pitch length for a 0-1 score (lower = more pressing)
                max_dist = np.sqrt((1/3)**2 + 1**2)  # Max distance in a third
                pressing_intensity = 1.0 - min(dist_to_ball / max_dist, 1.0)
            else:
                pressing_intensity = 0.0

            results[f'{third_name}_third_pressing'] = pressing_intensity

        # Overall pressing intensity (weighted by third importance)
        # Typically, pressing in attacking and middle thirds is more valuable
        weights = {'defensive': 0.2, 'middle': 0.3, 'attacking': 0.5}
        overall = sum(results[f'{k}_third_pressing'] * w for k, w in weights.items())
        results['overall_pressing_intensity'] = overall

        return results

    def counter_pressing_analysis(self,
                                team_positions: pd.DataFrame,
                                opponent_positions: pd.DataFrame,
                                ball_position: pd.DataFrame,
                                time_window: float = 5.0) -> Dict[str, float]:
        """
        Analyze counter-pressing effectiveness (pressing after losing possession).

        Args:
            team_positions: DataFrame with team player positions
            opponent_positions: DataFrame with opponent player positions
            ball_position: DataFrame with ball positions
            time_window: Time window (in seconds) after losing possession to analyze

        Returns:
            Dictionary with counter-pressing metrics.
        """
        # This is a simplified version; in reality, we would need to
        # detect possessions and transitions

        # For demonstration, we'll calculate how quickly the team
        # applies pressure after the ball enters their defensive third

        # Normalize positions
        team_norm = self._normalize_positions(team_positions)
        opp_norm = self._normalize_positions(opponent_positions)
        ball_norm = self._normalize_positions(ball_position)

        # Define when ball is in opponent's half (they have possession)
        ball_in_opp_half = ball_norm['y'] > 0.5

        # We would normally track possession changes, but for simplicity:
        # We'll look at moments when ball transitions from opponent half to our half
        # and see how quickly our team closes down

        # Since we don't have clear possession data in this simplified model,
        # we'll return placeholder metrics
        return {
            "counter_pressing_intensity": 0.0,  # Placeholder
            "avg_time_to_press": 0.0,           # Placeholder (seconds)
            "counter_pressing_success_rate": 0.0 # Placeholder
        }

    def pressing_passive_defensive_balance(self,
                                         team_positions: pd.DataFrame,
                                         opponent_positions: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze the balance between pressing and passive defending.

        Args:
            team_positions: DataFrame with team player positions
            opponent_positions: DataFrame with opponent player positions

        Returns:
            Dictionary with pressing vs passive defending metrics.
        """
        # Normalize positions
        team_norm = self._normalize_positions(team_positions)
        opp_norm = self._normalize_positions(opponent_positions)

        # Calculate average team position (how high up the pitch they play)
        avg_team_y = team_norm['y'].mean()
        avg_opp_y = opp_norm['y'].mean()

        # High average_y = team plays high up the pitch (more pressing)
        # Low average_y = team sits deep (more passive defending)

        # Pressing propensity: how high the team plays (0-1 scale)
        pressing_propensity = avg_team_y  # Already 0-1 if normalized

        # Compactness: how close teammates are to each other
        # We'll calculate average distance between teammates
        if len(team_norm) > 1:
            from scipy.spatial.distance import pdist
            positions = team_norm[['x', 'y']].values
            if len(positions) > 1:
                avg_dist = np.mean(pdist(positions))
                # Normalize by pitch dimensions
                max_dist = np.sqrt(1**2 + 1**2)  # Max possible distance on normalized pitch
                compactness = 1.0 - min(avg_dist / max_dist, 1.0)
            else:
                compactness = 0.0
        else:
            compactness = 0.0

        # Pressing intensity: how close team is to opponents
        if len(team_norm) > 0 and len(opp_norm) > 0:
            team_centroid = team_norm[['x', 'y']].mean().values
            opp_centroid = opp_norm[['x', 'y']].mean().values
            dist_between_teams = np.linalg.norm(team_centroid - opp_centroid)
            # Normalize and invert (closer = more pressing)
            max_dist = np.sqrt(1**2 + 1**2)
            pressing_intensity = 1.0 - min(dist_between_teams / max_dist, 1.0)
        else:
            pressing_intensity = 0.0

        return {
            "pressing_propensity": pressing_propensity,
            "defensive_depth": 1.0 - avg_team_y,  # How deep they sit (0 = high, 1 = deep)
            "team_compactness": compactness,
            "pressing_intensity": pressing_intensity,
            "pressing_passive_ratio": pressing_propensity / (1.0 - avg_team_y + 0.001)  # Avoid division by zero
        }

    def _normalize_positions(self, positions: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize positions to 0-1 pitch coordinates.

        Args:
            positions: DataFrame with columns ['x', 'y'] (in meters or already normalized)

        Returns:
            DataFrame with normalized positions (0-1).
        """
        pos = positions.copy()
        # Check if already normalized (max <= 1)
        if pos['x'].max() <= 1.0 and pos['y'].max() <= 1.0:
            # Already normalized
            return pos
        else:
            # Convert from meters to 0-1
            pos['x_norm'] = pos['x'] / self.pitch_length
            pos['y_norm'] = pos['y'] / self.pitch_width
            return pos[['x_norm', 'y_norm']].rename(columns={'x_norm': 'x', 'y_norm': 'y'})