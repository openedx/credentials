"""
Issuance module.
"""


class IssuanceException(Exception):
    """
    Outlines a general error during a verifiable credential issuance.
    """

    def __init__(self, detail=None):
        self.detail = detail

    def __str__(self):
        return str(self.detail)
