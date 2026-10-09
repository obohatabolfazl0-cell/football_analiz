"""
Tactical visualization module for football matches.
Creates plots and charts for tactical analysis.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import networkx as nx
from .utils.constants import PITCH_LENGTH, PITCH_WIDTH


class TacticalVisualizer:
    """
    Creates visualizations for football tactical analysis.
    """

    def __init__(self, figsize: Tuple[int, int] = (12, 8)):
        self.figsize = figsize
        # Set style
        plt.style.use('seaborn-v0_8')
        self.pitch_color = '#2E8B57'  # Sea green
        self.line_color = 'white'
        self.player_color = '#FFD700'  # Gold
        self.ball_color = '#FFFFFF'  # White

    def draw_pitch(self, ax: Optional[plt.Axes] = None) -> plt.Axes:
        """
        Draw a football pitch.

        Args:
            ax: Matplotlib axes to draw on. If None, creates new figure.

        Returns:
            Matplotlib axes with the pitch drawn.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)

        # Pitch outline
        ax.plot([0, 0, PITCH_LENGTH, PITCH_LENGTH, 0],
                [0, PITCH_WIDTH, PITCH_WIDTH, 0, 0],
                color=self.line_color, linewidth=2)

        # Halfway line
        ax.plot([PITCH_LENGTH/2, PITCH_LENGTH/2], [0, PITCH_WIDTH],
                color=self.line_color, linewidth=2)

        # Penalty areas
        # Left penalty area
        ax.plot([0, 16.5, 16.5, 0],
                [PITCH_WIDTH/2 - 20.15, PITCH_WIDTH/2 - 20.15,
                 PITCH_WIDTH/2 + 20.15, PITCH_WIDTH/2 + 20.15],
                color=self.line_color, linewidth=2)
        # Right penalty area
        ax.plot([PITCH_LENGTH, PITCH_LENGTH - 16.5, PITCH_LENGTH - 16.5, PITCH_LENGTH],
                [PITCH_WIDTH/2 - 20.15, PITCH_WIDTH/2 - 20.15,
                 PITCH_WIDTH/2 + 20.15, PITCH_WIDTH/2 + 20.15],
                color=self.line_color, linewidth=2)

        # 6-yard boxes
        # Left 6-yard box
        ax.plot([0, 5.5, 5.5, 0],
                [PITCH_WIDTH/2 - 9.16, PITCH_WIDTH/2 - 9.16,
                 PITCH_WIDTH/2 + 9.16, PITCH_WIDTH/2 + 9.16],
                color=self.line_color, linewidth=2)
        # Right 6-yard box
        ax.plot([PITCH_LENGTH, PITCH_LENGTH - 5.5, PITCH_LENGTH - 5.5, PITCH_LENGTH],
                [PITCH_WIDTH/2 - 9.16, PITCH_WIDTH/2 - 9.16,
                 PITCH_WIDTH/2 + 9.16, PITCH_WIDTH/2 + 9.16],
                color=self.line_color, linewidth=2)

        # Center circle
        center_circle = plt.Circle((PITCH_LENGTH/2, PITCH_WIDTH/2), 9.15,
                                   color=self.line_color, fill=False, linewidth=2)
        ax.add_patch(center_circle)

        # Penalty spots
        ax.plot(PITCH_LENGTH/2, PITCH_WIDTH/2, 'o', color=self.line_color, markersize=2)  # Center spot
        ax.plot(11, PITCH_WIDTH/2, 'o', color=self.line_color, markersize=2)  # Left penalty spot
        ax.plot(PITCH_LENGTH - 11, PITCH_WIDTH/2, 'o', color=self.line_color, markersize=2)  # Right penalty spot

#         # Corner arcs (quarter circles)
#         # Bottom left
#         corner_arc_bl = plt.Arc((0, 0), 2*1, 2*1, angle=0, theta1=0, theta2=90,
#                                 color=self.line_color, linewidth=2)
#         ax.add_patch(corner_arc_bl)
#         # Bottom right
#         corner_arc_br = plt.Arc((PITCH_LENGTH, 0), 2*1, 2*1, angle=0, theta1=90, theta2=180,
#                                 color=self.line_color, linewidth=2)
#         ax.add_patch(corner_arc_br)
#         # Top left
#         corner_arc_tl = plt.Arc((0, PITCH_WIDTH), 2*1, 2*1, angle=0, theta1=270, theta2=360,
#                                 color=self.line_color, linewidth=2)
#         ax.add_patch(corner_arc_tl)
#         # Top right
#         corner_arc_tr = plt.Arc((PITCH_LENGTH, PITCH_WIDTH), 2*1, 2*1, angle=0, theta1=180, theta2=270,
#                                 color=self.line_color, linewidth=2)
#         ax.add_patch(corner_arc_tr)

        ax.set_xlim(-2, PITCH_LENGTH + 2)
        ax.set_ylim(-2, PITCH_WIDTH + 2)
        ax.set_aspect('equal')
        ax.set_facecolor(self.pitch_color)
        ax.set_xticks([])
        ax.set_yticks([])

        return ax

    def plot_formation(self,
                      formation: Dict[str, Tuple[float, float]],
                      team_name: str = "Team",
                      ax: Optional[plt.Axes] = None) -> plt.Axes:
        """
        Plot team formation on a pitch.

        Args:
            formation: Dictionary mapping player_id to (x, y) coordinates (in meters).
            team_name: Name of the team for the title.
            ax: Matplotlib axes to draw on. If None, creates new figure.

        Returns:
            Matplotlib axes with the formation plotted.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)

        # Draw pitch
        self.draw_pitch(ax)

        # Plot players
        x_coords = [pos[0] for pos in formation.values()]
        y_coords = [pos[1] for pos in formation.values()]

        ax.scatter(x_coords, y_coords,
                  c=self.player_color, s=200, edgecolors='black', linewidth=2, zorder=5)

        # Optionally, add player numbers or names
        for i, (player_id, pos) in enumerate(formation.items()):
            ax.annotate(str(player_id),
                       (pos[0], pos[1]),
                       xytext=(0, 0),
                       textcoords='offset points',
                       ha='center', va='center',
                       fontsize=10, fontweight='bold', color='black')

        ax.set_title(f"{team_name} Formation", fontsize=16, fontweight='bold', pad=20)
        return ax

    def plot_passing_network(self,
                           passes: pd.DataFrame,
                           team_players: List[str],
                           team_name: str = "Team",
                           ax: Optional[plt.Axes] = None) -> plt.Axes:
        """
        Plot passing network as a graph on the pitch.

        Args:
            passes: DataFrame with pass events (must have from_player, to_player,
                   start_x, start_y, end_x, end_y, success columns).
            team_players: List of player IDs for the team.
            team_name: Name of the team for the title.
            ax: Matplotlib axes to draw on. If None, creates new figure.

        Returns:
            Matplotlib axes with the passing network plotted.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)

        # Draw pitch
        self.draw_pitch(ax)

        # Filter to team passes
        team_passes = passes[
            passes['from_player'].isin(team_players) &
            passes['to_player'].isin(team_players)
        ].copy()

        if len(team_passes) == 0:
            ax.set_title(f"{team_name} - No Pass Data", fontsize=16, pad=20)
            return ax

        # Create a directed graph
        G = nx.DiGraph()

        # Add nodes (players) with their average positions
        player_positions = {}
        for player in team_players:
            # Find all passes involving this player to get average position
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
                avg_x, avg_y = PITCH_LENGTH/2, PITCH_WIDTH/2

            player_positions[player] = (avg_x, avg_y)
            G.add_node(player, pos=(avg_x, avg_y))

        # Add edges with weight = number of successful passes
        for _, row in team_passes.iterrows():
            if row['success']:  # Only count successful passes for network visualization
                if G.has_edge(row['from_player'], row['to_player']):
                    G[row['from_player']][row['to_player']]['weight'] += 1
                else:
                    G.add_edge(row['from_player'], row['to_player'], weight=1)

        # Draw nodes (players)
        node_positions = nx.get_node_attributes(G, 'pos')
        nx.draw_networkx_nodes(G, node_positions,
                              node_color=self.player_color,
                              node_size=300,
                              edgecolors='black',
                              linewidths=2,
                              ax=ax)

        # Draw edges (passes) with width proportional to number of passes
        edges = G.edges()
        weights = [G[u][v]['weight'] for u, v in edges]

        # Normalize widths for visualization
        if len(weights) > 0 and max(weights) > 0:
            normalized_widths = [1 + 3 * (w / max(weights)) for w in weights]
        else:
            normalized_widths = [1] * len(weights) if len(weights) > 0 else []

        nx.draw_networkx_edges(G, node_positions,
                              width=normalized_widths,
                              alpha=0.6,
                              edge_color='red',
                              arrows=True,
                              arrowsize=10,
                              ax=ax)

        # Draw labels (player numbers/names)
        nx.draw_networkx_labels(G, node_positions,
                               font_size=10,
                               font_weight='bold',
                               font_color='black',
                               ax=ax)

        ax.set_title(f"{team_name} Passing Network\n"
                    f"(Edge width = number of successful passes)",
                    fontsize=14, fontweight='bold', pad=20)
        return ax

    def plot_pressing_zones(self,
                          pressing_data: pd.DataFrame,
                          team_name: str = "Team",
                          ax: Optional[plt.Axes] = None) -> plt.Axes:
        """
        Plot pressing intensity as a heatmap on the pitch.

        Args:
            pressing_data: DataFrame with columns ['x', 'y', 'pressure_value']
                          where pressure_value represents pressing intensity at that location.
            team_name: Name of the team for the title.
            ax: Matplotlib axes to draw on. If None, creates new figure.

        Returns:
            Matplotlib axes with the pressing zones plotted.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)

        # Draw pitch
        self.draw_pitch(ax)

        if len(pressing_data) == 0:
            ax.set_title(f"{team_name} - No Pressing Data", fontsize=16, pad=20)
            return ax

        # Create a hexbin plot or 2D histogram for pressing intensity
        # We'll use hexbin for a smooth heatmap
        hb = ax.hexbin(pressing_data['x'], pressing_data['y'],
                      C=pressing_data['pressure_value'],
                      gridsize=15,
                      cmap='hot',  # Hot colormap: black -> red -> yellow -> white
                      alpha=0.8,
                      reduce_C_function=np.mean)

        # Add colorbar
        plt.colorbar(hb, ax=ax, label='Pressing Intensity')

        ax.set_title(f"{team_name} Pressing Zones\n"
                    "(Hotter colors = higher pressing intensity)",
                    fontsize=14, fontweight='bold', pad=20)
        return ax

    def plot_defensive_shape(self,
                           defensive_data: pd.DataFrame,
                           team_name: str = "Team",
                           ax: Optional[plt.Axes] = None) -> plt.Axes:
        """
        Plot defensive shape showing defensive line and compactness.

        Args:
            defensive_data: DataFrame with columns ['player_id', 'x', 'y']
                           for defensive players.
            team_name: Name of the team for the title.
            ax: Matplotlib axes to draw on. If None, creates new figure.

        Returns:
            Matplotlib axes with the defensive shape plotted.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)

        # Draw pitch
        self.draw_pitch(ax)

        if len(defensive_data) == 0:
            ax.set_title(f"{team_name} - No Defensive Data", fontsize=16, pad=20)
            return ax

        # Plot defensive players
        ax.scatter(defensive_data['x'], defensive_data['y'],
                  c='#FF4500', s=150, edgecolors='black', linewidth=2,
                  label='Defenders', zorder=5)  # Orange red for defenders

        # Calculate and plot defensive line (convex hull or average line)
        from scipy.spatial import ConvexHull

        if len(defensive_data) >= 3:
            points = defensive_data[['x', 'y']].values
            try:
                hull = ConvexHull(points)
                # For defensive line, we want the bottom part of the hull
                # Assuming y increases towards opponent goal, defenders have lower y
                # We'll take the points with lowest y values from the hull
                hull_points = points[hull.vertices]
                # Sort by x to draw line
                hull_points = hull_points[hull_points[:, 0].argsort()]
                ax.plot(hull_points[:, 0], hull_points[:, 1],
                       'r-', linewidth=3, alpha=0.8, label='Defensive Line')
            except:
                # Fallback: just draw average position line
                avg_x = defensive_data['x'].mean()
                avg_y = defensive_data['y'].mean()
                std_x = defensive_data['x'].std()
                # Draw a horizontal line at average y position
                ax.plot([avg_x - 2*std_x, avg_x + 2*std_x],
                       [avg_y, avg_y],
                       'r-', linewidth=3, alpha=0.8, label='Defensive Line Position')
        else:
            # For fewer than 3 players, just plot mean position
            mean_pos = defensive_data[['x', 'y']].mean()
            ax.plot([mean_pos['x'] - 5, mean_pos['x'] + 5],
                   [mean_pos['y'], mean_pos['y']],
                   'r-', linewidth=3, alpha=0.8, label='Defensive Line Position')

        ax.set_title(f"{team_name} Defensive Shape Analysis",
                    fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='upper right')
        return ax

    def create_tactical_dashboard(self,
                                analysis_results: Dict,
                                team_name: str = "Team",
                                save_path: Optional[str] = None) -> plt.Figure:
        """
        Create a comprehensive tactical dashboard with multiple plots.

        Args:
            analysis_results: Dictionary containing various analysis results.
                            Expected keys: 'formation', 'passing_network',
                                          'pressing_zones', 'defensive_shape'
            team_name: Name of the team for the dashboard title.
            save_path: If provided, saves the figure to this path.

        Returns:
            Matplotlib Figure object with the dashboard.
        """
        fig = plt.figure(figsize=(20, 16))
        fig.suptitle(f"{team_name} Tactical Analysis Dashboard",
                    fontsize=20, fontweight='bold')

        # Formation plot
        ax1 = plt.subplot(2, 3, 1)
        if 'formation' in analysis_results:
            self.plot_formation(analysis_results['formation'],
                              f"{team_name} Formation", ax1)
        else:
            ax1.text(0.5, 0.5, 'No Formation Data',
                    ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title('Formation')

        # Passing network
        ax2 = plt.subplot(2, 3, 2)
        if 'passing_network' in analysis_results:
            # We need to extract the relevant data; for now, assume it's passed appropriately
            # This is a placeholder - in practice, you'd pass the raw data
            ax2.text(0.5, 0.5, 'Passing Network\n(Placeholder)',
                    ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Passing Network')
        else:
            ax2.text(0.5, 0.5, 'No Passing Data',
                    ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title('Passing Network')

        # Pressing zones
        ax3 = plt.subplot(2, 3, 3)
        if 'pressing_zones' in analysis_results:
            ax3.text(0.5, 0.5, 'Pressing Zones\n(Placeholder)',
                    ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Pressing Zones')
        else:
            ax3.text(0.5, 0.5, 'No Pressing Data',
                    ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title('Pressing Zones')

        # Defensive shape
        ax4 = plt.subplot(2, 3, 4)
        if 'defensive_shape' in analysis_results:
            ax4.text(0.5, 0.5, 'Defensive Shape\n(Placeholder)',
                    ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Defensive Shape')
        else:
            ax4.text(0.5, 0.5, 'No Defensive Data',
                    ha='center', va='center', transform=ax4.transAxes)
            ax4.set_title('Defensive Shape')

        # Key metrics summary
        ax5 = plt.subplot(2, 3, (5, 6))
        ax5.axis('off')

        # Create a text summary of key metrics
        metrics_text = f"""
        KEY TACTICAL METRICS FOR {team_name.upper()}
        {"="*50}

        Formation: {analysis_results.get('formation', {}).get('name', 'N/A')}
        Width: {analysis_results.get('formation', {}).get('width', 0):.1f}%
        Depth: {analysis_results.get('formation', {}).get('depth', 0):.1f}%

        Pressing Intensity: {analysis_results.get('pressing', {}).get('intensity', 0):.3f}
        Avg Pass Length: {analysis_results.get('passing', {}).get('avg_length', 0):.1f}m
        Pass Completion: {analysis_results.get('passing', {}).get('completion_rate', 0):.1%}

        Defensive Line Height: {analysis_results.get('defensive', {}).get('line_height', 0):.2f}
        Defensive Compactness: {analysis_results.get('defensive', {}).get('compactness', 0):.3f}
        """

        ax5.text(0.05, 0.95, metrics_text,
                transform=ax5.transAxes, fontsize=12,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig