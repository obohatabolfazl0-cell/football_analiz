"""
Tactical analysis module for football matches.
Implements core tactical concepts and metrics.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from .utils.constants import PITCH_LENGTH, PITCH_WIDTH


@dataclass
class Formation:
    """Represents a team formation."""
    name: str
    defense: int
    midfield: int
    attack: int
    width: float  # Average width of formation
    depth: float  # Average depth of formation
    positions: Dict[str, Tuple[float, float]]  # Player positions (x, y) normalized 0-1


class TacticalAnalyzer:
    """
    Main class for tactical analysis of football teams.
    """

    def __init__(self, pitch_length: float = PITCH_LENGTH, pitch_width: float = PITCH_WIDTH):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width

    def analyze_formation(self, positions: pd.DataFrame) -> Formation:
        """
        Analyze team formation from player positions.

        Args:
            positions: DataFrame with columns ['player_id', 'x', 'y', 'timestamp']
                       where x,y are normalized coordinates (0-1) or in meters.

        Returns:
            Formation object with detected formation and metrics.
        """
        # For simplicity, we assume the data is already normalized or we normalize it
        # In a real implementation, we would have more sophisticated formation detection

        # Calculate average position per player (over time if multiple timestamps)
        if 'timestamp' in positions.columns:
            avg_positions = positions.groupby('player_id')[['x', 'y']].mean().reset_index()
        else:
            avg_positions = positions[['player_id', 'x', 'y']].copy()

        # Sort by y-coordinate (defense to attack) to assign lines
        avg_positions = avg_positions.sort_values('y')

        # Simple line detection: split into defense, midfield, attack
        n_players = len(avg_positions)
        if n_players < 3:
            raise ValueError("Need at least 3 players to analyze formation")

        # We'll use tertials to split into three lines for simplicity
        # In reality, this would be more complex (using clustering or known formations)
        defense_count = n_players // 3
        midfield_count = n_players // 3
        attack_count = n_players - defense_count - midfield_count

        defense = avg_positions.iloc[:defense_count]
        midfield = avg_positions.iloc[defense_count:defense_count + midfield_count]
        attack = avg_positions.iloc[defense_count + midfield_count:]

        # Calculate formation name (simplified)
        formation_name = f"{len(defense)}-{len(midfield)}-{len(attack)}"

        # Calculate width and depth
        width = (avg_positions['x'].max() - avg_positions['x'].min()) * 100  # as percentage
        depth = (avg_positions['y'].max() - avg_positions['y'].min()) * 100

        # Create positions dictionary
        positions_dict = {
            row['player_id']: (row['x'], row['y']) for _, row in avg_positions.iterrows()
        }

        return Formation(
            name=formation_name,
            defense=len(defense),
            midfield=len(midfield),
            attack=len(attack),
            width=width,
            depth=depth,
            positions=positions_dict
        )

    def calculate_pressing_intensity(self,
                                   team_positions: pd.DataFrame,
                                   opponent_positions: pd.DataFrame,
                                   ball_position: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate pressing intensity metrics.

        Args:
            team_positions: DataFrame of team player positions
            opponent_positions: DataFrame of opponent player positions
            ball_position: DataFrame of ball positions (with timestamp)

        Returns:
            Dictionary with pressing intensity metrics.
        """
        # We'll simplify: calculate average distance of team players to ball
        # and opponent players to ball over time

        # Merge on timestamp to get simultaneous positions
        # For simplicity, we assume the data is synchronized and we can merge by index if no timestamp
        # In reality, we would need to align by timestamp

        # If no timestamp, we assume same length and order
        if 'timestamp' not in team_positions.columns:
            # We'll use index as proxy for time
            team_positions['time_idx'] = team_positions.index
            opponent_positions['time_idx'] = opponent_positions.index
            ball_position['time_idx'] = ball_position.index
            merge_on = 'time_idx'
        else:
            merge_on = 'timestamp'

        # We need to aggregate multiple players per time step
        # Let's compute the average position of team and opponent at each time step
        team_avg = team_positions.groupby(merge_on)[['x', 'y']].mean().reset_index()
        opp_avg = opponent_positions.groupby(merge_on)[['x', 'y']].mean().reset_index()
        ball_avg = ball_position.groupby(merge_on)[['x', 'y']].mean().reset_index()

        # Merge the average positions
        merged = pd.merge(team_avg, opp_avg, on=merge_on, suffixes=('_team', '_opp'))
        merged = pd.merge(merged, ball_avg, on=merge_on)

        # Calculate distances
        merged['dist_team_to_ball'] = np.sqrt(
            (merged['x_team'] - merged['x'])**2 +
            (merged['y_team'] - merged['y'])**2
        )
        merged['dist_opp_to_ball'] = np.sqrt(
            (merged['x_opp'] - merged['x'])**2 +
            (merged['y_opp'] - merged['y'])**2
        )

        # Pressing intensity: how close team players are to ball relative to opponents
        # Higher when team is closer to ball than opponents
        pressing_intensity = (merged['dist_opp_to_ball'] - merged['dist_team_to_ball']).mean()

        # Normalize by pitch length for a 0-1ish score (though can be negative)
        # We'll use a simple normalization for demonstration
        max_dist = np.sqrt(self.pitch_length**2 + self.pitch_width**2)
        normalized_intensity = pressing_intensity / max_dist

        return {
            "pressing_intensity": normalized_intensity,
            "avg_team_to_ball_dist": merged['dist_team_to_ball'].mean(),
            "avg_opp_to_ball_dist": merged['dist_opp_to_ball'].mean(),
            "pressing_effectiveness": 1 if normalized_intensity > 0 else 0  # Simplified
        }

    def analyze_passing_network(self,
                              passes: pd.DataFrame,
                              team_players: List[str]) -> Dict[str, float]:
        """
        Analyze passing network for a team.

        Args:
            passes: DataFrame with columns ['from_player', 'to_player', 'timestamp',
                                              'start_x', 'start_y', 'end_x', 'end_y', 'success']
            team_players: List of player IDs for the team

        Returns:
            Dictionary with passing network metrics.
        """
        # Filter to team passes only
        team_passes = passes[
            passes['from_player'].isin(team_players) &
            passes['to_player'].isin(team_players)
        ].copy()

        if len(team_passes) == 0:
            return {
                "total_passes": 0,
                "completion_rate": 0.0,
                "network_centrality": {},
                "key_passer": None
            }

        # Calculate completion rate
        completion_rate = team_passes['success'].mean() if 'success' in team_passes.columns else 1.0

        # Create a directed graph of passes
        import networkx as nx
        G = nx.DiGraph()

        # Add edges with weight = number of passes
        for _, row in team_passes.iterrows():
            if G.has_edge(row['from_player'], row['to_player']):
                G[row['from_player']][row['to_player']]['weight'] += 1
            else:
                G.add_edge(row['from_player'], row['to_player'], weight=1)

        # Calculate centrality measures
        try:
            # In-degree centrality (how often a player is passed to)
            in_centrality = nx.in_degree_centrality(G)
            # Out-degree centrality (how often a player passes)
            out_centrality = nx.out_degree_centrality(G)
            # Betweenness centrality (importance in connecting the network)
            betweenness = nx.betweenness_centrality(G, weight='weight')
        except:
            # If graph has issues, return empty
            in_centrality = out_centrality = betweenness = {}

        # Combine centrality scores (simple average)
        centrality = {}
        for player in set(list(in_centrality.keys()) + list(out_centrality.keys()) + list(betweenness.keys())):
            centrality[player] = np.mean([
                in_centrality.get(player, 0),
                out_centrality.get(player, 0),
                betweenness.get(player, 0)
            ])

        # Key passer: highest centrality
        key_passer = max(centrality, key=centrality.get) if centrality else None

        # Calculate average pass length
        if 'start_x' in team_passes.columns and 'start_y' in team_passes.columns:
            team_passes['pass_length'] = np.sqrt(
                (team_passes['end_x'] - team_passes['start_x'])**2 +
                (team_passes['end_y'] - team_passes['start_y'])**2
            )
            avg_pass_length = team_passes['pass_length'].mean()
        else:
            avg_pass_length = 0.0

        return {
            "total_passes": len(team_passes),
            "completion_rate": completion_rate,
            "avg_pass_length": avg_pass_length,
            "network_centrality": centrality,
            "key_passer": key_passer,
            "network_density": nx.density(G) if len(G) > 1 else 0.0
        }

    def defensive_shape_analysis(self,
                               positions: pd.DataFrame) -> Dict[str, float]:
        """
        Analyze defensive shape of a team.

        Args:
            positions: DataFrame with columns ['player_id', 'x', 'y', 'timestamp']
                       (normalized or in meters)

        Returns:
            Dictionary with defensive shape metrics.
        """
        # We'll focus on the defensive line (assuming we can identify defenders)
        # For simplicity, we'll use the bottom third of the pitch as defensive zone
        # and look at the spread and height of players in that zone

        # Normalize positions if needed (assuming 0-1 or convert to 0-1)
        # We'll assume the data is in meters and convert to 0-1
        # Pitch length: 105m, width: 68m (standard)
        # But we have PITCH_LENGTH and PITCH_WIDTH from constants

        pos = positions.copy()
        # Convert to 0-1 if not already
        if pos['x'].max() > 1 or pos['y'].max() > 1:
            pos['x_norm'] = pos['x'] / self.pitch_length
            pos['y_norm'] = pos['y'] / self.pitch_width
        else:
            pos['x_norm'] = pos['x']
            pos['y_norm'] = pos['y']

        # Define defensive zone (lower third of the pitch)
        defensive_zone = pos[pos['y_norm'] < 0.33]

        if len(defensive_zone) == 0:
            return {
                "defensive_line_height": 0.0,
                "defensive_line_width": 0.0,
                "defensive_compactness": 0.0,
                "line_deflection": 0.0
            }

        # Defensive line height: average y position of defenders (lower is deeper)
        defensive_line_height = defensive_zone['y_norm'].mean()

        # Defensive line width: spread in x direction
        defensive_line_width = defensive_zone['x_norm'].max() - defensive_zone['x_norm'].min()

        # Compactness: inverse of the area covered by defenders (smaller area = more compact)
        # We'll use the convex hull area or simply the product of width and height spread
        # For simplicity, we use the standard deviation of positions
        x_std = defensive_zone['x_norm'].std()
        y_std = defensive_zone['y_norm'].std()
        compactness = 1.0 / (1.0 + x_std + y_std)  # Higher when more compact

        # Line deflection: how much the defensive line is curved (standard deviation of y positions)
        line_deflection = defensive_zone['y_norm'].std()

        return {
            "defensive_line_height": defensive_line_height,
            "defensive_line_width": defensive_line_width * 100,  # as percentage
            "defensive_compactness": compactness,
            "line_deflection": line_deflection
        }