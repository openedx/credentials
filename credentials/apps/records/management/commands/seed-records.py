import logging
from datetime import datetime

from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.management import BaseCommand
from django.db import transaction
from faker import Faker

from credentials.apps.catalog.models import Course, CourseRun, Organization, Pathway, Program
from credentials.apps.core.api import get_user_by_username
from credentials.apps.credentials.constants import CertificateType
from credentials.apps.credentials.models import CourseCertificate, ProgramCertificate, Signatory, UserCredential
from credentials.apps.records.constants import UserCreditPathwayStatus
from credentials.apps.records.models import ProgramCertRecord, UserCreditPathway, UserGrade
from credentials.settings.base import TIME_ZONE_CLASS
from credentials.shared.constants import PathwayType

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Seed all the data needed to display fake student records"""

    help = "Seed catalog with fake data"

    def add_arguments(self, parser):
        """Add arguments to the command parser"""
        parser.add_argument(
            "--site-name", action="store", default="Open edx", required=False, help="The site to attach all records to"
        )

        parser.add_argument(
            "--user-name",
            action="store",
            type=str,
            default="edx",
            required=False,
            help="The user to attach all certs to",
        )

    def handle(self, *args, **options):
        site_name = options.get("site_name")
        username = options.get("user_name")

        Command.seed_all(site_name, username)

    @staticmethod
    def log_action(object_type, object_id, created):
        """Log a get_or_create action using a simple template"""
        action = "Created" if created else "Already exists"
        logger.info("%s %s %s", object_type, object_id, action)

    @staticmethod
    @transaction.atomic
    def seed_all(site_name, username):
        """Seed all catalog data"""
        # Make predictable UUIDs using faker
        faker = Faker()
        Faker.seed(1234)

        site = Command.get_site(site_name)
        organizations = Command.seed_organizations(site, faker)
        courses = Command.seed_courses(site, organizations, faker)
        course_runs = Command.seed_course_runs(courses, faker)
        programs = Command.seed_programs(site, organizations, course_runs, faker)
        user = Command.get_user(username)
        Command.seed_user_grades(user, course_runs)
        signatories = Command.seed_signatories(organizations)
        course_certificates = Command.seed_course_certificates(site, course_runs, signatories)
        program_certificates = Command.seed_program_certificates(site, programs, signatories)
        Command.seed_user_credentials(user, program_certificates, course_certificates, faker)
        Command.seed_program_cert_records(user, programs, faker)
        pathways = Command.seed_pathways(site, programs, faker)
        Command.seed_user_credit_pathways(user, pathways)
        industry_pathway = Command.seed_industry_pathway(site, programs, faker)

    @staticmethod
    def get_site(site_name):
        """Get a specific site by its name"""
        site = Site.objects.get(name=site_name)
        if site:
            logger.info("Retrieved site: %s", site_name)
        else:
            logger.info("Error retrieving site: %s", site_name)
        return site

    @staticmethod
    def seed_organizations(site, faker):
        """Seed two organizations"""
        organization1, created = Organization.objects.get_or_create(site=site, uuid=faker.uuid4(), name="Test-Org-1")
        Command.log_action("Organization", "Test-Org-1", created)

        organization2, created = Organization.objects.get_or_create(site=site, uuid=faker.uuid4(), name="Test-Org-2")
        Command.log_action("Organization", "Test-Org-2", created)

        return [organization1, organization2]

    @staticmethod
    def seed_courses(site, organizations, faker):
        """Seed two courses per organization

        Unlike in the context of a UserCredential.course_id, course_id here does literally mean
        the course.uuid, not course_run.key.
        """
        courses = []
        course_id = 1

        for organization in organizations:
            course1, created = Course.objects.get_or_create(
                site=site, uuid=faker.uuid4(), title=f"Course {course_id}", key=f"Course-{course_id}"
            )
            course1.owners.set([organization])
            courses.append(course1)
            Command.log_action("Course", course_id, created)

            course2, created = Course.objects.get_or_create(
                site=site,
                uuid=faker.uuid4(),
                title="Course {}".format(course_id + 1),
                key="Course-{}".format(course_id + 1),
            )
            course2.owners.set([organization])
            courses.append(course2)
            Command.log_action("Course", course_id + 1, created)

            course_id += 2

        return courses

    @staticmethod
    def seed_course_runs(courses, faker):
        """Seed one course run per course"""
        course_runs = []
        course_run_id = 1

        for course in courses:
            organization = course.owners.all()[0]
            key = f"course-v1:{organization.name}+{course.key}+{course_run_id}"
            course_run, created = CourseRun.objects.get_or_create(
                course=course,
                uuid=faker.uuid4(),
                start_date=datetime(2018, 1, 1, tzinfo=TIME_ZONE_CLASS),
                end_date=datetime(2018, 6, 1, tzinfo=TIME_ZONE_CLASS),
                key=key,
            )

            Command.log_action("CourseRun for", course.title, created)

            course_runs.append(course_run)
            course_run_id += 1

        return course_runs

    @staticmethod
    def seed_programs(site, organizations, course_runs, faker):
        """Seed one program per org of all course runs for that org"""
        programs = []
        program_id = 1

        for organization in organizations:
            courses = Course.objects.filter(owners=organization)
            course_runs = [CourseRun.objects.get(course=course) for course in courses]

            program, created = Program.objects.update_or_create(
                site=site,
                uuid=faker.uuid4(),
                defaults={
                    "title": f"Program {program_id}",
                    "status": "active",
                },
            )
            program.course_runs.set(course_runs)
            program.authoring_organizations.set([organization])
            Command.log_action("Program", program_id, created)

            programs.append(program)
            program_id += 1

        return programs

    @staticmethod
    def get_user(username):
        """Get the test user"""
        return get_user_by_username(username=username)

    @staticmethod
    def seed_user_grades(user, course_runs):
        """Seed user grades for the test users"""
        user_grades = []
        for course_run in course_runs:
            user_grade, created = UserGrade.objects.get_or_create(
                username=user.username, course_run=course_run, letter_grade="B", percent_grade=0.82, verified=True
            )

            Command.log_action("User Grade for", course_run.course.title, created)
            user_grades.append(user_grade)

        return user_grades

    @staticmethod
    def seed_signatories(organizations):
        """Seed one signatory per org"""

        signatories = []

        for organization in organizations:
            signatory, created = Signatory.objects.get_or_create(
                name=organization.name, title=organization.name
            )  # TODO: add image

            Command.log_action("Signatory for", organization.name, created)
            signatories.append(signatory)

        return signatories

    @staticmethod
    def seed_program_certificates(site, programs, signatories):
        """Seed program certs for two programs"""
        program_certificates = []

        for program in programs:
            program_certificate, created = ProgramCertificate.objects.update_or_create(
                site=site,
                program_uuid=program.uuid,
                defaults={
                    "is_active": True,
                    "language": "en",
                },
            )
            program_certificate.signatories.set(signatories)
            program_certificate.save()

            Command.log_action("Program certificate for", program.title, created)
            program_certificates.append(program_certificate)

        return program_certificates

    @staticmethod
    def seed_course_certificates(site, course_runs, signatories):
        """Seed course certificates for all courses for user edx"""
        course_certificates = []

        for course_run in course_runs:
            course_certificate, created = CourseCertificate.objects.update_or_create(
                site=site,
                course_run=course_run,
                course_id=course_run.key,
                defaults={
                    "is_active": True,
                    "certificate_type": CertificateType.VERIFIED,
                },
            )
            course_certificate.signatories.set(signatories)
            course_certificate.save()
            Command.log_action("Course certificate for course run", course_run, created)
            course_certificates.append(course_certificate)

        return course_certificates

    @staticmethod
    def seed_user_credentials(user, program_certificates, course_certificates, faker):
        """Seed user credentials for user"""
        user_program_credentials = []
        user_course_credentials = []

        for program_certificate in program_certificates:
            user_credential, created = UserCredential.objects.get_or_create(
                credential_content_type=ContentType.objects.get_for_model(program_certificate),
                credential_id=program_certificate.id,
                username=user.username,
                status=UserCredential.AWARDED,
            )

            Command.log_action("User Credential for", program_certificate, created)
            user_program_credentials.append(user_credential)

        for course_certificate in course_certificates:
            user_credential, created = UserCredential.objects.get_or_create(
                credential_content_type=ContentType.objects.get_for_model(course_certificate),
                credential_id=course_certificate.id,
                username=user.username,
                status=UserCredential.AWARDED,
            )

            Command.log_action("User Credential for Course", course_certificate.course_id, created)
            user_course_credentials.append(user_credential)

        return user_program_credentials, user_course_credentials

    @staticmethod
    def seed_program_cert_records(user, programs, faker):
        """Seed  program cert records for user"""
        program_cert_records = []

        for program in programs:
            program_cert_record, created = ProgramCertRecord.objects.get_or_create(
                program=program, user=user, uuid=faker.uuid4()
            )

            Command.log_action("Program Cert Record with ID", program_cert_record.id, created)
            program_cert_records.append(program_cert_record)

        return program_cert_records

    @staticmethod
    def seed_pathways(site, programs, faker):
        """Seed two pathways"""
        all_program_pathway, created = Pathway.objects.get_or_create(
            site=site, name="All program pathway", org_name="MIT", uuid=faker.uuid4()
        )
        all_program_pathway.programs.set(programs)
        Command.log_action("Pathway with name", all_program_pathway.name, created)

        one_program_pathway, created = Pathway.objects.get_or_create(
            site=site, name="One program pathway", org_name="MIT", uuid=faker.uuid4()
        )
        one_program_pathway.programs.set([programs[0]])
        Command.log_action("Pathway with name", one_program_pathway.name, created)

        return [all_program_pathway, one_program_pathway]

    @staticmethod
    def seed_user_credit_pathways(user, pathways):
        """Seed one UserCreditPathway, this denotes that a user
        has sent an email to that pathway"""
        user_credit_pathway, created = UserCreditPathway.objects.get_or_create(
            user=user, pathway=pathways[1], status=UserCreditPathwayStatus.SENT
        )
        Command.log_action("UserCreditPathway for user", user.username, created)

        return user_credit_pathway

    @staticmethod
    def seed_industry_pathway(site, programs, faker):
        """Seed one industry pathway"""
        industry_pathway, created = Pathway.objects.get_or_create(
            site=site,
            uuid=faker.uuid4(),
            defaults={
                "name": "Test industry pathway",
                "org_name": "Dunder Mifflin",
                "pathway_type": PathwayType.INDUSTRY.value,
            },
        )
        industry_pathway.programs.set(programs)
        Command.log_action("Industry pathway with name", industry_pathway.name, created)

        return industry_pathway
