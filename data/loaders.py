"""
Data loaders for football analysis.
Handles loading of sample data and provides interfaces for real data.
"""

import pandas as pd
import numpy as np
import json
import os
from typing import Dict, List, Tuple, Optional
from ..utils.constants import PITCH_LENGTH, PITCH_WIDTH


def load_sample_event_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load sample event data for demonstration and testing.

    Args:
        filepath: Path to the sample data file. If None, uses built-in sample.

    Returns:
        DataFrame with event data.
    """
    if filepath is None:
        # Return built-in sample data
        return _generate_sample_event_data()
    else:
        # Load from file
        if filepath.endswith('.json'):
            return pd.read_json(filepath)
        elif filepath.endswith('.csv'):
            return pd.read_csv(filepath)
        else:
            raise ValueError("Unsupported file format. Use .json or .csv")


def load_sample_tracking_data(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Load sample tracking data for demonstration and testing.

    Args:
        filepath: Path to the sample data file. If None, uses built-in sample.

    Returns:
        DataFrame with tracking data.
    """
    if filepath is None:
        # Return built-in sample data
        return _generate_sample_tracking_data()
    else:
        # Load from file
        if filepath.endswith('.csv'):
            return pd.read_csv(filepath)
        elif filepath.endswith('.json'):
            return pd.read_json(filepath)
        else:
            raise ValueError("Unsupported file format. Use .json or .csv")


def _generate_sample_event_data() -> pd.DataFrame:
    """
    Generate sample event data for demonstration.
    Returns a DataFrame with realistic football event data.
    """
    np.random.seed(42)  # For reproducibility

    n_events = 200
    teams = ['Team A', 'Team B']
    players_team_a = [f'A{i}' for i in range(1, 12)]  # A1 to A11
    players_team_b = [f'B{i}' for i in range(1, 12)]  # B1 to B11
    all_players = players_team_a + players_team_b

    # Event types with realistic distribution
    event_types = np.random.choice(
        ['Pass', 'Shot', 'Dribble', 'Tackle', 'Interception', 'Pressure', 'Carry'],
        size=n_events,
        p=[0.4, 0.1, 0.05, 0.1, 0.08, 0.12, 0.15]  # Passes most common
    )

    # Generate timestamps (match duration ~90 minutes)
    timestamps = np.sort(np.random.uniform(0, 90*60, n_events))  # in seconds

    # Generate positions (in meters)
    # For simplicity, we'll generate start and end positions
    start_x = np.random.uniform(0, PITCH_LENGTH, n_events)
    start_y = np.random.uniform(0, PITCH_WIDTH, n_events)

    # End positions: for passes, shots, etc., we'll generate realistic destinations
    end_x = np.zeros(n_events)
    end_y = np.zeros(n_events)

    for i in range(n_events):
        if event_types[i] == 'Pass':
            # Passes: tend to go forward but can go anywhere
            end_x[i] = np.clip(start_x[i] + np.random.normal(15, 10), 0, PITCH_LENGTH)
            end_y[i] = np.clip(start_y[i] + np.random.normal(0, 8), 0, PITCH_WIDTH)
        elif event_types[i] == 'Shot':
            # Shots: usually towards opponent goal
            if start_x[i] < PITCH_LENGTH/2:  # In own half
                end_x[i] = np.clip(start_x[i] + np.random.uniform(10, 30), 0, PITCH_LENGTH)
                end_y[i] = np.clip(start_y[i] + np.random.normal(0, 5), 0, PITCH_WIDTH)
            else:  # In opponent half
                end_x[i] = np.clip(start_x[i] + np.random.normal(5, 5), 0, PITCH_LENGTH)
                end_y[i] = np.clip(start_y[i] + np.random.normal(0, 3), 0, PITCH_WIDTH)
        else:
            # Other events: short movements
            end_x[i] = np.clip(start_x[i] + np.random.normal(0, 3), 0, PITCH_LENGTH)
            end_y[i] = np.clip(start_y[i] + np.random.normal(0, 3), 0, PITCH_WIDTH)

    # Determine which team each event belongs to (simplified)
    # We'll assign based on starting position
    team_of_event = []
    player_of_event = []
    for i in range(n_events):
        if start_x[i] < PITCH_LENGTH/2:
            team_of_event.append('Team A')
            player_of_event.append(np.random.choice(players_team_a))
        else:
            team_of_event.append('Team B')
            player_of_event.append(np.random.choice(players_team_b))

    # Success/failure for passes and shots
    success = np.zeros(n_events, dtype=bool)
    for i in range(n_events):
        if event_types[i] == 'Pass':
            # 75% pass completion rate
            success[i] = np.random.random() < 0.75
        elif event_types[i] == 'Shot':
            # 30% shot on target (simplified as success)
            success[i] = np.random.random() < 0.30
        else:
            # Other events: 60% success rate
            success[i] = np.random.random() < 0.60

    # Create DataFrame
    events_df = pd.DataFrame({
        'event_id': range(n_events),
        'timestamp': timestamps,
        'team': team_of_event,
        'player_id': player_of_event,
        'event_type': event_types,
        'start_x': start_x,
        'start_y': start_y,
        'end_x': end_x,
        'end_y': end_y,
        'success': success
    })

    return events_df


def _generate_sample_tracking_data() -> pd.DataFrame:
    """
    Generate sample tracking data for demonstration.
    Returns a DataFrame with player and ball positions over time.
    """
    np.random.seed(42)  # For reproducibility

    # Simulate 5 minutes of tracking data at 25 Hz
    duration_seconds = 5 * 60  # 5 minutes
    fps = 25
    n_frames = int(duration_seconds * fps)

    # Time stamps
    timestamps = np.linspace(0, duration_seconds, n_frames)

    # Players
    team_a_players = [f'A{i}' for i in range(1, 12)]  # A1 to A11
    team_b_players = [f'B{i}' for i in range(1, 12)]  # B1 to B11
    all_players = team_a_players + team_b_players + ['ball']

    # We'll generate data in long format: one row per player per frame
    data_rows = []

    for frame_idx, t in enumerate(timestamps):
        # Ball position: simulate realistic ball movement
        ball_x = np.clip(
            52.5 + 20 * np.sin(t/10) + 5 * np.random.normal(),
            0, PITCH_LENGTH
        )
        ball_y = np.clip(
            34 + 15 * np.cos(t/15) + 3 * np.random.normal(),
            0, PITCH_WIDTH
        )

        data_rows.append({
            'frame': frame_idx,
            'timestamp': t,
            'player_id': 'ball',
            'x': ball_x,
            'y': ball_y,
            'team': 'ball'
        })

        # Team A players: simulate formation and movement
        # We'll use a 4-3-3 formation as base
        team_a_formation = {
            'A1': (10, 10),   # GK
            'A2': (20, 15),   # RB
            'A3': (20, 30),   # RCB
            'A4': (20, 40),   # LCB
            'A5': (20, 55),   # LB
            'A6': (35, 25),   # CDM
            'A7': (40, 15),   # RM
            'A8': (40, 35),   # CM
            'A9': (40, 55),   # LM
            'A10': (55, 25),  # RF
            'A11': (55, 45)   # LF / ST
        }

        for player_id, (base_x, base_y) in team_a_formation.items():
            # Add some realistic movement around base position
            pos_x = np.clip(
                base_x + 3 * np.sin(t/5 + hash(player_id) % 10) + 2 * np.random.normal(),
                0, PITCH_LENGTH
            )
            pos_y = np.clip(
                base_y + 2 * np.cos(t/7 + hash(player_id) % 10) + 1.5 * np.random.normal(),
                0, PITCH_WIDTH
            )

            data_rows.append({
                'frame': frame_idx,
                'timestamp': t,
                'player_id': player_id,
                'x': pos_x,
                'y': pos_y,
                'team': 'Team A'
            })

        # Team B players: similar but oriented opposite direction
        team_b_formation = {
            'B1': (95, 58),   # GK
            'B2': (85, 53),   # RB
            'B3': (85, 38),   # RCB
            'B4': (85, 28),   # LCB
            'B5': (85, 13),   # LB
            'B6': (70, 43),   # CDM
            'B7': (65, 53),   # RM
            'B8': (65, 33),   # CM
            'B9': (65, 13),   # LM
            'B10': (50, 43),  # RF
            'B11': (50, 23)   # LF / ST
        }

        for player_id, (base_x, base_y) in team_b_formation.items():
            # Add some realistic movement around base position
            pos_x = np.clip(
                base_x + 3 * np.sin(t/5 + hash(player_id) % 10) + 2 * np.random.normal(),
                0, PITCH_LENGTH
            )
            pos_y = np.clip(
                base_y + 2 * np.cos(t/7 + hash(player_id) % 10) + 1.5 * np.random.normal(),
                0, PITCH_WIDTH
            )

            data_rows.append({
                'frame': frame_idx,
                'timestamp': t,
                'player_id': player_id,
                'x': pos_x,
                'y': pos_y,
                'team': 'Team B'
            })

    # Create DataFrame
    tracking_df = pd.DataFrame(data_rows)

    return tracking_df


def save_sample_data(data_dir: str = "data/samples"):
    """
    Save sample data files to the specified directory.

    Args:
        data_dir: Directory where to save the sample data files.
    """
    # Create directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)

    # Generate and save sample event data
    event_data = _generate_sample_event_data()
    event_data.to_json(os.path.join(data_dir, "sample_event_data.json"), indent=2)

    # Generate and save sample tracking data
    tracking_data = _generate_sample_tracking_data()
    tracking_data.to_csv(os.path.join(data_dir, "sample_tracking_data.csv"), index=False)

    print(f"Sample data saved to {data_dir}")
    print(f" - {os.path.join(data_dir, 'sample_event_data.json')}")
    print(f" - {os.path.join(data_dir, 'sample_tracking_data.csv')}")


if __name__ == "__main__":
    # When run directly, generate and save sample data
    save_sample_data()