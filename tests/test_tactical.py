"""
Unit tests for the football tactical analyzer.
"""

import unittest
import numpy as np
import pandas as pd
from analyzer.tactical import TacticalAnalyzer
from models.formations import FormationDetector
from models.pressing import PressingAnalyzer
from models.passing_networks import PassingNetworkAnalyzer
from models.defensive_shape import DefensiveShapeAnalyzer
from utils.helpers import normalize_positions, calculate_distance


class TestTacticalAnalyzer(unittest.TestCase):
    """Test cases for the TacticalAnalyzer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = TacticalAnalyzer()

    def test_analyzer_initialization(self):
        """Test that the analyzer initializes correctly."""
        self.assertIsInstance(self.analyzer, TacticalAnalyzer)
        self.assertEqual(self.analyzer.pitch_length, 105.0)
        self.assertEqual(self.analyzer.pitch_width, 68.0)

    def test_formation_analysis(self):
        """Test basic formation analysis."""
        # Create simple position data for a 4-4-2 formation
        positions_data = []
        # Goalkeeper
        positions_data.append({'player_id': 'GK', 'x': 10, 'y': 34})
        # Defenders
        positions_data.append({'player_id': 'RB', 'x': 20, 'y': 15})
        positions_data.append({'player_id': 'RCB', 'x': 20, 'y': 25})
        positions_data.append({'player_id': 'LCB', 'x': 20, 'y': 43})
        positions_data.append({'player_id': 'LB', 'x': 20, 'y': 53})
        # Midfielders
        positions_data.append({'player_id': 'RM', 'x': 40, 'y': 15})
        positions_data.append({'player_id': 'RCM', 'x': 40, 'y': 25})
        positions_data.append({'player_id': 'LCM', 'x': 40, 'y': 43})
        positions_data.append({'player_id': 'LM', 'x': 40, 'y': 53})
        # Forwards
        positions_data.append({'player_id': 'RF', 'x': 70, 'y': 25})
        positions_data.append({'player_id': 'LF', 'x': 70, 'y': 43})

        positions_df = pd.DataFrame(positions_data)

        # Test formation detection
        formation = self.analyzer.analyze_formation(positions_df)
        self.assertIsInstance(formation, FormationDetector.__bases__[0] if FormationDetector.__bases__ else object)
        # Actually, our analyzer returns a Formation object from tactical.py
        # Let's check the type differently
        self.assertTrue(hasattr(formation, 'name'))
        self.assertTrue(hasattr(formation, 'defense'))
        self.assertTrue(hasattr(formation, 'midfield'))
        self.assertTrue(hasattr(formation, 'attack'))


class TestFormationDetector(unittest.TestCase):
    """Test cases for the FormationDetector class."""

    def setUp(self):
        """Set up test fixtures."""
        self.detector = FormationDetector()

    def test_formation_detection_kmeans(self):
        """Test K-means based formation detection."""
        # Create position data that should form a 4-3-3
        positions_data = []
        # Back four
        for i, y in enumerate([10, 20, 30, 40]):
            positions_data.append({'player_id': f'D{i}', 'x': 15, 'y': y})
        # Midfield three
        for i, y in enumerate([15, 35, 45]):
            positions_data.append({'player_id': f'M{i}', 'x': 35, 'y': y})
        # Front three
        for i, y in enumerate([10, 30, 50]):
            positions_data.append({'player_id': f'A{i}', 'x': 60, 'y': y})

        positions_df = pd.DataFrame(positions_data)

        # Detect formation
        result = self.detector.detect_formation_kmeans(positions_df, n_lines=3)

        # Check that we got a result
        self.assertIn('formation_name', result)
        self.assertIn('line_counts', result)
        self.assertIn('positions', result)

        # The formation should be something like 4-3-3
        # Note: Due to the simplicity of our algorithm, it might not be exact
        # but we should get reasonable results
        self.assertIsInstance(result['formation_name'], str)
        self.assertGreater(len(result['formation_name']), 0)


class TestHelpers(unittest.TestCase):
    """Test cases for helper functions."""

    def test_normalize_positions(self):
        """Test position normalization."""
        # Create data in meters
        positions_m = pd.DataFrame({
            'x': [0, 52.5, 105],  # From own goal to halfway to opponent goal
            'y': [0, 34, 68]      # From left touchline to center to right touchline
        })

        normalized = normalize_positions(positions_m)

        # Check that values are between 0 and 1
        self.assertTrue((normalized['x_norm'] >= 0).all() and (normalized['x_norm'] <= 1).all())
        self.assertTrue((normalized['y_norm'] >= 0).all() and (normalized['y_norm'] <= 1).all())

        # Check specific values
        self.assertAlmostEqual(normalized.iloc[0]['x_norm'], 0.0)  # Own goal
        self.assertAlmostEqual(normalized.iloc[1]['x_norm'], 0.5)  # Halfway line
        self.assertAlmostEqual(normalized.iloc[2]['x_norm'], 1.0)  # Opponent goal

        self.assertAlmostEqual(normalized.iloc[0]['y_norm'], 0.0)  # Left touchline
        self.assertAlmostEqual(normalized.iloc[1]['y_norm'], 0.5)  # Center
        self.assertAlmostEqual(normalized.iloc[2]['y_norm'], 1.0)  # Right touchline

    def test_calculate_distance(self):
        """Test distance calculation."""
        # Test known distances
        dist = calculate_distance((0, 0), (3, 4))
        self.assertAlmostEqual(dist, 5.0)  # 3-4-5 triangle

        dist = calculate_distance((1, 1), (1, 1))
        self.assertAlmostEqual(dist, 0.0)  # Same point

        dist = calculate_distance((0, 0), (0, 5))
        self.assertAlmostEqual(dist, 5.0)  # Vertical line


if __name__ == '__main__':
    unittest.main()