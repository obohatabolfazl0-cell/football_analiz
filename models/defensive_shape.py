"""
Defensive shape analysis models.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from scipy.spatial import ConvexHull
from .utils.constants import PITCH_LENGTH, PITCH_WIDTH


class DefensiveShapeAnalyzer:
    """
    Analyzes defensive shape, compactness, and line behavior.
    """

    def __init__(self, pitch_length: float = PITCH_LENGTH, pitch_width: float = PITCH_WIDTH):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width

    def analyze_defensive_line(self,
                             defensive_positions: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze the defensive line shape and properties.

        Args:
            defensive_positions: DataFrame with columns ['player_id', 'x', 'y', 'timestamp']
                               for defensive players (x, y in meters or normalized 0-1)

        Returns:
            Dictionary with defensive line metrics.
        """
        if len(defensive_positions) == 0:
            return self._empty_defensive_result()

        # Normalize positions to 0-1 if needed
        pos = defensive_positions.copy()
        if pos['x'].max() > 1 or pos['y'].max() > 1:
            pos['x_norm'] = pos['x'] / self.pitch_length
            pos['y_norm'] = pos['y'] / self.pitch_width
        else:
            pos['x_norm'] = pos['x']
            pos['y_norm'] = pos['y']

        # We'll use the average position of each defensive player over time
        if 'timestamp' in pos.columns:
            avg_pos = pos.groupby('player_id')[['x_norm', 'y_norm']].mean().reset_index()
        else:
            avg_pos = pos[['player_id', 'x_norm', 'y_norm']].copy()

        if len(avg_pos) == 0:
            return self._empty_defensive_result()

        # Sort by y position (assuming y=0 is own goal, y increases towards opponent goal)
        # Defenders should have lower y values (deeper position)
        avg_pos = avg_pos.sort_values('y_norm')

        # Calculate defensive line height (average y position of defenders)
        line_height = avg_pos['y_norm'].mean()

        # Calculate defensive line width (spread in x direction)
        line_width = avg_pos['x_norm'].max() - avg_pos['x_norm'].min()

        # Calculate line flatness (how straight the line is - std of y positions)
        line_flatness = avg_pos['y_norm'].std()

        # Calculate line depth (how deep the deepest defender is)
        line_depth = avg_pos['y_norm'].min()

        # Calculate compactness: how close defenders are to each other
        # We'll use the average distance between defenders
        if len(avg_pos) > 1:
            from scipy.spatial.distance import pdist
            positions = avg_pos[['x_norm', 'y_norm']].values
            avg_dist = np.mean(pdist(positions))
            # Normalize by pitch dimensions
            max_dist = np.sqrt(1**2 + 1**2)  # Max possible distance on normalized pitch
            compactness = 1.0 - min(avg_dist / max_dist, 1.0)
        else:
            compactness = 0.0

        # Calculate defensive line angle (are they flat or diagonal?)
        # We'll fit a line to the defenders and see the slope
        if len(avg_pos) >= 2:
            x = avg_pos['x_norm'].values
            y = avg_pos['y_norm'].values
            # Simple linear regression
            A = np.vstack([x, np.ones(len(x))]).T
            slope, intercept = np.linalg.lstsq(A, y, rcond=None)[0]
            line_angle = np.arctan(slope) * 180 / np.pi  # Convert to degrees
        else:
            line_angle = 0.0

        # Calculate spaces between lines (if we had midfield and attack data)
        # For now, we'll just return what we have

        return {
            "defensive_line_height": line_height,
            "defensive_line_width": line_width * 100,  # as percentage of pitch width
            "defensive_line_flatness": line_flatness,
            "defensive_line_depth": line_depth,
            "defensive_line_angle": line_angle,  # degrees from horizontal
            "defensive_compactness": compactness,
            "number_of_defenders": len(avg_pos),
            "line_length": line_width * 100  # Same as width for now
        }

    def defensive_third_control(self,
                              defensive_positions: pd.DataFrame,
                              opponent_positions: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze control of the defensive third.

        Args:
            defensive_positions: DataFrame with team defensive player positions
            opponent_positions: DataFrame with opponent player positions

        Returns:
            Dictionary with defensive third control metrics.
        """
        # Normalize positions
        def_norm = self._normalize_positions(defensive_positions)
        opp_norm = self._normalize_positions(opponent_positions)

        # Define defensive third (assuming y=0 is own goal, y=1 is opponent goal)
        defensive_third_mask = def_norm['y_norm'] < 0.33 if 'y_norm' in def_norm.columns else \
                              (def_norm['y'] / self.pitch_length) < 0.33

        if 'y_norm' not in def_norm.columns:
            def_norm['y_norm'] = def_norm['y'] / self.pitch_length
            opp_norm['y_norm'] = opp_norm['y'] / self.pitch_length

        defensive_third_mask = def_norm['y_norm'] < 0.33
        opp_in_defensive_third = opp_norm[opp_norm['y_norm'] < 0.33]

        # Calculate occupancy of defensive third by team
        team_in_def_third = def_norm[defensive_third_mask]
        opp_in_def_third = opp_norm[opp_norm['y_norm'] < 0.33]

        # Simple metric: ratio of team to opponent players in defensive third
        team_count = len(team_in_def_third)
        opp_count = len(opp_in_def_third)
        total_count = team_count + opp_count

        if total_count > 0:
            defensive_control = team_count / total_count
        else:
            defensive_control = 0.5  # Neutral if no players in third

        # Calculate space control: average distance to opponents in defensive third
        if len(team_in_def_third) > 0 and len(opp_in_def_third) > 0:
            # We'll simplify: distance between centroids
            team_centroid = team_in_def_third[['x_norm', 'y_norm']].mean().values
            opp_centroid = opp_in_def_third[['x_norm', 'y_norm']].mean().values
            avg_distance = np.linalg.norm(team_centroid - opp_centroid)
            # Normalize and invert (closer = better control)
            max_dist = np.sqrt((0.33)**2 + 1**2)  # Max distance in defensive third
            space_control = 1.0 - min(avg_distance / max_dist, 1.0)
        else:
            space_control = 0.0 if len(opp_in_def_third) > 0 else 1.0

        return {
            "defensive_third_control": defensive_control,
            "team_players_in_def_third": team_count,
            "opp_players_in_def_third": opp_count,
            "defensive_third_space_control": space_control,
            "defensive_third_occupancy_ratio": team_count / (team_count + opp_count + 0.001)
        }

    def pressing_resistance(self,
                          defensive_positions: pd.DataFrame,
                          opponent_positions: pd.DataFrame,
                          ball_position: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze how well the defensive line resists pressing.

        Args:
            defensive_positions: DataFrame with team defensive player positions
            opponent_positions: DataFrame with opponent player positions (pressers)
            ball_position: DataFrame with ball positions

        Returns:
            Dictionary with pressing resistance metrics.
        """
        # Normalize positions
        def_norm = self._normalize_positions(defensive_positions)
        opp_norm = self._normalize_positions(opponent_positions)
        ball_norm = self._normalize_positions(ball_position)

        # We'll look at the distance between defensive line and pressing opponents
        # when the ball is in defensive team's possession

        # For simplicity, we'll calculate average distance from defenders to nearest presser
        if len(def_norm) > 0 and len(opp_norm) > 0:
            from scipy.spatial.distance import cdist
            def_positions = def_norm[['x_norm', 'y_norm']].values
            opp_positions = opp_norm[['x_norm', 'y_norm']].values

            # Distance from each defender to nearest opponent
            distances = cdist(def_positions, opp_positions)
            min_distances = np.min(distances, axis=1)
            avg_min_distance = np.mean(min_distances)

            # Normalize and invert (smaller distance = more pressure = less resistance)
            max_dist = np.sqrt(1**2 + 1**2)
            pressure_level = min(avg_min_distance / max_dist, 1.0)
            pressing_resistance = 1.0 - pressure_level  # Higher = better resistance
        else:
            pressing_resistance = 0.0
            avg_min_distance = 0.0

        # Also look at vertical compactness under pressure
        # How much the defensive line drops when pressed
        if len(def_norm) > 0:
            line_height = def_norm['y_norm'].mean()
        else:
            line_height = 0.5

        return {
            "pressing_resistance": pressing_resistance,
            "avg_defender_to_presser_distance": avg_min_distance,
            "defensive_line_height_under_pressure": line_height,
            "pressing_resistance_rating": "High" if pressing_resistance > 0.7 else
                                        "Medium" if pressing_resistance > 0.4 else "Low"
        }

    def _empty_defensive_result(self) -> Dict[str, float]:
        """Return empty result for when no defensive data is available."""
        return {
            "defensive_line_height": 0.0,
            "defensive_line_width": 0.0,
            "defensive_line_flatness": 0.0,
            "defensive_line_depth": 0.0,
            "defensive_line_angle": 0.0,
            "defensive_compactness": 0.0,
            "number_of_defenders": 0,
            "line_length": 0.0
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
        if 'x' in pos.columns and 'y' in pos.columns:
            if pos['x'].max() <= 1.0 and pos['y'].max() <= 1.0:
                # Already normalized
                pos['x_norm'] = pos['x']
                pos['y_norm'] = pos['y']
                return pos[['x_norm', 'y_norm']]
            else:
                # Convert from meters to 0-1
                pos['x_norm'] = pos['x'] / self.pitch_length
                pos['y_norm'] = pos['y'] / self.pitch_width
                return pos[['x_norm', 'y_norm']]
        else:
            # If columns don't exist, return empty dataframe with expected columns
            return pd.DataFrame(columns=['x_norm', 'y_norm'])