"""
Credly specific utilities.
"""


def get_credly_api_base_url(settings):
    """
    Determines the base URL for the Credly API based on application settings.

    Parameters:
    - settings: A configuration object containing the application's settings,
                including those specific to Credly API integration.

    Returns:
    - str:  The base URL for the Credly API. This will be the URL for the sandbox
            environment if `USE_SANDBOX` is set to a truthy value in the configuration;
            otherwise, it will be the production environment's URL.
    """

    credly_config = settings.BADGES_CONFIG["credly"]

    if credly_config.get("USE_SANDBOX"):
        return credly_config["CREDLY_SANDBOX_API_BASE_URL"]

    return credly_config["CREDLY_API_BASE_URL"]


def get_credly_base_url(settings):
    """
    Determines the base URL for the Credly service based on application settings.

    Parameters:
    - settings: A configuration object containing the application's settings.

    Returns:
    - str:  The base URL for the Credly service (web site).
            This will be the URL for the sandbox environment if `USE_SANDBOX` is
            set to a truthy value in the configuration;
            otherwise, it will be the production environment's URL.
    """

    credly_config = settings.BADGES_CONFIG["credly"]

    if credly_config.get("USE_SANDBOX"):
        return credly_config["CREDLY_SANDBOX_BASE_URL"]

    return credly_config["CREDLY_BASE_URL"]
