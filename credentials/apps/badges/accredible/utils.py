"""
Accredible utility functions.
"""


def get_accredible_api_base_url(settings) -> str:
    """
    Determines the base URL for the Accredible service based on application settings.

    Parameters:
    - settings: A configuration object containing the application's settings.

    Returns:
    - str:  The base URL for the Accredible service (web site).
            This will be the URL for the sandbox environment if `USE_SANDBOX` is
            set to a truthy value in the configuration;
            otherwise, it will be the production environment's URL.
    """
    accredible_config = settings.BADGES_CONFIG["accredible"]

    if accredible_config.get("USE_SANDBOX"):
        return accredible_config["ACCREDIBLE_SANDBOX_API_BASE_URL"]

    return accredible_config["ACCREDIBLE_API_BASE_URL"]


def get_accredible_base_url(settings) -> str:
    """
    Determines the base URL for the Accredible service based on application settings.

    Parameters:
    - settings: A configuration object containing the application's settings.

    Returns:
    - str:  The base URL for the Accredible service (web site).
            This will be the URL for the sandbox environment if `USE_SANDBOX` is
            set to a truthy value in the configuration;
            otherwise, it will be the production environment's URL.
    """
    accredible_config = settings.BADGES_CONFIG["accredible"]

    if accredible_config.get("USE_SANDBOX"):
        return accredible_config["ACCREDIBLE_SANDBOX_BASE_URL"]

    return accredible_config["ACCREDIBLE_BASE_URL"]
