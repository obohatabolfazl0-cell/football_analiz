"""
Passing network analysis models.
"""

import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Tuple, Optional
from .utils.constants import PITCH_LENGTH, PITCH_WIDTH


class PassingNetworkAnalyzer:
    """
    Analyzes passing networks and ball circulation patterns.
    """

    def __init__(self):
        pass

    def analyze_network(self,
                       passes: pd.DataFrame,
                       team_players: List[str]) -> Dict:
        """
        Analyze passing network for a team.

        Args:
            passes: DataFrame with pass events (from_player, to_player,
                   start_x, start_y, end_x, end_y, success, timestamp).
            team_players: List of player IDs for the team.

        Returns:
            Dictionary with network analysis results.
        """
        # Filter to team passes only
        team_passes = passes[
            passes['from_player'].isin(team_players) &
            passes['to_player'].isin(team_players)
        ].copy()

        if len(team_passes) == 0:
            return self._empty_network_result()

        # Calculate basic passing stats
        total_passes = len(team_passes)
        completion_rate = team_passes['success'].mean() if 'success' in team_passes.columns else 1.0

        # Calculate average pass length
        if 'start_x' in team_passes.columns and 'start_y' in team_passes.columns:
            team_passes['pass_length'] = np.sqrt(
                (team_passes['end_x'] - team_passes['start_x'])**2 +
                (team_passes['end_y'] - team_passes['start_y'])**2
            )
            avg_pass_length = team_passes['pass_length'].mean()
        else:
            avg_pass_length = 0.0

        # Create directed graph
        G = nx.DiGraph()

        # Add edges with weight = number of passes
        for _, row in team_passes.iterrows():
            if G.has_edge(row['from_player'], row['to_player']):
                G[row['from_player']][row['to_player']]['weight'] += 1
            else:
                G.add_edge(row['from_player'], row['to_player'], weight=1)

        # Calculate network metrics
        try:
            # Centrality measures
            in_centrality = nx.in_degree_centrality(G)
            out_centrality = nx.out_degree_centrality(G)

            # Betweenness centrality (slower but important for network analysis)
            if len(G) > 1:
                betweenness = nx.betweenness_centrality(G, weight='weight')
            else:
                betweenness = {node: 0.0 for node in G.nodes()}

            # Clustering coefficient (how clustered the network is)
            if len(G) > 1:
                # Convert to undirected for clustering coefficient
                G_undirected = G.to_undirected()
                clustering = nx.clustering(G_undirected)
            else:
                clustering = {node: 0.0 for node in G.nodes()}

            # Density (how complete the network is)
            density = nx.density(G)

        except:
            # Fallback if graph calculations fail
            in_centrality = out_centrality = betweenness = clustering = {node: 0.0 for node in team_players}
            density = 0.0

        # Combine centrality scores
        centrality = {}
        for player in set(list(in_centrality.keys()) + list(out_centrality.keys()) +
                         list(betweenness.keys()) + list(clustering.keys())):
            centrality[player] = np.mean([
                in_centrality.get(player, 0),
                out_centrality.get(player, 0),
                betweenness.get(player, 0),
                clustering.get(player, 0)
            ])

        # Key passer(s): players with highest centrality
        if centrality:
            max_centrality = max(centrality.values())
            key_passers = [player for player, score in centrality.items()
                          if score == max_centrality]
        else:
            key_passers = []

        # Calculate network efficiency metrics
        # 1. Link density (actual connections / possible connections)
        n_players = len([p for p in team_players if p in G.nodes()])
        possible_connections = n_players * (n_players - 1) if n_players > 1 else 0
        actual_connections = G.number_of_edges()
        link_density = actual_connections / possible_connections if possible_connections > 0 else 0

        # 2. Average clustering coefficient
        avg_clustering = np.mean(list(clustering.values())) if clustering else 0

        # 3. Assortativity (do similar players connect to each other?)
        # We'll skip this for simplicity as it requires node attributes

        # 4. Network diameter (longest shortest path)
        try:
            if nx.is_weakly_connected(G) and len(G) > 1:
                diameter = nx.diameter(G.to_undirected())
            else:
                diameter = 0
        except:
            diameter = 0

        return {
            "total_passes": total_passes,
            "completion_rate": completion_rate,
            "avg_pass_length": avg_pass_length,
            "network_centrality": centrality,
            "key_passers": key_passers,
            "in_degree_centrality": in_centrality,
            "out_degree_centrality": out_centrality,
            "betweenness_centrality": betweenness,
            "clustering_coefficient": clustering,
            "network_density": density,
            "link_density": link_density,
            "avg_clustering": avg_clustering,
            "network_diameter": diameter,
            "number_of_nodes": G.number_of_nodes(),
            "number_of_edges": G.number_of_edges(),
            "is_connected": nx.is_weakly_connected(G) if len(G) > 1 else True
        }

    def analyze_passing_patterns(self,
                               passes: pd.DataFrame,
                               team_players: List[str]) -> Dict[str, float]:
        """
        Analyze passing patterns and tendencies.

        Args:
            passes: DataFrame with pass events.
            team_players: List of player IDs for the team.

        Returns:
            Dictionary with passing pattern metrics.
        """
        # Filter to team passes
        team_passes = passes[
            passes['from_player'].isin(team_players) &
            passes['to_player'].isin(team_players)
        ].copy()

        if len(team_passes) == 0:
            return {
                "short_pass_ratio": 0.0,
                "long_pass_ratio": 0.0,
                "forward_pass_ratio": 0.0,
                "lateral_pass_ratio": 0.0,
                "backward_pass_ratio": 0.0,
                "left_right_balance": 0.5,
                "forward_backward_balance": 0.5
            }

        # Calculate pass lengths if not already present
        if 'pass_length' not in team_passes.columns:
            if 'start_x' in team_passes.columns and 'start_y' in team_passes.columns:
                team_passes['pass_length'] = np.sqrt(
                    (team_passes['end_x'] - team_passes['start_x'])**2 +
                    (team_passes['end_y'] - team_passes['start_y'])**2
                )
            else:
                team_passes['pass_length'] = 0

        # Define passing categories based on length
        short_threshold = 10.0  # meters
        long_threshold = 30.0   # meters

        short_passes = team_passes[team_passes['pass_length'] <= short_threshold]
        long_passes = team_passes[team_passes['pass_length'] >= long_threshold]
        medium_passes = team_passes[
            (team_passes['pass_length'] > short_threshold) &
            (team_passes['pass_length'] < long_threshold)
        ]

        short_pass_ratio = len(short_passes) / len(team_passes) if len(team_passes) > 0 else 0
        long_pass_ratio = len(long_passes) / len(team_passes) if len(team_passes) > 0 else 0

        # Calculate pass direction (assuming x increases from own goal to opponent goal)
        # We need to know which direction is attacking for the team
        # For simplicity, we'll assume higher x is more attacking
        team_passes['dx'] = team_passes['end_x'] - team_passes['start_x']
        team_passes['dy'] = team_passes['end_y'] - team_passes['start_y']  # Not typically used for direction

        forward_passes = team_passes[team_passes['dx'] > 0]      # Positive x direction
        backward_passes = team_passes[team_passes['dx'] < 0]     # Negative x direction
        lateral_passes = team_passes[abs(team_passes['dx']) <= 1.0]  # Small x change

        forward_pass_ratio = len(forward_passes) / len(team_passes) if len(team_passes) > 0 else 0
        backward_pass_ratio = len(backward_passes) / len(team_passes) if len(team_passes) > 0 else 0
        lateral_pass_ratio = len(lateral_passes) / len(team_passes) if len(team_passes) > 0 else 0

        # Left-right balance (assuming y=0 is left touchline, y=pitch_width is right touchline)
        # Passes that go left vs right
        team_passes['dy'] = team_passes['end_y'] - team_passes['start_y']
        right_passes = team_passes[team_passes['dy'] > 0]   # Positive y direction (to the right)
        left_passes = team_passes[team_passes['dy'] < 0]    # Negative y direction (to the left)

        total_lateral = len(left_passes) + len(right_passes)
        left_right_balance = len(right_passes) / total_lateral if total_lateral > 0 else 0.5

        # Forward-backward balance
        total_longitudinal = len(forward_passes) + len(backward_passes)
        forward_backward_balance = len(forward_passes) / total_longitudinal if total_longitudinal > 0 else 0.5

        return {
            "short_pass_ratio": short_pass_ratio,
            "medium_pass_ratio": len(medium_passes) / len(team_passes) if len(team_passes) > 0 else 0,
            "long_pass_ratio": long_pass_ratio,
            "forward_pass_ratio": forward_pass_ratio,
            "lateral_pass_ratio": lateral_pass_ratio,
            "backward_pass_ratio": backward_pass_ratio,
            "left_right_balance": left_right_balance,
            "forward_backward_balance": forward_backward_balance,
            "avg_pass_length": team_passes['pass_length'].mean(),
            "pass_length_std": team_passes['pass_length'].std()
        }

    def _empty_network_result(self) -> Dict:
        """Return empty result for when no passes are available."""
        return {
            "total_passes": 0,
            "completion_rate": 0.0,
            "avg_pass_length": 0.0,
            "network_centrality": {},
            "key_passers": [],
            "in_degree_centrality": {},
            "out_degree_centrality": {},
            "betweenness_centrality": {},
            "clustering_coefficient": {},
            "network_density": 0.0,
            "link_density": 0.0,
            "avg_clustering": 0.0,
            "network_diameter": 0,
            "number_of_nodes": 0,
            "number_of_edges": 0,
            "is_connected": False
        }