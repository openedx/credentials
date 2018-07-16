import json
from collections import defaultdict

import waffle
from django import http
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, View

from credentials.apps.catalog.models import CourseRun, CreditPathway, Program
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
        course_certificates = CourseCertificate.objects.filter(id__in=course_credential_ids, site=request.site)
        course_run_keys = map(lambda course_certificate: course_certificate.course_id, course_certificates)
        course_runs = CourseRun.objects.filter(key__in=course_run_keys)
        programs = Program.objects.filter(course_runs__in=course_runs, site=request.site).distinct().prefetch_related(
            'authoring_organizations'
        ).order_by('title')

        # Get the completed programs and a UUID set using the program_credentials
        program_credential_ids = map(lambda program_credential: program_credential.credential_id, program_credentials)
        program_certificates = ProgramCertificate.objects.filter(id__in=program_credential_ids)
        completed_program_uuids = set(program_certificate.program_uuid for program_certificate in program_certificates)

        return [
            {
                'name': program.title,
                'partner': ', '.join(program.authoring_organizations.values_list('name', flat=True)),
                'uuid': program.uuid.hex,
                'type': slugify(program.type),
                'progress': _('Completed') if program.uuid in completed_program_uuids else _('In Progress')
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


class ConditionallyRequireLoginMixin(AccessMixin):
    """ Variant of LoginRequiredMixin that allows a user not to be logged in if is_public argument is true"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and not kwargs['is_public']:
            return self.handle_no_permission()
        return super(ConditionallyRequireLoginMixin, self).dispatch(request, *args, **kwargs)


class ProgramRecordView(ConditionallyRequireLoginMixin, TemplateView, ThemeViewMixin):
    template_name = 'programs.html'

    def _get_record(self, uuid, is_public):
        # if a public view, the uuid is that of a ProgramCertRecord,
        # if private, the uuid is that of a Program
        if is_public:
            program_cert_record = get_object_or_404(ProgramCertRecord, uuid=uuid)
            user = program_cert_record.user
            program_uuid = program_cert_record.certificate.program_uuid
        else:
            user = self.request.user
            program_uuid = uuid

        platform_name = self.request.site.siteconfiguration.platform_name

        program = Program.objects.prefetch_related('course_runs__course').get(uuid=program_uuid, site=self.request.site)
        program_course_runs = program.course_runs.all()
        program_course_runs_set = set(program_course_runs)

        # Get all of the user course-certificates associated with the program courses
        course_certificate_content_type = ContentType.objects.get(app_label='credentials', model='coursecertificate')
        course_user_credentials = UserCredential.objects.prefetch_related('credential').filter(
            username=user.username,
            credential_content_type=course_certificate_content_type,)

        # Maps course run key to the associated credential
        user_credential_dict = {
            user_credential.credential.course_id: user_credential for user_credential in course_user_credentials}

        # Get all (verified) user grades relevant to this program
        course_grades = UserGrade.objects.select_related('course_run__course').filter(
            username=user.username, course_run__in=program_course_runs_set, verified=True)

        # Keep track of number of attempts and best attempt per course
        num_attempts_dict = defaultdict(int)
        highest_attempt_dict = {}  # Maps course -> highest grade earned

        # Find the highest course cert grades for each course
        for course_grade in course_grades:
            course_run = course_grade.course_run
            course = course_run.course
            user_credential = user_credential_dict.get(course_run.key)

            if user_credential is not None:
                num_attempts_dict[course] += 1

                # Update grade if grade is higher and part of awarded cert
                if user_credential.status == UserCredential.AWARDED:
                    current = highest_attempt_dict.setdefault(course, course_grade)
                    if course_grade.percent_grade > current.percent_grade:
                        highest_attempt_dict[course] = course_grade

        learner_data = {'full_name': user.get_full_name(),
                        'username': user.username,
                        'email': user.email, }

        program_data = {'name': program.title,
                        'type': slugify(program.type),
                        'school': ', '.join(program.authoring_organizations.values_list('name', flat=True))}

        # Add course-run data to the response in the order that is maintained by the Program's sorted field
        course_data = []
        for course_run in program_course_runs:
            course = course_run.course
            grade = highest_attempt_dict.get(course)
            if grade is not None and grade.course_run == course_run:
                course_data.append({
                    'name': course_run.title,
                    'school': ', '.join(course.owners.values_list('name', flat=True)),
                    'attempts': num_attempts_dict[course],
                    'course_id': course_run.key,
                    'issue_date': user_credential_dict[course_run.key].modified.isoformat(),
                    'percent_grade': float(grade.percent_grade),
                    'letter_grade': grade.letter_grade, })

        # Get credit pathways for the given program.
        pathways = CreditPathway.objects.filter(programs__uuid=program.uuid)
        pathways_data = []
        for pathway in pathways:
            pathways_data.append({
                'name': pathway.name,
                'org_name': pathway.org_name,
                'email': pathway.email,
            })

        return {'learner': learner_data,
                'program': program_data,
                'platform_name': platform_name,
                'grades': course_data,
                'pathways': pathways_data}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        uuid = kwargs['uuid']
        is_public = kwargs['is_public']
        record = self._get_record(uuid, is_public)

        context.update({
            'child_templates': {
                'footer': self.select_theme_template(['_footer.html']),
                'header': self.select_theme_template(['_header.html']),
            },
            'record': json.dumps(record, sort_keys=True),
            'program_name': record.get('program', {}).get('name'),
            'render_language': self.request.LANGUAGE_CODE,
            'is_public': is_public,
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
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)

        username = body['username']
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User does not exist'}, status=404)

        # verify that the user or an admin is making the request
        if username != request.user.get_username() and not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        cert_uuid = body['uuid']
        certificate = get_object_or_404(ProgramCertificate, program_uuid=cert_uuid)

        # verify that the User has the User Credentials for the Program Certificate
        try:
            UserCredential.objects.get(username=username, program_credentials__program_uuid=cert_uuid)
        except UserCredential.DoesNotExist:
            return JsonResponse({'error': 'User does not have credentials'}, status=404)

        pcr, created = ProgramCertRecord.objects.get_or_create(user=user, certificate=certificate)
        status_code = 201 if created else 200

        url = request.build_absolute_uri(reverse("records:public_programs", kwargs={'uuid': pcr.uuid.hex}))
        return JsonResponse({'url': url}, status=status_code)

    def dispatch(self, request, *args, **kwargs):
        if not waffle.flag_is_active(request, WAFFLE_FLAG_RECORDS):
            return JsonResponse({'error': 'Waffle flag not enabled'}, status=404)
        return super().dispatch(request, *args, **kwargs)
