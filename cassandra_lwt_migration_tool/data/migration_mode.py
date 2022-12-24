import enum


class MigrationMode(enum.IntEnum):
    """
    Represents the mode of operation of the tool.
    """

    CHECK_TARGETING_NODES = 0
    CAPTURE_BASELINE = 1
    CHECK_COMPLETION = 2
    CHECK_BASELINE_COMPLETION = 3
