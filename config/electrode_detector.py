"""
Electrode detector configuration file
"""


class DogParameters:
    KSIZE = 39
    SIGMA = 16
    FACTOR = 1.1
    THRESHOLD_LEVEL = 1


class HoughParameters:
    PARAM1 = 5
    PARAM2 = 7.5
    MIN_DISTANCE = 100
    MIN_RADIUS = 12
    MAX_RADIUS = 20
