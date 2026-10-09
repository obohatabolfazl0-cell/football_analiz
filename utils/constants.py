"""
Constants for football analysis.
"""

# Standard pitch dimensions (in meters)
PITCH_LENGTH = 105.0  # Length (goal to goal)
PITCH_WIDTH = 68.0    # Width (touchline to touchline)

# Common event types in football data
EVENT_TYPES = {
    'Pass',
    'Shot',
    'Dribble',
    'Tackle',
    'Interception',
    'Pressure',
    'Carry',
    'Ball Receipt*',
    'Ball Recovery',
    'Clearance',
    'Block',
    'Foul Committed',
    'Foul Won',
    'Offside',
    'Yellow Card',
    'Red Card',
    'Corner',
    'Free Kick',
    'Penalty',
    'Kick Off',
    'Goal Keeper',
    'Substitution',
    'Starting XI'
}

# Formation constants
FORMATIONS = {
    '4-3-3': {'defense': 4, 'midfield': 3, 'attack': 3},
    '4-4-2': {'defense': 4, 'midfield': 4, 'attack': 2},
    '3-5-2': {'defense': 3, 'midfield': 5, 'attack': 2},
    '3-4-3': {'defense': 3, 'midfield': 4, 'attack': 3},
    '5-3-2': {'defense': 5, 'midfield': 3, 'attack': 2},
    '4-2-3-1': {'defense': 4, 'midfield': 2, 'attacking_mid': 3, 'attack': 1},
    '4-1-2-1-2': {'defense': 4, 'midfield': 1, 'attacking_mid': 2, 'defensive_mid': 1, 'attack': 2},
    '3-3-4': {'defense': 3, 'midfield': 3, 'attack': 4}
}

# Zones on the pitch (normalized 0-1 coordinates)
PITCH_ZONES = {
    'defensive_third': {'y_min': 0.0, 'y_max': 0.33},
    'middle_third': {'y_min': 0.33, 'y_max': 0.66},
    'attacking_third': {'y_min': 0.66, 'y_max': 1.0},
    'left_wing': {'x_min': 0.0, 'x_max': 0.25},
    'left_halfspace': {'x_min': 0.25, 'x_max': 0.5},
    'center': {'x_min': 0.25, 'x_max': 0.75},  # Actually, this should be more specific
    'right_halfspace': {'x_min': 0.5, 'x_max': 0.75},
    'right_wing': {'x_min': 0.75, 'x_max': 1.0}
}

# More accurate zone definitions
PITCH_ZONES_DETAILED = {
    'defensive_left_wing': {'x_min': 0.0, 'x_max': 0.20, 'y_min': 0.0, 'y_max': 0.33},
    'defensive_left_halfspace': {'x_min': 0.20, 'x_max': 0.40, 'y_min': 0.0, 'y_max': 0.33},
    'defensive_center': {'x_min': 0.40, 'x_max': 0.60, 'y_min': 0.0, 'y_max': 0.33},
    'defensive_right_halfspace': {'x_min': 0.60, 'x_max': 0.80, 'y_min': 0.0, 'y_max': 0.33},
    'defensive_right_wing': {'x_min': 0.80, 'x_max': 1.0, 'y_min': 0.0, 'y_max': 0.33},

    'middle_left_wing': {'x_min': 0.0, 'x_max': 0.20, 'y_min': 0.33, 'y_max': 0.66},
    'middle_left_halfspace': {'x_min': 0.20, 'x_max': 0.40, 'y_min': 0.33, 'y_max': 0.66},
    'middle_center': {'x_min': 0.40, 'x_max': 0.60, 'y_min': 0.33, 'y_max': 0.66},
    'middle_right_halfspace': {'x_min': 0.60, 'x_max': 0.80, 'y_min': 0.33, 'y_max': 0.66},
    'middle_right_wing': {'x_min': 0.80, 'x_max': 1.0, 'y_min': 0.33, 'y_max': 0.66},

    'attacking_left_wing': {'x_min': 0.0, 'x_max': 0.20, 'y_min': 0.66, 'y_max': 1.0},
    'attacking_left_halfspace': {'x_min': 0.20, 'x_max': 0.40, 'y_min': 0.66, 'y_max': 1.0},
    'attacking_center': {'x_min': 0.40, 'x_max': 0.60, 'y_min': 0.66, 'y_max': 1.0},
    'attacking_right_halfspace': {'x_min': 0.60, 'x_max': 0.80, 'y_min': 0.66, 'y_max': 1.0},
    'attacking_right_wing': {'x_min': 0.80, 'x_max': 1.0, 'y_min': 0.66, 'y_max': 1.0}
}

# Pressing intensity thresholds
PRESSING_THRESHOLDS = {
    'low': 0.3,
    'medium': 0.6,
    'high': 0.8
}

# Pass length categories (in meters)
PASS_LENGTH_CATEGORIES = {
    'short': (0, 10),
    'medium': (10, 30),
    'long': (30, 100)  # Up to full pitch length
}