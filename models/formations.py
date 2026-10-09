"""
Formation detection and analysis models.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from sklearn.cluster import KMeans
from .utils.constants import PITCH_LENGTH, PITCH_WIDTH


class FormationDetector:
    """
    Detects and analyzes team formations from player positions.
    """

    def __init__(self, pitch_length: float = PITCH_LENGTH, pitch_width: float = PITCH_WIDTH):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width

    def detect_formation_kmeans(self,
                              positions: pd.DataFrame,
                              n_lines: int = 3) -> Dict:
        """
        Detect formation using K-means clustering to identify lines.

        Args:
            positions: DataFrame with columns ['player_id', 'x', 'y', 'timestamp']
                      (x, y in meters or normalized 0-1)
            n_lines: Number of lines to detect (typically 3: defense, midfield, attack)

        Returns:
            Dictionary with formation information.
        """
        # We'll use the average position of each player over time
        if 'timestamp' in positions.columns:
            avg_positions = positions.groupby('player_id')[['x', 'y']].mean().reset_index()
        else:
            avg_positions = positions[['player_id', 'x', 'y']].copy()

        # Normalize positions to 0-1 if they aren't already
        pos = avg_positions.copy()
        if pos['x'].max() > 1 or pos['y'].max() > 1:
            pos['x_norm'] = pos['x'] / self.pitch_length
            pos['y_norm'] = pos['y'] / self.pitch_width
        else:
            pos['x_norm'] = pos['x']
            pos['y_norm'] = pos['y']

        # We'll cluster based on y position (vertical) to find lines
        # For formation, we primarily care about the vertical stratification
        Y = pos[['y_norm']].values

        # Use KMeans to find n_lines clusters
        kmeans = KMeans(n_clusters=n_lines, random_state=42, n_init=10)
        pos['line'] = kmeans.fit_predict(Y)

        # Sort clusters by their centroid y position (from own goal to opponent goal)
        line_centroids = pos.groupby('line')['y_norm'].mean().sort_values()
        line_mapping = {old_label: new_label for new_label, old_label in
                       enumerate(line_centroids.index)}
        pos['line'] = pos['line'].map(line_mapping)

        # Count players in each line
        line_counts = pos['line'].value_counts().sort_index()

        # Formation name (e.g., 4-3-3)
        formation_name = '-'.join([str(line_counts.get(i, 0)) for i in range(n_lines)])

        # Calculate width and depth for each line
        line_stats = {}
        for line_num in range(n_lines):
            line_data = pos[pos['line'] == line_num]
            if len(line_data) > 0:
                width = (line_data['x_norm'].max() - line_data['x_norm'].min()) * 100
                # Depth within the line (vertical spread)
                depth_within_line = (line_data['y_norm'].max() - line_data['y_norm'].min()) * 100
            else:
                width = 0.0
                depth_within_line = 0.0

            line_stats[line_num] = {
                'player_count': line_counts.get(line_num, 0),
                'width': width,
                'depth_within_line': depth_within_line,
                'avg_x': line_data['x_norm'].mean() if len(line_data) > 0 else 0.5,
                'avg_y': line_data['y_norm'].mean() if len(line_data) > 0 else 0.0
            }

        # Overall team width and depth
        overall_width = (pos['x_norm'].max() - pos['x_norm'].min()) * 100
        overall_depth = (pos['y_norm'].max() - pos['y_norm'].min()) * 100

        # Create positions dictionary
        positions_dict = {
            row['player_id']: (row['x_norm'], row['y_norm']) for _, row in pos.iterrows()
        }

        return {
            'formation_name': formation_name,
            'n_lines': n_lines,
            'line_counts': line_counts.to_dict(),
            'line_stats': line_stats,
            'overall_width': overall_width,
            'overall_depth': overall_depth,
            'positions': positions_dict,
            'formation_quality': self._calculate_formation_quality(pos, line_counts)
        }

    def _calculate_formation_quality(self,
                                   positions: pd.DataFrame,
                                   line_counts: pd.Series) -> float:
        """
        Calculate a quality metric for the formation (how well-defined the lines are).

        Args:
            positions: DataFrame with player positions and line assignments.
            line_counts: Series with player counts per line.

        Returns:
            Quality score between 0 and 1 (higher is better defined lines).
        """
        # We'll use the silhouette score concept: how well each player fits
        # into their assigned line vs. neighboring lines

        if len(positions) < 2:
            return 0.0

        # For each player, calculate distance to their line centroid
        # and to the nearest other line centroid
        line_centroids = positions.groupby('line')[['x_norm', 'y_norm']].mean()

        def min_distance_to_other_lines(player_idx):
            player_row = positions.iloc[player_idx]
            player_line = player_row['line']
            player_pos = np.array([player_row['x_norm'], player_row['y_norm']])

            # Distance to own line centroid
            own_centroid = line_centroids.loc[player_line].values
            dist_to_own = np.linalg.norm(player_pos - own_centroid)

            # Distance to nearest other line centroid
            other_lines = [l for l in line_centroids.index if l != player_line]
            if not other_lines:
                return dist_to_own  # Only one line

            min_dist_to_other = float('inf')
            for other_line in other_lines:
                other_centroid = line_centroids.loc[other_line].values
                dist_to_other = np.linalg.norm(player_pos - other_centroid)
                if dist_to_other < min_dist_to_other:
                    min_dist_to_other = dist_to_other

            # Quality: how much closer to own line than to nearest other line
            # If dist_to_own << min_dist_to_other, quality is high
            if min_dist_to_other == 0:
                return 0.0
            return 1.0 - (dist_to_own / min_dist_to_other)

        # Apply to all players
        qualities = []
        for i in range(len(positions)):
            quality = min_distance_to_other_lines(i)
            qualities.append(max(0, quality))  # Ensure non-negative

        return np.mean(qualities) if qualities else 0.0

    def compare_formations(self,
                         formation1: Dict,
                         formation2: Dict) -> Dict[str, float]:
        """
        Compare two formations.

        Args:
            formation1: First formation dictionary from detect_formation_kmeans.
            formation2: Second formation dictionary.

        Returns:
            Dictionary with comparison metrics.
        """
        # Compare formation names
        same_formation = formation1['formation_name'] == formation2['formation_name']

        # Compare line counts
        line_count_diff = 0
        all_lines = set(formation1['line_counts'].keys()) | set(formation2['line_counts'].keys())
        for line in all_lines:
            count1 = formation1['line_counts'].get(line, 0)
            count2 = formation2['line_counts'].get(line, 0)
            line_count_diff += abs(count1 - count2)

        # Compare positions (average distance between corresponding players)
        # This is tricky without player matching; we'll use a simplified approach
        pos_diff = 0.0
        n_players = 0

        # We'll match by order in formation (simplified)
        pos1_items = list(formation1['positions'].items())
        pos2_items = list(formation2['positions'].items())

        # Take minimum number of players
        n_compare = min(len(pos1_items), len(pos2_items))

        for i in range(n_compare):
            _, pos1 = pos1_items[i]
            _, pos2 = pos2_items[i]
            pos_diff += np.linalg.norm(np.array(pos1) - np.array(pos2))
            n_players += 1

        avg_pos_diff = pos_diff / n_players if n_players > 0 else 0.0

        return {
            'same_formation_name': same_formation,
            'formation1_name': formation1['formation_name'],
            'formation2_name': formation2['formation_name'],
            'line_count_difference': line_count_diff,
            'average_position_difference': avg_pos_diff,
            'width_difference': abs(formation1['overall_width'] - formation2['overall_width']),
            'depth_difference': abs(formation1['overall_depth'] - formation2['overall_depth'])
        }