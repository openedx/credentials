BASEDIR=$(dirname $0)

export SELENIUM_BROWSER=firefox
export PATH="$PATH:$BASEDIR/../node_modules/geckodriver/bin"
export DJANGO_SETTINGS_MODULE=credentials.settings.local
export BOKCHOY_A11Y_CUSTOM_RULES_FILE="$BASEDIR/../node_modules/edx-custom-a11y-rules/lib/custom_a11y_rules.js"

# Make sure that if this script stops, we try to clean up the runservers we started
trap cleanup TERM EXIT
cleanup()
{
    trap - TERM EXIT
    [ -n "$RUNSERVER_PID" ] && kill "$RUNSERVER_PID" 2>/dev/null
    exit 0
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
