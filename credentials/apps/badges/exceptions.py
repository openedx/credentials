"""
Badges exceptions.
"""


class BadgesError(Exception):
    """
    Badges generic exception.
    """

    pass


class BadgesProcessingError(BadgesError):
    """
    Exception raised for errors that occur during badge processing.
    """

    pass


class StopEventProcessing(BadgesProcessingError):
    """
    Exception raised to stop processing an event due to a specific condition.
    """

    pass
