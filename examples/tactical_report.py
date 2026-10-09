"""
Example of generating a tactical report from match analysis.
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
import json
from datetime import datetime


def generate_tactical_report(match_id: str = "sample_match_001") -> dict:
    """
    Generate a comprehensive tactical report for a match.

    Args:
        match_id: Identifier for the match being analyzed

    Returns:
        Dictionary containing the tactical report
    """
    print(f"Generating tactical report for match: {match_id}")
    print("-" * 50)

    # Load data
    events = load_sample_event_data()
    tracking = load_sample_tracking_data()

    # Initialize analyzers
    tactical_analyzer = TacticalAnalyzer()
    event_analyzer = EventAnalyzer()
    tracking_analyzer = TrackingAnalyzer()
    visualizer = TacticalVisualizer()
    formation_detector = FormationDetector()
    pressing_analyzer = PressingAnalyzer()
    passing_analyzer = PassingNetworkAnalyzer()
    defensive_analyzer = DefensiveShapeAnalyzer()

    # Analyze both teams
    teams = events['team'].unique()
    team_a_name = teams[0] if len(teams) > 0 else "Team A"
    team_b_name = teams[1] if len(teams) > 1 else "Team B"

    # Get players for each team
    team_a_players = events[events['team'] == team_a_name]['player_id'].unique()
    team_b_players = events[events['team'] == team_b_name]['player_id'].unique()

    # Get tracking data for each team
    team_a_tracking = tracking[tracking['team'] == team_a_name]
    team_b_tracking = tracking[tracking['team'] == team_b_name]

    # Build the report
    report = {
        "match_info": {
            "match_id": match_id,
            "analysis_date": datetime.now().isoformat(),
            "teams": [team_a_name, team_b_name],
            "data_quality": {
                "events_analyzed": len(events),
                "tracking_records": len(tracking)
            }
        },
        "team_analysis": {}
    }

    # Analyze each team
    for team_name, team_players, team_tracking in [
        (team_a_name, team_a_players, team_a_tracking),
        (team_b_name, team_b_players, team_b_tracking)
    ]:
        print(f"Analyzing {team_name}...")

        team_events = events[events['team'] == team_name]

        # Get ball position data (simplified)
        # In reality, you'd have explicit ball tracking
        ball_x = tracking[tracing['player_id'] == 'ball']['x'].mean() if 'ball' in tracking['player_id'].values else PITCH_LENGTH/2
        ball_y = tracking[tracing['player_id'] == 'ball']['y'].mean() if 'ball' in tracking['player_id'].values else PITCH_WIDTH/2
        ball_position = tracking[tracking['player_id'] == 'ball'][['timestamp', 'x', 'y']].copy() if 'ball' in tracking['player_id'].values else \
                       pd.DataFrame({'timestamp': team_tracking['timestamp'].unique(), 'x': ball_x, 'y': ball_y})

        # Formation analysis
        formation_result = formation_detector.detect_formation_kmeans(team_tracking)

        # Passing network analysis
        team_passes = event_analyzer.process_passes(team_events)
        passing_results = passing_analyzer.analyze_network(team_passes, team_players)
        passing_patterns = passing_analyzer.analyze_passing_patterns(team_passes, team_players)

        # Pressing analysis
        pressing_results = pressing_analyzer.analyze_pressing_phases(
            team_tracking,
            tracking[tracking['team'] != team_name],  # Opponent tracking
            ball_position
        )

        # Defensive analysis
        # Identify defenders (simplified: players with lowest average y position)
        if len(team_tracking) > 0:
            avg_positions = team_tracking.groupby('player_id')[['x', 'y']].mean().reset_index()
            avg_positions = avg_positions.sort_values('y')
            n_defenders = max(3, len(avg_positions) // 3)  # At least 3, or roughly 1/3 of team
            defender_ids = avg_positions.head(n_defenders)['player_id'].tolist()
            defensive_tracking = team_tracking[team_tracking['player_id'].isin(defender_ids)]
        else:
            defensive_tracking = pd.DataFrame(columns=team_tracking.columns)

        defensive_results = defensive_analyzer.analyze_defensive_line(defensive_tracking)
        third_control = defensive_analyzer.defensive_third_control(
            defensive_tracking,
            tracking[tracking['team'] != team_name]
        )
        pressing_resistance = defensive_analyzer.pressing_resistance(
            defensive_tracking,
            tracking[tracking['team'] != team_name],
            ball_position
        )

        # Event-based summaries
        defensive_actions = event_analyzer.defensive_actions_summary(team_events, team_players)
        attacking_actions = event_analyzer.attacking_actions_summary(team_events, team_players)

        # Compile team analysis
        report["team_analysis"][team_name] = {
            "formation": {
                "name": formation_result['formation_name'],
                "line_counts": formation_result['line_counts'],
                "width": formation_result['overall_width'],
                "depth": formation_result['overall_depth'],
                "quality": formation_result['formation_quality']
            },
            "passing": {
                "total_passes": passing_results['total_passes'],
                "completion_rate": passing_results['completion_rate'],
                "avg_pass_length": passing_results['avg_pass_length'],
                "network_density": passing_results['network_density'],
                "key_passers": passing_results['key_passers'],
                "patterns": {
                    "short_pass_ratio": passing_patterns['short_pass_ratio'],
                    "long_pass_ratio": passing_patterns['long_pass_ratio'],
                    "forward_pass_ratio": passing_patterns['forward_pass_ratio'],
                    "left_right_balance": passing_patterns['left_right_balance']
                }
            },
            "pressing": {
                "overall_intensity": pressing_results['overall_pressing_intensity'],
                "defensive_third": pressing_results.get('defensive_third_pressing', 0),
                "middle_third": pressing_results.get('middle_third_pressing', 0),
                "attacking_third": pressing_results.get('attacking_third_pressing', 0)
            },
            "defensive": {
                "line_height": defensive_results['defensive_line_height'],
                "line_width": defensive_results['defensive_line_width'],
                "compactness": defensive_results['defensive_compactness'],
                "defensive_third_control": third_control['defensive_third_control'],
                "pressing_resistance": pressing_resistance['pressing_resistance'],
                "pressing_resistance_rating": pressing_resistance['pressing_resistance_rating']
            },
            "actions": {
                "defensive": defensive_actions,
                "attacking": attacking_actions
            }
        }

    # Generate insights and recommendations
    report["insights"] = _generate_insights(report)
    report["recommendations"] = _generate_recommendations(report)

    return report


def _generate_insights(report: dict) -> list:
    """
    Generate tactical insights from the analysis.

    Args:
        report: The tactical report dictionary

    Returns:
        List of insight strings
    """
    insights = []

    teams = list(report["team_analysis"].keys())
    if len(teams) < 2:
        return insights

    team_a, team_b = teams[0], teams[1]
    a_data = report["team_analysis"][team_a]
    b_data = report["team_analysis"][team_b]

    # Formation insights
    a_formation = a_data['formation']['name']
    b_formation = b_data['formation']['name']
    if a_formation != b_formation:
        insights.append(
            f"Formation mismatch: {team_a} plays {a_formation} while {team_b} uses {b_formation}. "
            f"This could create tactical advantages/disadvantages in specific zones."
        )

    # Pressing insights
    a_press = a_data['pressing']['overall_intensity']
    b_press = b_data['pressing']['overall_intensity']
    if abs(a_press - b_press) > 0.2:
        higher_pressing_team = team_a if a_press > b_press else team_b
        lower_pressing_team = team_b if a_press > b_press else team_a
        insights.append(
            f"{higher_pressing_team} applies significantly more pressure ({max(a_press, b_press):.2f}) "
            f"than {lower_pressing_team} ({min(a_press, b_press):.2f}). "
            f"This could lead to more turnovers in {higher_pressing_team}'s favor."
        )

    # Passing insights
    a_completion = a_data['passing']['completion_rate']
    b_completion = b_data['passing']['completion_rate']
    if abs(a_completion - b_completion) > 0.1:
        better_passing_team = team_a if a_completion > b_completion else team_b
        worse_passing_team = team_b if a_completion > b_completion else team_a
        insights.append(
            f"{better_passing_team} has superior passing accuracy ({max(a_completion, b_completion):.1%}) "
            f"compared to {worse_passing_team} ({min(a_completion, b_completion):.1%}). "
            f"This suggests better ball control and build-up play."
        )

    # Defensive insights
    a_compact = a_data['defensive']['compactness']
    b_compact = b_data['defensive']['compactness']
    if abs(a_compact - b_compact) > 0.15:
        more_compact_team = team_a if a_compact > b_compact else team_b
        less_compact_team = team_b if a_compact > b_compact else team_a
        insights.append(
            f"{more_compact_team} maintains a more compact defensive shape "
            f"(compactness: {max(a_compact, b_compact):.2f}) than {less_compact_team} "
            f"(compactness: {min(a_compact, b_compact):.2f}). "
            f"This may make it harder for opponents to find space between lines."
        )

    # Third control insights
    a_third = a_data['defensive']['defensive_third_control']
    b_third = b_data['defensive']['defensive_third_control']
    if abs(a_third - b_third) > 0.2:
        better_defending_team = team_a if a_third > b_third else team_b
        weaker_defending_team = team_b if a_third > b_third else team_a
        insights.append(
            f"{better_defending_team} controls their defensive third better "
            f"({max(a_third, b_third):.2f}) than {weaker_defending_team} "
            f"({min(a_third, b_third):.2f}). "
            f"This suggests {better_defending_team} is more effective at preventing "
            f"opponent incursions into dangerous areas."
        )

    # If no specific insights, add a general one
    if not insights:
        insights.append(
            "Teams show relatively balanced tactical profiles in the analyzed metrics. "
            "The match may be decided by individual performances, set pieces, or "
            "moments of individual brilliance rather than systemic tactical advantages."
        )

    return insights


def _generate_recommendations(report: dict) -> list:
    """
    Generate tactical recommendations based on the analysis.

    Args:
        report: The tactical report dictionary

    Returns:
        List of recommendation strings
    """
    recommendations = []

    teams = list(report["team_analysis"].keys())
    if len(teams) < 2:
        return recommendations

    team_a, team_b = teams[0], teams[1]
    a_data = report["team_analysis"][team_a]
    b_data = report["team_analysis"][team_b]

    # Pressing recommendations
    a_press = a_data['pressing']['overall_intensity']
    b_press = b_data['pressing']['overall_intensity']
    if a_press < 0.4 and b_press < 0.4:
        recommendations.append(
            "Both teams show low pressing intensity. Consider implementing "
            "a coordinated press to disrupt opponent build-up and force turnovers "
            "in advantageous areas of the pitch."
        )
    elif a_press > 0.7 or b_press > 0.7:
        recommendations.append(
            "High pressing intensity detected. Ensure players understand "
            "pressing triggers and have the fitness to sustain this approach "
            "throughout the match to avoid being vulnerable to counter-attacks."
        )

    # Passing recommendations
    a_completion = a_data['passing']['completion_rate']
    b_completion = b_data['passing']['completion_rate']
    if a_completion < 0.7 or b_completion < 0.7:
        low_completion_team = team_a if a_completion < 0.7 else team_b
        recommendations.append(
            f"{low_completion_team}'s pass completion rate is below 70%. "
            f"Focus on improving passing accuracy through technical training "
            f"and better decision-making under pressure."
        )

    # Defensive recommendations
    a_third_control = a_data['defensive']['defensive_third_control']
    b_third_control = b_data['defensive']['defensive_third_control']
    if a_third_control < 0.4 or b_third_control < 0.4:
        weak_defending_team = team_a if a_third_control < 0.4 else team_b
        recommendations.append(
            f"{weak_defending_team} struggles to control their defensive third "
            f"(control: {min(a_third_control, b_third_control):.2f}). "
            f"Consider dropping the defensive line deeper or increasing "
            f"midfield compactness to protect this zone."
        )

    # Formation flexibility recommendations
    a_quality = a_data['formation']['quality']
    b_quality = b_data['formation']['quality']
    if a_quality < 0.5 or b_quality < 0.5:
        low_quality_team = team_a if a_quality < 0.5 else team_b
        recommendations.append(
            f"{low_quality_team}'s formation shows low structural quality "
            f"(quality score: {min(a_quality, b_quality):.2f}). "
            f"Work on maintaining positional discipline and understanding "
            f"of tactical roles within the formation."
        )

    # If no specific recommendations, add a general one
    if not recommendations:
        recommendations.append(
            "Tactical analysis shows both teams are well-organized. "
            "Look for marginal gains in set-piece execution, transition play, "
            "and individual match-ups to gain competitive advantage."
        )

    return recommendations


def save_report(report: dict, filename: str = "tactical_report.json"):
    """
    Save the tactical report to a JSON file.

    Args:
        report: The tactical report dictionary
        filename: Name of the file to save to
    """
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    print(f"Tactical report saved to {filename}")


def print_report_summary(report: dict):
    """
    Print a human-readable summary of the tactical report.

    Args:
        report: The tactical report dictionary
    """
    print("\n" + "="*60)
    print("TACTICAL REPORT SUMMARY")
    print("="*60)

    print(f"Match ID: {report['match_info']['match_id']}")
    print(f"Analysis Date: {report['match_info']['analysis_date']}")
    print(f"Teams: {', '.join(report['match_info']['teams'])}")
    print(f"Events Analyzed: {report['match_info']['data_quality']['events_analyzed']}")
    print(f"Tracking Records: {report['match_info']['data_quality']['tracking_records']}")

    print("\n" + "-"*60)
    print("TEAM ANALYSIS")
    print("-"*60)

    for team_name, team_data in report["team_analysis"].items():
        print(f"\n{team_name.upper()}:")
        print(f"  Formation: {team_data['formation']['name']} "
              f"(Quality: {team_data['formation']['quality']:.2f})")
        print(f"  Passing: {team_data['passing']['completion_rate']:.1%} completion "
              f"({team_data['passing']['avg_pass_length']:.1f}m avg)")
        print(f"  Pressing: {team_data['pressing']['overall_intensity']:.2f} intensity")
        print(f"  Defense: {team_data['defensive']['compactness']:.2f} compactness "
              f"({team_data['defensive']['defensive_third_control']:.2f} third control)")

    print("\n" + "-"*60)
    print("KEY INSIGHTS")
    print("-"*60)
    for i, insight in enumerate(report["insights"], 1):
        print(f"{i}. {insight}")

    print("\n" + "-"*60)
    print("RECOMMENDATIONS")
    print("-"*60)
    for i, rec in enumerate(report["recommendations"], 1):
        print(f"{i}. {rec}")

    print("\n" + "="*60)


if __name__ == "__main__":
    # Generate and display the report
    report = generate_tactical_report("sample_match_001")
    print_report_summary(report)

    # Save the report
    save_report(report, "tactical_report_sample.json")

    print(f"\nFull report saved as JSON: tactical_report_sample.json")
    print("You can now:")
    print("1. Replace sample data with your actual match data")
    print("2. Enhance the analysis with your proprietary algorithms")
    print("3. Customize the report format for your clients")
    print("4. Build automated report generation for multiple matches")