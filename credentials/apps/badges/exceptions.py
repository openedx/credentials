"""
Badges exceptions.
"""


class BadgesError(Exception):
    """
    Badges generic exception.
    """


class BadgesProcessingError(BadgesError):
    """
    Exception raised for errors that occur during badge processing.
    """


class StopEventProcessing(BadgesProcessingError):
    """
    Exception raised to stop processing an event due to a specific condition.
    """
