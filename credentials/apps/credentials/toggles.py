"""
Waffle switches for the credentials app.
"""
from edx_toggles.toggles import WaffleSwitch


# .. toggle_name: credentials.custom_program_certificate_templates
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: When enabled, the credentials service checks the
#      ProgramCertificateTemplate model for a custom HTML template before
#      falling back to file-based certificate templates. Allows per-program,
#      per-type, and per-organization certificate customization via Django admin
#      without touching files or rebuilding images.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2026-03-26
CUSTOM_PROGRAM_CERTIFICATE_TEMPLATES = WaffleSwitch(
    "credentials.custom_program_certificate_templates",
    module_name=__name__,
)
