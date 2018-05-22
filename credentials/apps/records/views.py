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


class ProgramRecordView(LoginRequiredMixin, TemplateView, ThemeViewMixin):
    template_name = 'programs.html'

    def _get_record(self):
        # FIXME: Stop using fake data here, can reconsider data format as well
        return {
            'learner': {
                'full_name': 'Firsty Lasty',
                'username': 'edxIsGood',
                'email': 'edx@example.com',
            },
            'program': {
                'name': 'Test Program ',
                'school': 'TestX'
            },
            'platform_name': 'edX',
            'grades': [
                {
                    'name': 'Course 1',
                    'school': 'TestX',
                    'attempts': 1,
                    'course_id': 'course1x',
                    'issue_date': '2018-01-01',
                    'percent_grade': '98%',
                    'letter_grade': 'A'
                },
                {
                    'name': 'Course 2',
                    'school': 'TestX',
                    'attempts': 1,
                    'course_id': 'course2x',
                    'issue_date': '2018-01-01',
                    'percent_grade': '98%',
                    'letter_grade': 'A'
                },
                {
                    'name': 'Course 3',
                    'school': 'TestX',
                    'attempts': 1,
                    'course_id': 'course3x',
                    'issue_date': '2018-01-01',
                    'percent_grade': '98%',
                    'letter_grade': 'A'
                },
                {
                    'name': 'Course 4',
                    'school': 'TestX',
                    'attempts': 1,
                    'course_id': 'course4x',
                    'issue_date': '2018-01-01',
                    'percent_grade': '98%',
                    'letter_grade': 'A'
                },
                {
                    'name': 'Course 5',
                    'school': 'TestX',
                    'attempts': 1,
                    'course_id': 'course5x',
                    'issue_date': '2018-01-01',
                    'percent_grade': '98%',
                    'letter_grade': 'A'
                }
            ]
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        record = self._get_record()
        context.update({
            'child_templates': {
                'footer': self.select_theme_template(['_footer.html']),
                'header': self.select_theme_template(['_header.html']),
            },
            'record': json.dumps(record, sort_keys=True),
            'program_name': record.get('program', {}).get('name'),
            'render_language': self.request.LANGUAGE_CODE,
        })
        return context

    def dispatch(self, request, *args, **kwargs):
        if not waffle.flag_is_active(request, WAFFLE_FLAG_RECORDS):
            raise http.Http404()
        return super().dispatch(request, *args, **kwargs)
