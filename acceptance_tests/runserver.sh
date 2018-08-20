export DEBUG_TOOLBAR=0
export DJANGO_SETTINGS_MODULE=credentials.settings.local

trap cleanup TERM EXIT
cleanup()
{
    trap - TERM EXIT
    pkill -f 'runserver localhost:19150' || true
}

# First, clean any existing runservers just to be safe
cleanup

# Use port 19150 instead of 18150 to avoid any existing servers
./manage.py runserver localhost:19150
