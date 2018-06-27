import logging
from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.management import BaseCommand
from django.db import transaction
from faker import Faker

from credentials.apps.catalog.models import Course, CourseRun, Organization, Program
from credentials.apps.core.models import User
from credentials.apps.credentials.models import CourseCertificate, ProgramCertificate, Signatory, UserCredential
from credentials.apps.records.models import ProgramCertRecord, UserGrade

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """ Seed all the data needed to display fake student records """
    help = 'Seed catalog with fake data'

    def add_arguments(self, parser):
        """ Add arguments to the command parser """
        parser.add_argument(
            '--site-name',
            action='store',
            default='Open edx',
            required=False,
            help="The site to attach all records to"
        )

        parser.add_argument(
            '--user-name',
            action='store',
            type=str,
            default='edx',
            required=False,
            help="The user to attach all certs to"
        )

    def handle(self, *args, **options):
        site_name = options.get('site_name')
        username = options.get('user_name')

        Command.seed_all(site_name, username)

    @staticmethod
    def log_action(object_type, object_id, created):
        """ Log a get_or_create action using a simple template """
        action = "Created" if created else "Already exists"
        logger.info("%s %s %s", object_type, object_id, action)

    @staticmethod
    @transaction.atomic
    def seed_all(site_name, username):
        """ Seed all catalog data """
        # Make predictable UUIDs using faker
        faker = Faker()
        faker.seed(1234)

        site = Command.get_site(site_name)
        organizations = Command.seed_organizations(site, faker)
        courses = Command.seed_courses(site, organizations, faker)
        course_runs = Command.seed_course_runs(courses, faker)
        programs = Command.seed_programs(site, organizations, course_runs, faker)
        user = Command.get_user(username)
        Command.seed_user_grades(user, course_runs)
        Command.seed_signatories(organizations)
        course_certificates = Command.seed_course_certificates(site, course_runs)
        program_certificates = Command.seed_program_certificates(site, programs)
        Command.seed_user_credentials(user, program_certificates, course_certificates, faker)
        Command.seed_program_cert_records(user, program_certificates, faker)

    @staticmethod
    def get_site(site_name):
        """ Get a specific site by its name """
        return Site.objects.get(name=site_name)

    @staticmethod
    def seed_organizations(site, faker):
        """ Seed two organizations """
        organization1, created = Organization.objects.get_or_create(
            site=site, uuid=faker.uuid4(), name='Test-Org-1')
        Command.log_action('Organization', 'Test-Org-1', created)

        organization2, created = Organization.objects.get_or_create(
            site=site, uuid=faker.uuid4(), name='Test-Org-2')
        Command.log_action('Organization', 'Test-Org-2', created)

        return [organization1, organization2]

    @staticmethod
    def seed_courses(site, organizations, faker):
        """ Seed two courses per organization """
        courses = []
        course_id = 1

        for organization in organizations:

            course1, created = Course.objects.get_or_create(
                site=site,
                uuid=faker.uuid4(),
                title="Course {}".format(course_id),
                key="Course-{}".format(course_id))
            course1.owners = [organization]
            courses.append(course1)
            Command.log_action("Course", course_id, created)

            course2, created = Course.objects.get_or_create(
                site=site,
                uuid=faker.uuid4(),
                title="Course {}".format(course_id + 1),
                key="Course-{}".format(course_id + 1))
            course2.owners = [organization]
            courses.append(course2)
            Command.log_action("Course", course_id + 1, created)

            course_id += 2

        return courses

    @staticmethod
    def seed_course_runs(courses, faker):
        """ Seed one course run per course """
        course_runs = []
        course_run_id = 1

        for course in courses:
            organization = course.owners.all()[0]
            key = "course-v1:{}+{}+{}".format(organization.name, course.key, course_run_id)
            course_run, created = CourseRun.objects.get_or_create(
                course=course,
                uuid=faker.uuid4(),
                start=datetime(2018, 1, 1),
                end=datetime(2018, 6, 1),
                key=key)

            Command.log_action("CourseRun for", course.title, created)

            course_runs.append(course_run)
            course_run_id += 1

        return course_runs

    @staticmethod
    def seed_programs(site, organizations, course_runs, faker):
        """ Seed one program per org of all course runs for that org """
        programs = []
        program_id = 1

        for organization in organizations:
            courses = Course.objects.filter(owners=organization)
            course_runs = [CourseRun.objects.get(course=course) for course in courses]

            program, created = Program.objects.get_or_create(
                site=site,
                uuid=faker.uuid4(),
                title='Program {}'.format(program_id))
            program.course_runs = course_runs
            program.authoring_organizations = [organization]
            Command.log_action("Program", program_id, created)

            programs.append(program)
            program_id += 1

        return programs

    @staticmethod
    def get_user(username):
        """ Get the test user """
        return User.objects.get(username=username)

    @staticmethod
    def seed_user_grades(user, course_runs):
        """ Seed user grades for the test users """
        user_grades = []

        for course_run in course_runs:
            user_grade, created = UserGrade.objects.get_or_create(
                username=str(user),
                course_run=course_run,
                letter_grade='B',
                percent_grade=0.82,
                verified=True)

            Command.log_action("User Grade for", course_run.course.title, created)
            user_grades.append(user_grade)

        return user_grades

    @staticmethod
    def seed_signatories(organizations):
        """ Seed one signatory per org """

        signatories = []

        for organization in organizations:
            signatory, created = Signatory.objects.get_or_create(
                name=organization.name,
                title=organization.name)  # TODO: add image

            Command.log_action("Signatory for", organization.name, created)
            signatories.append(signatory)

        return signatories

    @staticmethod
    def seed_program_certificates(site, programs):
        """ Seed program certs for two programs """
        program_certificates = []

        for program in programs:
            program_certificate, created = ProgramCertificate.objects.get_or_create(
                site=site,
                program_uuid=program.uuid,
                language='en')

            Command.log_action("Program certificate for", program.title, created)
            program_certificates.append(program_certificate)

        return program_certificates

    @staticmethod
    def seed_course_certificates(site, course_runs):
        """ Seed course certificates for all courses for user edx"""
        course_certificates = []

        for course_run in course_runs:
            course_certificate, created = CourseCertificate.objects.get_or_create(
                site=site, course_id=course_run.key)
            Command.log_action("Course certificate for course run", course_run, created)
            course_certificates.append(course_certificate)

        return course_certificates

    @staticmethod
    def seed_user_credentials(user, program_certificates, course_certificates, faker):
        """ Seed user credentials for user """
        user_program_credentials = []
        user_course_credentials = []

        for program_certificate in program_certificates:
            user_credential, created = UserCredential.objects.get_or_create(
                credential_content_type=ContentType.objects.get_for_model(program_certificate),
                credential_id=program_certificate.id,
                username=str(user),
                status=UserCredential.AWARDED,
                download_url="http://localhost:18150/download",
                uuid=faker.uuid4())

            Command.log_action("User Credential for", program_certificate, created)
            user_program_credentials.append(user_credential)

        for course_certificate in course_certificates:
            user_credential, created = UserCredential.objects.get_or_create(
                credential_content_type=ContentType.objects.get_for_model(course_certificate),
                credential_id=course_certificate.id,
                username=str(user),
                status=UserCredential.AWARDED,
                download_url="http://localhost:18150/download",
                uuid=faker.uuid4())

            Command.log_action("User Credential for Course", course_certificate.course_id, created)
            user_course_credentials.append(user_credential)

        return user_program_credentials, user_course_credentials

    @staticmethod
    def seed_program_cert_records(user, program_certificates, faker):
        """ Seed  program cert records for user"""
        program_cert_records = []

        for program_certificate in program_certificates:
            program_cert_record, created = ProgramCertRecord.objects.get_or_create(
                certificate=program_certificate,
                user=user,
                uuid=faker.uuid4())

            Command.log_action("Program Certificate with ID", program_certificate.id, created)
            program_cert_records.append(program_cert_record)

        return program_cert_records
