import json
import waffle

from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from credentials.apps.core.views import ThemeViewMixin

from .constants import WAFFLE_FLAG_RECORDS


class RecordsView(LoginRequiredMixin, TemplateView, ThemeViewMixin):
    template_name = 'records.html'

    def _get_programs(self):
        # FIXME: Stop using fake data here, obviously
        return [
            {
                'name': 'Dog Mind Reading',
                'partner': 'DOGx',
                'uuid': 'XXXXXXXX',
            },
            {
                "name": "MIT's Simple XSS <script>alert(\"Attack\")</script>",
                'partner': 'MITx',
                'uuid': 'YYYYYYYY',
            },
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'child_templates': {
                'footer': self.select_theme_template(['_footer.html']),
                'header': self.select_theme_template(['_header.html']),
            },
            'programs': json.dumps(self._get_programs(), sort_keys=True),
            'render_language': self.request.LANGUAGE_CODE,
        })
        return context

    def dispatch(self, request, *args, **kwargs):
        if not waffle.flag_is_active(request, WAFFLE_FLAG_RECORDS):
            raise http.Http404()
        return super().dispatch(request, *args, **kwargs)
