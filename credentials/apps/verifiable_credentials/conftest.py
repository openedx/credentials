# pylint: disable=unused-argument,redefined-outer-name
"""
Pytest: Verifiable Credentials base testing config/fixtures.
"""
import pytest

from credentials.apps.catalog.tests.factories import (
    CourseFactory,
    CourseRunFactory,
    OrganizationFactory,
    ProgramFactory,
)
from credentials.apps.core.tests.factories import SiteConfigurationFactory, SiteFactory, UserFactory
from credentials.apps.credentials.tests.factories import (
    CourseCertificateFactory,
    ProgramCertificateFactory,
    UserCredentialFactory,
)
from credentials.apps.verifiable_credentials.issuance.tests.factories import IssuanceLineFactory


TEST_ISSUER_CONFIG = {
    "ID": "test-issuer-did",
    "KEY": "test-issuer-key",
    "NAME": "test-issuer-name",
}


@pytest.fixture(autouse=True)
def vc_enabled(settings):
    settings.ENABLE_VERIFIABLE_CREDENTIALS = True


@pytest.fixture()
def vc_disabled(settings):
    settings.ENABLE_VERIFIABLE_CREDENTIALS = False


@pytest.fixture()
def verifiable_credentials_data_model():
    return "credentials.apps.verifiable_credentials.composition.verifiable_credentials.VerifiableCredentialsDataModel"


@pytest.fixture()
def open_badges_data_model():
    return "credentials.apps.verifiable_credentials.composition.open_badges.OpenBadgesDataModel"


@pytest.fixture()
def status_list_data_model():
    return "credentials.apps.verifiable_credentials.composition.status_list.StatusListDataModel"


@pytest.fixture()
def issuance_line_serializer():
    return "credentials.apps.verifiable_credentials.issuance.serializers.IssuanceLineSerializer"


@pytest.fixture()
def learner_credentials_storage():
    return "credentials.apps.verifiable_credentials.storages.learner_credential_wallet.LCWallet"


@pytest.fixture()
def default_issuer_config():
    return TEST_ISSUER_CONFIG


@pytest.fixture()
def user():
    return UserFactory(username="testuser1", full_name="TestUser1 FullName")


@pytest.fixture()
def site():
    return SiteFactory(name="TestSite1")


@pytest.fixture()
def site_configuration(db, site):
    return SiteConfigurationFactory(site=site, platform_name="TestPlatformName1")


@pytest.fixture()
def two_organizations(site):
    return [OrganizationFactory.create(name=name, site=site) for name in ["TestOrg1", "TestOrg2"]]


@pytest.fixture()
def course(site):
    return CourseFactory.create(site=site)


@pytest.fixture()
def two_course_runs(course):
    return CourseRunFactory.create_batch(2, course=course)


@pytest.fixture()
def program_setup(site, two_course_runs, two_organizations):
    return ProgramFactory(
        title="TestProgram1",
        total_hours_of_effort=10,
        course_runs=two_course_runs,
        authoring_organizations=two_organizations,
        site=site,
    )


@pytest.fixture()
def program_certificate(site, program_setup):
    return ProgramCertificateFactory(program=program_setup, site=site)


@pytest.fixture()
def course_certificate(site, two_course_runs):
    return CourseCertificateFactory.create(course_id=two_course_runs[0].key, course_run=two_course_runs[0], site=site)


@pytest.fixture()
def program_user_credential(program_certificate):
    return UserCredentialFactory(credential=program_certificate)


@pytest.fixture()
def course_user_credential(course_certificate):
    return UserCredentialFactory(credential=course_certificate)


@pytest.fixture()
def program_issuance_line(program_user_credential):
    return IssuanceLineFactory(user_credential=program_user_credential, subject_id="did:key:test")


@pytest.fixture()
def course_issuance_line(course_user_credential):
    return IssuanceLineFactory(user_credential=course_user_credential, subject_id="did:key:test")
