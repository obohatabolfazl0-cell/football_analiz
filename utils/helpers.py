"""
Helper functions for football analysis.
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from .constants import PITCH_LENGTH, PITCH_WIDTH


def normalize_positions(positions: pd.DataFrame,
                       length: float = PITCH_LENGTH,
                       width: float = PITCH_WIDTH) -> pd.DataFrame:
    """
    Normalize positions to 0-1 pitch coordinates.

    Args:
        positions: DataFrame with columns ['x', 'y'] (in meters or already normalized)
        length: Pitch length in meters (default from constants)
        width: Pitch width in meters (default from constants)

    Returns:
        DataFrame with normalized positions (0-1) and columns ['x_norm', 'y_norm'].
    """
    pos = positions.copy()

    # Check if already normalized (max <= 1)
    if pos['x'].max() <= 1.0 and pos['y'].max() <= 1.0:
        # Already normalized
        pos['x_norm'] = pos['x']
        pos['y_norm'] = pos['y']
        return pos[['x_norm', 'y_norm']]
    else:
        # Convert from meters to 0-1
        pos['x_norm'] = pos['x'] / length
        pos['y_norm'] = pos['y'] / width
        return pos[['x_norm', 'y_norm']]


def calculate_distance(pos1: Tuple[float, float],
                      pos2: Tuple[float, float]) -> float:
    """
    Calculate Euclidean distance between two points.

    Args:
        pos1: Tuple of (x, y) coordinates
        pos2: Tuple of (x, y) coordinates

    Returns:
        Euclidean distance between the points.
    """
    return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)


def calculate_speed(positions: pd.DataFrame,
                   time_column: str = 'timestamp') -> pd.DataFrame:
    """
    Calculate speed from tracking data.

    Args:
        positions: DataFrame with columns ['player_id', 'x', 'y', 'timestamp']
                  (x, y in meters or normalized)
        time_column: Name of the timestamp column

    Returns:
        DataFrame with added speed column.
    """
    # We assume the data is sorted by player_id and timestamp
    positions = positions.sort_values(['player_id', time_column])

    # Compute time differences
    positions['dt'] = positions.groupby('player_id')[time_column].diff()

    # Compute differences in x and y
    positions['dx'] = positions.groupby('player_id')['x'].diff()
    positions['dy'] = positions.groupby('player_id')['y'].diff()

    # Speed = distance / time
    positions['speed'] = np.sqrt(positions['dx']**2 + positions['dy']**2) / positions['dt']
    # Replace infinite or NaN due to zero time diff
    positions['speed'] = positions['speed'].replace([np.inf, -np.inf], np.nan).fillna(0)

    return positions


def calculate_acceleration(positions: pd.DataFrame,
                          time_column: str = 'timestamp') -> pd.DataFrame:
    """
    Calculate acceleration from tracking data.

    Args:
        positions: DataFrame with columns ['player_id', 'x', 'y', 'timestamp', 'speed']
                  (x, y in meters or normalized, speed in m/s or normalized/s)
        time_column: Name of the timestamp column

    Returns:
        DataFrame with added acceleration column.
    """
    # We assume the data is sorted by player_id and timestamp
    positions = positions.sort_values(['player_id', time_column])

    # Compute time differences
    positions['dt'] = positions.groupby('player_id')[time_column].diff()

    # Compute differences in speed
    positions['dspeed'] = positions.groupby('player_id')['speed'].diff()

    # Acceleration = change in speed / time
    positions['acceleration'] = positions['dspeed'] / positions['dt']
    # Replace infinite or NaN due to zero time diff
    positions['acceleration'] = positions['acceleration'].replace([np.inf, -np.inf], np.nan).fillna(0)

    return positions


def zone_possession(positions: pd.DataFrame,
                   zone_def: dict) -> float:
    """
    Calculate the percentage of time players spend in a specific zone.

    Args:
        positions: DataFrame with columns ['x_norm', 'y_norm'] (normalized 0-1)
        zone_def: Dictionary defining the zone with keys:
                 'x_min', 'x_max', 'y_min', 'y_max' (all 0-1)

    Returns:
        Percentage of time spent in the zone (0-100).
    """
    if len(positions) == 0:
        return 0.0

    # Check if positions are normalized
    x_col = 'x_norm' if 'x_norm' in positions.columns else 'x'
    y_col = 'y_norm' if 'y_norm' in positions.columns else 'y'

    # Check if we need to normalize
    if positions[x_col].max() > 1.0 or positions[y_col].max() > 1.0:
        # Need to normalize first
        from .constants import PITCH_LENGTH, PITCH_WIDTH
        norm_pos = normalize_positions(positions, PITCH_LENGTH, PITCH_WIDTH)
        x_col, y_col = 'x_norm', 'y_norm'
        positions_for_check = norm_pos
    else:
        positions_for_check = positions

    # Check if players are in zone
    in_zone = (
        (positions_for_check[x_col] >= zone_def['x_min']) &
        (positions_for_check[x_col] <= zone_def['x_max']) &
        (positions_for_check[y_col] >= zone_def['y_min']) &
        (positions_for_check[y_col] <= zone_def['y_max'])
    )

    return (in_zone.sum() / len(positions_for_check)) * 100


def formation_symmetry(positions: pd.DataFrame) -> float:
    """
    Calculate how symmetric a formation is left-right.

    Args:
        positions: DataFrame with columns ['x_norm', 'y_norm'] (normalized 0-1)
                  representing player positions

    Returns:
        Symmetry score between 0 and 1 (1 is perfectly symmetric).
    """
    if len(positions) == 0:
        return 0.0

    # Check if positions are normalized
    x_col = 'x_norm' if 'x_norm' in positions.columns else 'x'
    y_col = 'y_norm' if 'y_norm' in positions.columns else 'y'

    # Normalize if needed
    if positions[x_col].max() > 1.0 or positions[y_col].max() > 1.0:
        from .constants import PITCH_LENGTH, PITCH_WIDTH
        positions = normalize_positions(positions, PITCH_LENGTH, PITCH_WIDTH)
        x_col, y_col = 'x_norm', 'y_norm'

    # Calculate centroid
    centroid_x = positions[x_col].mean()
    centroid_y = positions[y_col].mean()

    # For perfect symmetry, we'd expect the formation to be mirrored around x=0.5
    # We'll calculate how close the average x position is to 0.5
    # and how balanced the left and right sides are

    # Deviation from center
    center_deviation = abs(centroid_x - 0.5)

    # Left-right balance: compare number of players on each side
    left_count = (positions[x_col] < 0.5).sum()
    right_count = (positions[x_col] > 0.5).sum()
    total = len(positions)

    if total > 0:
        left_ratio = left_count / total
        right_ratio = right_count / total
        # Perfect balance would be 0.5 each
        balance_score = 1.0 - abs(left_ratio - 0.5) * 2  # 0 to 1 scale
    else:
        balance_score = 0.0

    # Combine metrics: we want low center deviation and high balance
    symmetry = (1.0 - min(center_deviation * 2, 1.0)) * balance_score

    return max(0.0, min(1.0, symmetry))  # Clamp to 0-1


def passing_network_visualization_data(passes: pd.DataFrame,
                                     team_players: List[str]) -> Tuple[List[Tuple[float, float]],
                                                                     List[Tuple[int, int]],
                                                                     List[float]]:
    """
    Prepare data for passing network visualization.

    Args:
        passes: DataFrame with pass events (from_player, to_player,
               start_x, start_y, end_x, end_y, success).
        team_players: List of player IDs for the team.

    Returns:
        Tuple of (node_positions, edges, edge_weights) for visualization.
    """
    # Filter to team passes only
    team_passes = passes[
        passes['from_player'].isin(team_players) &
        passes['to_player'].isin(team_players)
    ].copy()

    if len(team_passes) == 0:
        return [], [], []

    # Calculate average position for each player
    player_positions = {}
    for player in team_players:
        # Find all passes involving this player
        player_passes = team_passes[
            (team_passes['from_player'] == player) |
            (team_passes['to_player'] == player)
        ]

        if len(player_passes) > 0:
            # Average of start and end positions
            avg_x = (player_passes['start_x'].mean() + player_passes['end_x'].mean()) / 2
            avg_y = (player_passes['start_y'].mean() + player_passes['end_y'].mean()) / 2
        else:
            # Default position if no passes (center of pitch)
            avg_x, avg_y = 0.5, 0.5  # Normalized center

        player_positions[player] = (avg_x, avg_y)

    # Create edges and weights
    edges = []
    weights = []

    for _, row in team_passes.iterrows():
        if row['success']:  # Only count successful passes for visualization
            from_player = row['from_player']
            to_player = row['to_player']

            # Check if edge already exists
            edge_found = False
            for i, (u, v) in enumerate(edges):
                if (u == from_player and v == to_player) or (u == to_player and v == from_player):
                    # For simplicity, we treat as directed but could be undirected
                    edges[i] = (from_player, to_player)  # Ensure direction
                    weights[i] += 1
                    edge_found = True
                    break

            if not edge_found:
                edges.append((from_player, to_player))
                weights.append(1)

    # Convert node positions to list in order of team_players for consistency
    node_positions = [player_positions.get(player, (0.5, 0.5)) for player in team_players]

    return node_positions, edges, weights