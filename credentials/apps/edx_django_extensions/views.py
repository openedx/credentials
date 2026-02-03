import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

logger = logging.getLogger(__name__)


class ManagementView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "management.html"

    def test_func(self):
        return self.request.user.is_superuser

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        if action == "clear_cache":
            cache.clear()
            logger.info("Cache cleared by %s.", request.user.username)
            messages.add_message(request, messages.SUCCESS, _("Cache cleared."))
        else:
            messages.add_message(request, messages.ERROR, _("{action} is not a valid action.").format(action=action))

        return self.get(request)
