"""
Basic usage examples for the football tactical analyzer.
"""

import pandas as pd
import numpy as np
from analyzer.tactical import TacticalAnalyzer
from analyzer.events import EventAnalyzer
from analyzer.tracking import TrackingAnalyzer
from analyzer.visualization import TacticalVisualizer
from data.loaders import load_sample_event_data, load_sample_tracking_data
from models.formations import FormationDetector
from models.pressing import PressingAnalyzer
from models.passing_networks import PassingNetworkAnalyzer
from models.defensive_shape import DefensiveShapeAnalyzer


def example_event_analysis():
    """Example of analyzing event data."""
    print("=== Event Data Analysis Example ===")

    # Load sample event data
    events = load_sample_event_data()
    print(f"Loaded {len(events)} events")

    # Initialize analyzers
    event_analyzer = EventAnalyzer()
    tactical_analyzer = TacticalAnalyzer()

    # Analyze passes for Team A
    team_a_events = events[events['team'] == 'Team A']
    team_a_players = [f'A{i}' for i in range(1, 12)]

    passes = event_analyzer.process_passes(team_a_events)
    print(f"Team A completed {len(passes)} pass events")

    # Analyze passing network
    network_results = event_analyzer.build_passing_network(passes, team_a_players)
    print(f"Pass completion rate: {network_results['completion_rate']:.1%}")
    print(f"Key passer(s): {network_results['key_passers']}")

    # Analyze defensive actions
    defensive_actions = event_analyzer.defensive_actions_summary(team_a_events, team_a_players)
    print(f"Defensive actions: {defensive_actions}")

    return events


def example_formation_analysis():
    """Example of formation analysis from position data."""
    print("\n=== Formation Analysis Example ===")

    # Load sample tracking data
    tracking = load_sample_tracking_data()
    print(f"Loaded tracking data with {len(tracking)} records")

    # Get Team A position data
    team_a_tracking = tracking[tracking['team'] == 'Team A']

    # Initialize formation detector
    formation_detector = FormationDetector()

    # Detect formation
    formation_result = formation_detector.detect_formation_kmeans(team_a_tracking)

    print(f"Detected formation: {formation_result['formation_name']}")
    print(f"Line counts: {formation_result['line_counts']}")
    print(f"Overall width: {formation_result['overall_width']:.1f}%")
    print(f"Overall depth: {formation_result['overall_depth']:.1f}%")
    print(f"Formation quality: {formation_result['formation_quality']:.3f}")

    return formation_result


def example_pressing_analysis():
    """Example of pressing analysis."""
    print("\n=== Pressing Analysis Example ===")

    # Load sample data
    events = load_sample_event_data()
    tracking = load_sample_tracking_data()

    # Get position data for both teams
    team_a_tracking = tracking[tracking['team'] == 'Team A']
    team_b_tracking = tracking[tracking['team'] == 'Team B']

    # For simplicity, we'll use average positions as proxy for ball position
    # In reality, you'd have explicit ball tracking data
    team_a_avg = team_a_tracking.groupby('timestamp')[['x', 'y']].mean().reset_index()
    team_b_avg = team_b_tracking.groupby('timestamp')[['x', 'y']].mean().reset_index()

    # Use Team A's average position as ball position (simplified)
    ball_position = team_a_avg[['timestamp', 'x', 'y']].copy()
    ball_position.rename(columns={'x': 'ball_x', 'y': 'ball_y'}, inplace=True)

    # Initialize pressing analyzer
    pressing_analyzer = PressingAnalyzer()

    # Analyze pressing phases
    pressing_results = pressing_analyzer.analyze_pressing_phases(
        team_a_tracking, team_b_tracking, ball_position
    )

    print("Pressing intensity by third:")
    for key, value in pressing_results.items():
        if 'third' in key:
            print(f"  {key}: {value:.3f}")
    print(f"Overall pressing intensity: {pressing_results['overall_pressing_intensity']:.3f}")

    return pressing_results


def example_passing_network():
    """Example of passing network analysis."""
    print("\n=== Passing Network Analysis Example ===")

    # Load sample event data
    events = load_sample_event_data()

    # Get Team A passes
    team_a_events = events[events['team'] == 'Team A']
    team_a_players = [f'A{i}' for i in range(1, 12)]

    # Initialize passing network analyzer
    passing_analyzer = PassingNetworkAnalyzer()

    # Analyze passing network
    network_results = passing_analyzer.analyze_network(team_a_events, team_a_players)

    print(f"Total passes: {network_results['total_passes']}")
    print(f"Completion rate: {network_results['completion_rate']:.1%}")
    print(f"Average pass length: {network_results['avg_pass_length']:.1f}m")
    print(f"Network density: {network_results['network_density']:.3f}")
    print(f"Key passer(s): {network_results['key_passers']}")

    # Analyze passing patterns
    pattern_results = passing_analyzer.analyze_passing_patterns(team_a_events, team_a_players)
    print(f"Forward pass ratio: {pattern_results['forward_pass_ratio']:.1%}")
    print(f"Short pass ratio: {pattern_results['short_pass_ratio']:.1%}")
    print(f"Long pass ratio: {pattern_results['long_pass_ratio']:.1%}")

    return network_results, pattern_results


def example_defensive_analysis():
    """Example of defensive shape analysis."""
    print("\n=== Defensive Shape Analysis Example ===")

    # Load sample tracking data
    tracking = load_sample_tracking_data()

    # Get defensive players for Team A (simplified: first 5 players as defenders)
    team_a_tracking = tracking[tracking['team'] == 'Team A']
    # We'll assume players A1-A5 are defenders for this example
    defensive_players = [f'A{i}' for i in range(1, 6)]
    team_a_defensive = team_a_tracking[team_a_tracking['player_id'].isin(defensive_players)]

    # Get opponent positions (Team B)
    team_b_tracking = tracking[tracking['team'] == 'Team B']

    # Initialize defensive shape analyzer
    defensive_analyzer = DefensiveShapeAnalyzer()

    # Analyze defensive line
    defensive_results = defensive_analyzer.analyze_defensive_line(team_a_defensive)

    print(f"Defensive line height: {defensive_results['defensive_line_height']:.3f}")
    print(f"Defensive line width: {defensive_results['defensive_line_width']:.1f}%")
    print(f"Defensive line flatness: {defensive_results['defensive_line_flatness']:.3f}")
    print(f"Defensive compactness: {defensive_results['defensive_compactness']:.3f}")
    print(f"Number of defenders: {defensive_results['number_of_defenders']}")

    # Analyze defensive third control
    third_control = defensive_analyzer.defensive_third_control(
        team_a_defensive, team_b_tracking
    )

    print(f"Defensive third control: {third_control['defensive_third_control']:.3f}")
    print(f"Team players in defensive third: {third_control['team_players_in_def_third']}")
    print(f"Opponent players in defensive third: {third_control['opp_players_in_def_third']}")

    return defensive_results, third_control


def example_visualization():
    """Example of creating tactical visualizations."""
    print("\n=== Visualization Example ===")

    # Initialize visualizer
    visualizer = TacticalVisualizer()

    # Example formation data (normalized 0-1 coordinates)
    # This would normally come from your analysis
    sample_formation = {
        'A1': (0.1, 0.1),   # GK
        'A2': (0.2, 0.2),   # RB
        'A3': (0.2, 0.4),   # RCB
        'A4': (0.2, 0.6),   # LCB
        'A5': (0.2, 0.8),   # LB
        'A6': (0.4, 0.3),   # CDM
        'A7': (0.4, 0.2),   # RM
        'A8': (0.4, 0.5),   # CM
        'A9': (0.4, 0.8),   # LM
        'A10': (0.6, 0.2),  # RF
        'A11': (0.6, 0.7)   # LF / ST
    }

    # Create formation plot
    print("Creating formation visualization...")
    fig, ax = visualizer.plot_formation(
        sample_formation,
        team_name="Sample Team"
    )

    # Save the plot
    fig.savefig("sample_formation.png", dpi=300, bbox_inches='tight')
    print("Formation visualization saved as 'sample_formation.png'")

    # Close the plot to free memory
    import matplotlib.pyplot as plt
    plt.close(fig)

    return "Sample visualization created"


def run_all_examples():
    """Run all examples sequentially."""
    print("Football Tactical Analyzer - Usage Examples")
    print("=" * 50)

    try:
        # Run all examples
        events_data = example_event_analysis()
        formation_data = example_formation_analysis()
        pressing_data = example_pressing_analysis()
        network_data, pattern_data = example_passing_network()
        defensive_data, third_control = example_defensive_analysis()
        viz_result = example_visualization()

        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("\nNext steps:")
        print("1. Replace sample data with your actual data")
        print("2. Enhance the models with your proprietary algorithms")
        print("3. Build custom visualizations and reports")
        print("4. Develop the commercial aspects of your product")

    except Exception as e:
        print(f"\nError running examples: {e}")
        print("This is expected if sample data generation fails or dependencies are missing.")
        print("The core library structure is ready for you to build upon.")


if __name__ == "__main__":
    run_all_examples()