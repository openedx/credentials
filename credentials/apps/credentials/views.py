"""
Credentials rendering views.
"""
import logging

from django.views.generic import TemplateView


logger = logging.getLogger(__name__)


class RenderCredential(TemplateView):
    """ Certificate rendering view."""
    template_name = 'credentials/view_certificate.html'

    def get_context_data(self, **kwargs):
        context = super(RenderCredential, self).get_context_data(**kwargs)

        context.update({
            'uuid': kwargs.get('uuid'),
        })

        return context
