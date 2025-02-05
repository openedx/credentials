"""Core views."""

import logging
import uuid

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, login
from django.db import DatabaseError, connection, transaction
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.template import TemplateDoesNotExist
from django.template.loader import select_template
from django.views.generic import View
from edx_django_utils.monitoring import ignore_transaction

from credentials.apps.core.constants import Status


logger = logging.getLogger(__name__)
User = get_user_model()


@transaction.non_atomic_requests
def health(_):
    """Allows a load balancer to verify this service is up.

    Checks the status of the database connection on which this service relies.

    Returns:
        HttpResponse: 200 if the service is available, with JSON data indicating the health of each required service
        HttpResponse: 503 if the service is unavailable, with JSON data indicating the health of each required service

    Example:
        >>> response = requests.get('https://credentials.edx.org/health')
        >>> response.status_code
        200
        >>> response.content
        '{"overall_status": "OK", "detailed_status": {"database_status": "OK", "lms_status": "OK"}}'
    """
    # Ignores health check in performance monitoring so as to not artifically inflate our response time metrics
    ignore_transaction()

    try:
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        database_status = Status.OK
    except DatabaseError:
        database_status = Status.UNAVAILABLE

    overall_status = Status.OK if (database_status == Status.OK) else Status.UNAVAILABLE

    data = {
        "overall_status": overall_status,
        "detailed_status": {
            "database_status": database_status,
        },
    }

    if overall_status == Status.OK:
        return JsonResponse(data)
    return JsonResponse(data, status=503)


class AutoAuth(View):
    """Creates and authenticates a new User with superuser permissions.

    If the ENABLE_AUTO_AUTH setting is not True, returns a 404.
    """

    def get(self, request):
        """
        Create a new User.

        Raises Http404 if auto auth is not enabled.
        """
        if not getattr(settings, "ENABLE_AUTO_AUTH", None):
            raise Http404

        username_prefix = getattr(settings, "AUTO_AUTH_USERNAME_PREFIX", "auto_auth_")

        # Create a new user with staff permissions
        username = password = username_prefix + uuid.uuid4().hex[0:20]
        User.objects.create_superuser(username, email=None, password=password)

        # Log in the new user
        user = authenticate(username=username, password=password)
        login(request, user)

        return redirect("/")


class ThemeViewMixin:
    def add_theme_to_template_names(self, template_names):
        """Prepend the the list of template names with the path of the current theme."""
        theme_template_path = self.request.site.siteconfiguration.theme_name
        themed_template_names = [
            "{theme_path}/{template_name}".format(
                theme_path=theme_template_path, template_name=template_name.strip("/")
            )
            for template_name in template_names
        ]
        template_names = themed_template_names + template_names
        return template_names

    def select_theme_template(self, templates):
        try:
            return select_template(self.add_theme_to_template_names(templates))
        except TemplateDoesNotExist:
            logger.error(f"Could not select template in [{templates}] for theme ")
            raise

    def try_select_theme_template(self, templates):
        """Select a template or return an empty string if the template doesn't exist.
        Provides ability to check if a template exists before including it.
        """
        try:
            return select_template(self.add_theme_to_template_names(templates))
        except TemplateDoesNotExist:
            logger.error(f"Could not find theme template in [{templates}]")
            return ""


def render_500(request, template_name="500.html"):
    """Custom 500 error handler.

    Arguments:
        template_name (template): Template for rendering
    """
    return render(request, template_name, status=500)
