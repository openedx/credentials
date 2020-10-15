BASEDIR=$(dirname $0)

export DJANGO_SETTINGS_MODULE=credentials.settings.local

# Selenium config
export SELENIUM_BROWSER=firefox
export PATH="$PATH:$BASEDIR/../node_modules/geckodriver/bin"

# Bokchoy config
export BOKCHOY_A11Y_CUSTOM_RULES_FILE="$BASEDIR/../node_modules/edx-custom-a11y-rules/lib/custom_a11y_rules.js"
export VERIFY_ACCESSIBILITY="true"
export VERIFY_XSS="true"

# Make sure that if this script stops, we try to clean up the runservers we started
trap cleanup TERM EXIT
cleanup()
{
    # catch existing exit code so we can return it after we shut down the servers
    exit_code=$?
    trap - TERM EXIT
    [ -n "$RUNSERVER_PID" ] && kill "$RUNSERVER_PID" 2>/dev/null
    exit $exit_code
}

# Set QUICK=1 or similar if you are trying to manually iterate
if [ -z "$QUICK" ]; then
    "$BASEDIR"/runserver.sh >/dev/null 2>/dev/null &
    RUNSERVER_PID=$!
    "$BASEDIR"/provision.sh || exit 1
fi

ARGS="$BASEDIR"
if [ "$#" -gt 0 ]; then
    ARGS="$*"
fi

xvfb-run pytest "$ARGS"
