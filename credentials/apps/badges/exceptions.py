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


class BadgeProviderError(BadgesError):
    """
    Exception raised for errors that occur during badge API client processing.

    Args:
        message (str): Error description.
        status_code (int, optional): HTTP status code of the failed provider response, if any.
    """

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code
