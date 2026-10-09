"""
Football Tactical Analyzer
A Python library for football match analysis with deep tactical concepts integration.
"""

from .analyzer.tactical import TacticalAnalyzer
from .analyzer.events import EventAnalyzer
from .analyzer.tracking import TrackingAnalyzer
from .analyzer.visualization import TacticalVisualizer
from .models.formations import FormationDetector
from .models.pressing import PressingAnalyzer
from .models.passing_networks import PassingNetworkAnalyzer
from .models.defensive_shape import DefensiveShapeAnalyzer
from .data.loaders import load_sample_event_data, load_sample_tracking_data

__version__ = "0.1.0"
__author__ = "Your Name"
__description__ = "A Python library for football tactical analysis"

# Make key classes easily accessible
__all__ = [
    "TacticalAnalyzer",
    "EventAnalyzer",
    "TrackingAnalyzer",
    "TacticalVisualizer",
    "FormationDetector",
    "PressingAnalyzer",
    "PassingNetworkAnalyzer",
    "DefensiveShapeAnalyzer",
    "load_sample_event_data",
    "load_sample_tracking_data"
]