"""
Command-line interface for the football tactical analyzer.
"""

import argparse
import sys
from .tactical import TacticalAnalyzer
from .events import EventAnalyzer
from .tracking import TrackingAnalyzer
from .visualization import TacticalVisualizer
from data.loaders import load_sample_event_data, load_sample_tracking_data
from models.formations import FormationDetector
from models.pressing import PressingAnalyzer
from models.passing_networks import PassingNetworkAnalyzer
from models.defensive_shape import DefensiveShapeAnalyzer
from examples.tactical_report import generate_tactical_report, print_report_summary


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Football Tactical Analyzer - Analyze football matches with tactical concepts"
    )
    parser.add_argument(
        "--example",
        action="store_true",
        help="Run example analyses"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a tactical report"
    )
    parser.add_argument(
        "--viz",
        action="store_true",
        help="Create sample visualizations"
    )
    parser.add_argument(
        "--data",
        choices=["event", "tracking"],
        help="Load and display sample data info"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="tactical_report.json",
        help="Output file for reports (default: tactical_report.json)"
    )

    args = parser.parse_args()

    if args.example:
        from examples.basic_analysis import run_all_examples
        run_all_examples()
    elif args.report:
        print("Generating tactical report...")
        report = generate_tactical_report("cli_generated_report")
        print_report_summary(report)
        # Save report
        import json
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nFull report saved to {args.output}")
    elif args.viz:
        from examples.basic_analysis import example_visualization
        example_visualization()
    elif args.data:
        if args.data == "event":
            events = load_sample_event_data()
            print(f"Sample event data: {len(events)} events")
            print(f"Columns: {list(events.columns)}")
            print(f"Event types: {events['event_type'].unique()}")
            print(f"Teams: {events['team'].unique()}")
        elif args.data == "tracking":
            tracking = load_sample_tracking_data()
            print(f"Sample tracking data: {len(tracking)} records")
            print(f"Columns: {list(tracking.columns)}")
            print(f"Teams: {tracking['team'].unique()}")
            print(f"Time range: {tracking['timestamp'].min():.1f} - {tracking['timestamp'].max():.1f} seconds")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()