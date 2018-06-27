import json
from collections import defaultdict

import waffle
from django import http
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, View

from credentials.apps.catalog.models import CourseRun, Program
from credentials.apps.core.models import User
from credentials.apps.core.views import ThemeViewMixin
from credentials.apps.credentials.models import CourseCertificate, ProgramCertificate, UserCredential
from credentials.apps.records.models import ProgramCertRecord, UserGrade

from .constants import WAFFLE_FLAG_RECORDS


class RecordsView(LoginRequiredMixin, TemplateView, ThemeViewMixin):
    template_name = 'records.html'

    def _get_programs(self, request):
        user = request.user
        # Get the content types for course and program certs, query for both in single query
        course_cert_content_types = ContentType.objects.filter(
            app_label='credentials',
            model__in=['coursecertificate', 'programcertificate']
        )
        course_certificate_type = None
        program_certificate_type = None
        for course_cert_content_type in course_cert_content_types:
            if course_cert_content_type.model == 'coursecertificate':
                course_certificate_type = course_cert_content_type
            elif course_cert_content_type.model == 'programcertificate':
                program_certificate_type = course_cert_content_type

        # Get all user credentials, then sort them out to course/programs
        user_credentials = UserCredential.objects.filter(
            username=user.username,
            credential_content_type__in=course_cert_content_types
        )
        course_credentials = []
        program_credentials = []
        for credential in user_credentials:
            if credential.credential_content_type_id == course_certificate_type.id:
                course_credentials.append(credential)
            elif credential.credential_content_type_id == program_certificate_type.id:
                program_credentials.append(credential)

        # Using the course credentials, get the programs associated with them via course runs
        course_credential_ids = map(lambda course_credential: course_credential.credential_id, course_credentials)
        course_certificates = CourseCertificate.objects.filter(id__in=course_credential_ids)
        course_run_keys = map(lambda course_certificate: course_certificate.course_id, course_certificates)
        course_runs = CourseRun.objects.filter(key__in=course_run_keys)
        programs = Program.objects.filter(course_runs__in=course_runs).distinct().prefetch_related(
            'authoring_organizations'
        )

        # Get the completed programs and a UUID set using the program_credentials
        program_credential_ids = map(lambda program_credential: program_credential.credential_id, program_credentials)
        program_certificates = ProgramCertificate.objects.filter(id__in=program_credential_ids)
        completed_programs = dict({program_certificate.program_uuid: program_certificate
                                   for program_certificate in program_certificates})

        return [
            {
                'name': program.title,
                'partner': ', '.join(program.authoring_organizations.values_list('name', flat=True)),
                'uuid': str(program.uuid),
                'progress': _('In Progress') if program.uuid not in completed_programs else _(
                    'Completed at {completed_date}'
                ).format(completed_date=completed_programs[program.uuid].modified)
            } for program in programs]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        site_configuration = request.site.siteconfiguration

        records_help_url = site_configuration.records_help_url if site_configuration else ''

        context.update({
            'child_templates': {
                'footer': self.select_theme_template(['_footer.html']),
                'header': self.select_theme_template(['_header.html']),
            },
            'programs': json.dumps(self._get_programs(request), sort_keys=True),
            'render_language': self.request.LANGUAGE_CODE,
            'records_help_url': records_help_url,
        })
        return context

    def dispatch(self, request, *args, **kwargs):
        if not waffle.flag_is_active(request, WAFFLE_FLAG_RECORDS):
            raise http.Http404()
        return super().dispatch(request, *args, **kwargs)


class ProgramRecordView(LoginRequiredMixin, TemplateView, ThemeViewMixin):
    template_name = 'programs.html'

    def _get_record(self, program_uuid):
        user = self.request.user
        platform_name = self.request.site.siteconfiguration.platform_name

        program = Program.objects.prefetch_related('course_runs').get(uuid=program_uuid)
        program_course_runs = program.course_runs.all()

        # Get all courses and their keys associated with a program
        program_course_run_keys = set([course_run.key for course_run in program_course_runs])

        # Get all of the user course-certificates associated with the program courses
        course_certificate_content_type = ContentType.objects.get(app_label='credentials', model='coursecertificate')
        course_user_credentials = set(UserCredential.objects.filter(username=user.username,
                                      credential_content_type=course_certificate_content_type,
                                      status=UserCredential.AWARDED))
        course_certificates = CourseCertificate.objects.filter(course_id__in=program_course_run_keys,
                                                               user_credentials__in=course_user_credentials)
        # Maps course run 'key' to the cert
        course_certificate_dict = {
            course_certificate.course_id: course_certificate for course_certificate in course_certificates}

        # Get all (verified) user grades relevant to this program
        course_grades = UserGrade.objects.select_related('course_run__course').filter(
            username=user.username, course_run__in=program_course_runs, verified=True)

        # Keep track of number of attempts and best attempt per course
        num_attempts_dict = defaultdict(int)
        highest_attempt_dict = {}

        # Find the highest course cert grades for each course
        for course_grade in course_grades:
            course_run = course_grade.course_run
            course = course_grade.course_run.course

            if course_run.key in course_certificate_dict:
                num_attempts_dict[course] += 1
                percent_grade = float(course_grade.percent_grade)  # Use the percent instead of letters

                if (course not in highest_attempt_dict or
                        (course in highest_attempt_dict and
                            percent_grade > highest_attempt_dict[course].percent_grade)):
                    highest_attempt_dict[course] = course_grade

        learner_data = {'full_name': user.get_full_name(),
                        'username': user.username,
                        'email': user.email}

        program_data = {'name': program.title,
                        'school': ','.join(program.authoring_organizations.values_list('name', flat=True))}

        course_data = [{'name': course.title,
                        'school': ','.join(course.owners.values_list('name', flat=True)),
                        'attempts': num_attempts_dict[course],
                        'course_id': course.key,
                        'issue_date': course_certificate_dict[grade.course_run.key].modified.isoformat(),
                        'percent_grade': float(grade.percent_grade),
                        'letter_grade': grade.letter_grade,
                        } for course, grade in highest_attempt_dict.items()]

        return {'learner': learner_data,
                'program': program_data,
                'platform_name': platform_name,
                'grades': course_data}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        program_uuid = kwargs['uuid']
        record = self._get_record(program_uuid)
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


class ProgramRecordCreationView(View):
    """
    Creates a new Program Certificate Record from given username and program certificate uuid,
    returns the uuid of the created Program Certificate Record
    """

    def post(self, request):
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User does not exist'}, status=404)

        # verify that the user or an admin is making the request
        if username != request.user.get_username() and not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        cert_uuid = request.POST.get('program_cert_uuid')
        certificate = get_object_or_404(ProgramCertificate, program_uuid=cert_uuid)

        # verify that the User has the User Credentials for the Program Certificate
        try:
            UserCredential.objects.get(username=username, program_credentials__program_uuid=cert_uuid)
        except UserCredential.DoesNotExist:
            return JsonResponse({'error': 'User does not have credentials'}, status=404)

        pcr, created = ProgramCertRecord.objects.get_or_create(user=user, certificate=certificate)
        status_code = 201 if created else 200

        return JsonResponse({'uuid': pcr.uuid.hex}, status=status_code)

    def dispatch(self, request, *args, **kwargs):
        if not waffle.flag_is_active(request, WAFFLE_FLAG_RECORDS):
            return JsonResponse({'error': 'Waffle flag not enabled'}, status=404)
        return super().dispatch(request, *args, **kwargs)
