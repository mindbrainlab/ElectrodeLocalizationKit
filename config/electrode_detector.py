"""
Electrode detector configuration file
"""

class DogParameters:
    KSIZE = 35
    SIGMA = 12
    FACTOR = 1.1
    THRESHOLD_LEVEL = 1
    
class HoughParameters:
    PARAM1 = 5
    PARAM2 = 12
    MIN_DISTANCE = 100
    MIN_RADIUS = 10
    MAX_RADIUS = 30