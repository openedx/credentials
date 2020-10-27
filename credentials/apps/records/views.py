import csv
import datetime
import io
import json
import logging
import urllib.parse
from collections import defaultdict

from analytics.client import Client as SegmentClient
from django import http
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView, View
from edx_ace import Recipient, ace
from ratelimit.decorators import ratelimit

from credentials.apps.catalog.models import CourseRun, Pathway, Program
from credentials.apps.core.models import User
from credentials.apps.core.views import ThemeViewMixin
from credentials.apps.credentials.models import CourseCertificate, ProgramCertificate, UserCredential
from credentials.apps.credentials.utils import filter_visible, get_credential_visible_dates
from credentials.apps.records.constants import UserCreditPathwayStatus
from credentials.apps.records.messages import ProgramCreditRequest
from credentials.apps.records.models import ProgramCertRecord, UserCreditPathway, UserGrade
from credentials.shared.constants import PathwayType

from .constants import RECORDS_RATE_LIMIT


log = logging.getLogger(__name__)


def rate_limited(request, exception):
    log.warning("Credentials records endpoint is being throttled.")
    return JsonResponse({'error': 'Too Many Requests'}, status=429)


class RecordsEnabledMixin:
    """ Only allows view if records are enabled for the installation & site.
        Note that the API views are will still be active even if records is disabled.
        You may want to disable records support in the LMS if you want to stop data being sent over.
        If the user is not logged in, we direct them to a login page first. """
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not request.site.siteconfiguration.records_enabled:
                raise http.Http404()
        return super().dispatch(request, *args, **kwargs)


class ConditionallyRequireLoginMixin(AccessMixin):
    """ Variant of LoginRequiredMixin that allows a user not to be logged in if is_public argument is true"""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and not kwargs['is_public']:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


def get_record_data(user, program_uuid, site, platform_name=None):
    program = Program.objects.prefetch_related('course_runs__course').get(uuid=program_uuid, site=site)
    program_course_runs = program.course_runs.all()
    program_course_runs_set = frozenset(program_course_runs)

    # Get all pathway organizations and their statuses
    program_pathways = program.pathways.all()
    program_pathways_set = frozenset(program_pathways)
    user_credit_pathways = UserCreditPathway.objects.select_related('pathway').filter(
        user=user, pathway__in=program_pathways_set).all()
    user_credit_pathways_dict = {user_pathway.pathway:
                                 user_pathway.status for user_pathway in user_credit_pathways}
    pathways = [(pathway, user_credit_pathways_dict.setdefault(pathway, ''))
                for pathway in program_pathways]

    # Find program credential if it exists (indicates if user has completed this program)
    program_credential_query = filter_visible(UserCredential.objects.filter(
        username=user.username,
        status=UserCredential.AWARDED,
        program_credentials__program_uuid=program_uuid))

    # Get all of the user course-certificates associated with the program courses (including not AWARDED ones)
    course_certificate_content_type = ContentType.objects.get(app_label='credentials', model='coursecertificate')
    course_user_credentials = filter_visible(UserCredential.objects.prefetch_related('credential').filter(
        username=user.username,
        credential_content_type=course_certificate_content_type,))

    # Maps course run key to the associated credential
    user_credential_dict = {
        user_credential.credential.course_id: user_credential for user_credential in course_user_credentials}

    # Maps credentials to visible_date datetimes (a date when the cert becomes valid)
    visible_dates = get_credential_visible_dates(course_user_credentials)

    # Get all (verified) user grades relevant to this program
    course_grades = UserGrade.objects.select_related('course_run__course').filter(
        username=user.username, course_run__in=program_course_runs_set, verified=True)

    # Keep track of number of attempts and best attempt per course
    num_attempts_dict = defaultdict(int)
    highest_attempt_dict = {}  # Maps course -> highest grade earned
    last_updated = None

    # Find the highest course cert grades for each course
    for course_grade in course_grades:
        course_run = course_grade.course_run
        course = course_run.course
        user_credential = user_credential_dict.get(course_run.key)

        if user_credential is not None:
            num_attempts_dict[course] += 1
            visible_date = visible_dates[user_credential]
            last_updated = max(filter(None, [visible_date, course_grade.modified, last_updated]))

            # Update grade if grade is higher and part of awarded cert
            if user_credential.status == UserCredential.AWARDED:
                current = highest_attempt_dict.setdefault(course, course_grade)
                if course_grade.percent_grade > current.percent_grade:
                    highest_attempt_dict[course] = course_grade

    last_updated = last_updated or datetime.datetime.today()

    learner_data = {'full_name': user.get_full_name(),
                    'username': user.username,
                    'email': user.email, }

    program_data = {'name': program.title,
                    'type': slugify(program.type),
                    'type_name': program.type,
                    'completed': program_credential_query.exists(),
                    'empty': not highest_attempt_dict,
                    'last_updated': last_updated.isoformat(),
                    'school': ', '.join(program.authoring_organizations.values_list('name', flat=True))}

    pathway_data = [{'name': pathway[0].name,
                     'id': pathway[0].id,
                     'status': pathway[1],
                     'is_active': bool(pathway[0].email),
                     'pathway_type': pathway[0].pathway_type, }
                    for pathway in pathways]

    # Add course-run data to the response in the order that is maintained by the Program's sorted field
    course_data = []
    added_courses = set()
    for course_run in program_course_runs:
        course = course_run.course
        grade = highest_attempt_dict.get(course)

        # If user hasn't taken this course yet, or doesn't have a cert, we want to show empty values
        if grade is None and course not in added_courses:
            course_data.append({
                'name': course.title,
                'school': ', '.join(course.owners.values_list('name', flat=True)),
                'attempts': 0,
                'course_id': '',
                'issue_date': '',
                'percent_grade': 0.0,
                'letter_grade': '', })
            added_courses.add(course)

        # If the user has taken the course, show the course_run info for the highest grade
        elif grade is not None and grade.course_run == course_run:
            issue_date = visible_dates[user_credential_dict[course_run.key]]
            course_data.append({
                'name': course_run.title,
                'school': ', '.join(course.owners.values_list('name', flat=True)),
                'attempts': num_attempts_dict[course],
                'course_id': course_run.key,
                'issue_date': issue_date.isoformat(),
                'percent_grade': float(grade.percent_grade),
                'letter_grade': grade.letter_grade or _('N/A'), })
            added_courses.add(course)

    return {'learner': learner_data,
            'program': program_data,
            'platform_name': platform_name,
            'grades': course_data,
            'pathways': pathway_data, }


class RecordsListBaseView(LoginRequiredMixin, RecordsEnabledMixin, TemplateView, ThemeViewMixin):
    template_name = 'records.html'

    def _get_credentials(self):
        """ Returns two lists of credentials: a course list and a program list """
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
        user_credentials = filter_visible(UserCredential.objects.filter(
            username=self.request.user.username,
            status=UserCredential.AWARDED,
            credential_content_type__in=course_cert_content_types
        ))
        course_credentials = []
        program_credentials = []
        for credential in user_credentials:
            if credential.credential_content_type_id == course_certificate_type.id:
                course_credentials.append(credential)
            elif credential.credential_content_type_id == program_certificate_type.id:
                program_credentials.append(credential)

        return course_credentials, program_credentials

    def _course_credentials_to_course_runs(self, course_credentials):
        """ Convert a list of course UserCredentials into a list of CourseRun objects """
        # Using the course credentials, get the programs associated with them via course runs
        course_credential_ids = [x.credential_id for x in course_credentials if x.status == UserCredential.AWARDED]
        course_certificates = CourseCertificate.objects.filter(id__in=course_credential_ids, site=self.request.site)
        course_run_keys = map(lambda course_certificate: course_certificate.course_id, course_certificates)
        return CourseRun.objects.filter(key__in=course_run_keys)

    def _programs_context(self, include_empty_programs=False, include_retired_programs=False):
        """ Translates a list of Program and UserCredentials (for programs) into context data. """
        # Get all user credentials
        course_credentials, program_credentials = self._get_credentials()

        # Get course runs that this user has a credential in
        course_runs = frozenset(self._course_credentials_to_course_runs(course_credentials))
        course_filters = {} if include_empty_programs else {'course_runs__in': course_runs}

        allowed_statuses = [Program.ACTIVE]
        if include_retired_programs:
            allowed_statuses.append(Program.RETIRED)

        # Get a list of programs
        programs = Program.objects.filter(
            site=self.request.site, status__in=allowed_statuses, **course_filters
        ).distinct().prefetch_related(
            'authoring_organizations', 'course_runs',
        ).order_by('title')

        # Get the completed programs and a UUID set using the program_credentials
        program_credential_ids = map(lambda program_credential: program_credential.credential_id, program_credentials)
        program_certificates = ProgramCertificate.objects.filter(id__in=program_credential_ids, site=self.request.site)
        completed_program_uuids = frozenset(
            program_certificate.program_uuid for program_certificate in program_certificates)

        return [
            {
                'name': program.title,
                'partner': ', '.join(program.authoring_organizations.values_list('name', flat=True)),
                'uuid': program.uuid.hex,
                'type': slugify(program.type),
                'completed': program.uuid in completed_program_uuids,
                'empty': not bool(course_runs.intersection(frozenset(program.course_runs.all()))),
            } for program in programs]

    def _get_programs(self):
        """ Returns a list of relevant program data (in _programs_context format) """
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'child_templates': {
                'footer': self.select_theme_template(['_footer.html']),
                'header': self.select_theme_template(['_header.html']),
            },
            'programs': json.dumps(self._get_programs(), sort_keys=True),
            'render_language': self.request.LANGUAGE_CODE,
            'request': self.request,
            'icons_template': self.try_select_theme_template(['credentials/records.html']),
        })

        return context


class RecordsView(RecordsListBaseView):
    def _get_programs(self):
        return self._programs_context(include_empty_programs=False, include_retired_programs=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        site_configuration = self.request.site.siteconfiguration
        if site_configuration:
            context['profile_url'] = urllib.parse.urljoin(site_configuration.lms_url_root,
                                                          'u/' + self.request.user.username)
            context['records_help_url'] = site_configuration.records_help_url

        context['child_templates']['masquerade'] = self.select_theme_template(['_masquerade.html'])

        # Translators: A 'record' here means something like a transcript -- a list of courses and grades.
        context['title'] = _('My Learner Records')
        context['program_help'] = _('A program record is created once you have earned at least one '
                                    'course certificate in a program.')

        return context


class ProgramListingView(RecordsListBaseView):
    def _get_programs(self):
        return self._programs_context(include_empty_programs=True, include_retired_programs=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('Program Listing View')
        context['program_help'] = _('The following is a list of all active programs for which program records '
                                    'are being generated.')

        return context

    def dispatch(self, request, *args, **kwargs):
        # Kick out non staff and non superuser users (skipping anonymous users,
        # because they are redirected to a login screen instead)
        if not request.user.is_anonymous and not request.user.is_staff and not request.user.is_superuser:
            raise http.Http404()
        return super().dispatch(request, *args, **kwargs)


class ProgramRecordView(ConditionallyRequireLoginMixin, RecordsEnabledMixin, TemplateView, ThemeViewMixin):
    template_name = 'programs.html'

    def _get_record(self, uuid, is_public):
        # if a public view, the uuid is that of a ProgramCertRecord,
        # if private, the uuid is that of a Program
        if is_public:
            program_cert_record = get_object_or_404(ProgramCertRecord, uuid=uuid)
            user = program_cert_record.user
            program_uuid = program_cert_record.program.uuid
        else:
            user = self.request.user
            program_uuid = uuid

        data = get_record_data(
            user,
            program_uuid,
            self.request.site,
            platform_name=self.request.site.siteconfiguration.platform_name
        )

        # Only allow superusers to view a record with no data in it (i.e. don't allow learners to guess URLs and view)
        if not self.request.user.is_superuser and data['program']['empty']:
            raise http.Http404()

        return data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        uuid = kwargs['uuid']
        is_public = kwargs['is_public']
        record = self._get_record(uuid, is_public)

        site_configuration = self.request.site.siteconfiguration
        records_help_url = site_configuration.records_help_url if site_configuration else ''

        context.update({
            'child_templates': {
                'footer': self.select_theme_template(['_footer.html']),
                'header': self.select_theme_template(['_header.html']),
                'masquerade': self.select_theme_template(['_masquerade.html']),
            },
            'record': json.dumps(record, sort_keys=True),
            'program_name': record.get('program', {}).get('name'),
            'render_language': self.request.LANGUAGE_CODE,
            'is_public': is_public,
            'icons_template': self.try_select_theme_template(['credentials/programs.html']),
            'uuid': uuid,
            'records_help_url': records_help_url,
            'request': self.request,
        })
        return context


@method_decorator(
    ratelimit(
        key='user', rate=RECORDS_RATE_LIMIT,
        method='POST', block=True
    ), name='dispatch'
)
class ProgramSendView(LoginRequiredMixin, RecordsEnabledMixin, View):
    """
    Sends a program via email to a requested partner
    """
    def post(self, request, **kwargs):
        body_unicode = request.body.decode('utf-8')
        body = json.loads(body_unicode)

        username = body['username']
        pathway_id = body['pathway_id']
        program_uuid = kwargs['uuid']

        # verify that the user or an admin is making the request
        if username != request.user.get_username() and not request.user.is_staff:
            return JsonResponse({'error': 'Permission denied'}, status=403)

        credential = UserCredential.objects.filter(username=username, status=UserCredential.AWARDED,
                                                   program_credentials__program_uuid=program_uuid)
        program = get_object_or_404(Program, uuid=program_uuid, site=request.site)
        pathway = get_object_or_404(
            Pathway,
            id=pathway_id,
            programs__uuid=program_uuid,
            pathway_type=PathwayType.CREDIT.value,
        )
        certificate = get_object_or_404(ProgramCertificate, program_uuid=program_uuid, site=request.site)
        user = get_object_or_404(User, username=username)
        public_record, _ = ProgramCertRecord.objects.get_or_create(user=user, program=program)

        # Make sure we haven't already sent an email with a 'sent' status
        if UserCreditPathway.objects.filter(
                user=user, pathway=pathway, status=UserCreditPathwayStatus.SENT).exists():
            return JsonResponse({'error': 'Pathway email already sent'}, status=400)

        record_path = reverse('records:public_programs', kwargs={'uuid': public_record.uuid.hex})
        record_link = request.build_absolute_uri(record_path)
        csv_link = urllib.parse.urljoin(record_link, "csv")

        msg = ProgramCreditRequest(request.site, user.email).personalize(
            recipient=Recipient(username=None, email_address=pathway.email),
            language=certificate.language,
            user_context={
                'pathway_name': pathway.name,
                'program_name': program.title,
                'record_link': record_link,
                'user_full_name': request.user.get_full_name() or request.user.username,
                'program_completed': credential.exists(),
                'previously_sent': False,
                'csv_link': csv_link,
            },
        )
        ace.send(msg)

        # Create a record of this email so that we can't send multiple times
        # If the status was previously changed, we want to reset it to SENT
        UserCreditPathway.objects.update_or_create(
            user=user,
            pathway=pathway,
            defaults={'status': UserCreditPathwayStatus.SENT}, )

        return http.HttpResponse(status=200)


@method_decorator(
    ratelimit(
        key='user', rate=RECORDS_RATE_LIMIT,
        method='POST', block=True
    ), name='dispatch'
)
class ProgramRecordCreationView(LoginRequiredMixin, RecordsEnabledMixin, View):
    """
    Creates a new Program Certificate Record from given username and program uuid,
    returns the uuid of the created Program Certificate Record
    """
    def post(self, request, **kwargs):
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

        program_uuid = kwargs['uuid']
        program = get_object_or_404(Program, uuid=program_uuid, site=request.site)
        pcr, created = ProgramCertRecord.objects.get_or_create(user=user, program=program)
        status_code = 201 if created else 200

        url = request.build_absolute_uri(reverse("records:public_programs", kwargs={'uuid': pcr.uuid.hex}))
        return JsonResponse({'url': url}, status=status_code)


class ProgramRecordCsvView(RecordsEnabledMixin, View):
    """
    Returns a csv view of the Program Record for a Learner from a username and program_uuid.

    Note:  We are currently not rate limiting this endpoint due to the issues
    surrounding rate limiting unauthenticated users.  If this endpoint starts
    causing trouble down the line, may be worth adding annotated rate limits
    that force users to solve a captcha.
    """

    class SegmentHttpResponse(HttpResponse):
        def __init__(self, *args, **kwargs):
            # Pop off the unneeded args that are sent to segment
            self.event = kwargs.pop('event')
            self.properties = kwargs.pop('properties')
            self.context = kwargs.pop('context')
            self.anonymous_id = kwargs.pop('anonymous_id')
            self.segment_client = kwargs.pop('segment_client')
            super(ProgramRecordCsvView.SegmentHttpResponse, self).__init__(*args, **kwargs)

        def close(self):
            self.segment_client.track(
                self.anonymous_id,
                event=self.event,
                properties=self.properties,
                context=self.context
            )
            super(ProgramRecordCsvView.SegmentHttpResponse, self).close()

    def get(self, request, *args, **kwargs):
        site_configuration = request.site.siteconfiguration
        segment_client = SegmentClient(write_key=site_configuration.segment_key)

        program_cert_record = get_object_or_404(ProgramCertRecord, uuid=kwargs.get('uuid'))
        record = get_record_data(program_cert_record.user, program_cert_record.program.uuid, request.site,
                                 platform_name=site_configuration.platform_name)

        user_metadata = [
            ['Program Name', record['program']['name']],
            ['Program Type', record['program']['type_name']],
            ['Platform Provider', record['platform_name']],
            ['Authoring Organization(s)', record['program']['school']],
            ['Learner Name', record['learner']['full_name']],
            ['Username', record['learner']['username']],
            ['Email', record['learner']['email']],
            [''],
        ]

        properties = {
            'category': 'records',
            'program_uuid': program_cert_record.program.uuid.hex,
            'record_uuid': program_cert_record.uuid.hex,
        }
        context = {
            'page': {
                'path': request.path,
                'referrer': request.META.get('HTTP_REFERER'),
                'url': request.build_absolute_uri(),
            },
            'userAgent': request.META.get('HTTP_USER_AGENT'),
        }

        segment_client.track(
            request.COOKIES.get('ajs_anonymous_id'),
            context=context,
            event='edx.bi.credentials.program_record.download_started',
            properties=properties,
        )

        string_io = io.StringIO()
        writer = csv.writer(string_io, quoting=csv.QUOTE_ALL)
        writer.writerows(user_metadata)
        writer = csv.DictWriter(string_io, record['grades'][0].keys(), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(record['grades'])
        string_io.seek(0)
        filename = '{username}_{program_name}_grades'.format(
            username=record['learner']['username'],
            program_name=record['program']['name']
        )
        response = ProgramRecordCsvView.SegmentHttpResponse(
            string_io,
            anonymous_id=request.COOKIES.get('ajs_anonymous_id'),
            content_type='text/csv',
            context=context,
            event='edx.bi.credentials.program_record.download_finished',
            properties=properties,
            segment_client=segment_client,
        )
        filename = filename.replace(' ', '_').lower().encode('utf-8')
        response['Content-Disposition'] = 'attachment; filename="{filename}.csv"'.format(
            filename=filename
        )
        return response
