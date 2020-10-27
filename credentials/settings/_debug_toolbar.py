# DJANGO DEBUG TOOLBAR CONFIGURATION
import os

from credentials.settings.utils import str2bool

DEBUG_TOOLBAR = str2bool(os.environ.get('DEBUG_TOOLBAR', True))
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': (lambda __: DEBUG_TOOLBAR),
}
# END DJANGO DEBUG TOOLBAR CONFIGURATION
