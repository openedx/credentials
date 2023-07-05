import pytest
from django.test import TestCase

from ..open_badges import AchievementSchema, CredentialSubjectSchema, OpenBadges301DataModel, OpenBadgesDataModel


class OpenBadgesTestCase(TestCase):
    def test_open_badges_get_context(self):
        self.assertEqual(type(OpenBadgesDataModel.get_context()), list)

    def test_open_badges_get_types(self):
        self.assertEqual(type(OpenBadgesDataModel.get_types()), list)

    def test_open_badges_301_get_context(self):
        self.assertEqual(type(OpenBadges301DataModel.get_context()), list)


class TestOpenBadgesDataModel:
    """
    Open Badges v3.0 composition.
    """

    @pytest.mark.django_db
    def test_default_name(self, issuance_line):
        """
        Predefined for Program certificate value is used as `name` property.
        """
        expected_default_name = "Program certificate for passing a program TestProgram1"

        composed_obv3 = OpenBadgesDataModel(issuance_line).data

        assert composed_obv3["name"] == expected_default_name

    @pytest.mark.django_db
    def test_overridden_name(self, monkeypatch, issuance_line):
        """
        Program certificate title overrides `name` property.
        """
        expected_overridden_name = "Explicit Credential Title"
        monkeypatch.setattr(issuance_line.user_credential.credential, "title", expected_overridden_name)

        composed_obv3 = OpenBadgesDataModel(issuance_line).data

        assert composed_obv3["name"] == expected_overridden_name

    @pytest.mark.django_db
    def test_credential_subject_id(self, issuance_line):
        """
        Credential Subject `id` property.
        """
        expected_id = issuance_line.subject_id

        composed_obv3 = OpenBadgesDataModel(issuance_line).data

        assert composed_obv3["credentialSubject"]["id"] == expected_id

    @pytest.mark.django_db
    def test_credential_subject_type(self, issuance_line):
        """
        Credential Subject `type` property.
        """
        expected_type = CredentialSubjectSchema.TYPE

        composed_obv3 = OpenBadgesDataModel(issuance_line).data

        assert composed_obv3["credentialSubject"]["type"] == expected_type

    @pytest.mark.django_db
    def test_credential_subject_name(self, monkeypatch, issuance_line, user):
        """
        Credential Subject `name` property.
        """
        expected_name = user.full_name
        monkeypatch.setattr(issuance_line.user_credential, "username", user.username)

        composed_obv3 = OpenBadgesDataModel(issuance_line).data

        assert composed_obv3["credentialSubject"]["name"] == expected_name

    @pytest.mark.django_db
    def test_credential_subject_achievement_id(self, issuance_line):
        """
        Credential Subject Achievement `id` property.
        """
        expected_id = str(issuance_line.user_credential.uuid)

        composed_obv3 = OpenBadgesDataModel(issuance_line).data

        assert composed_obv3["credentialSubject"]["achievement"]["id"] == expected_id

    @pytest.mark.django_db
    def test_credential_subject_achievement_type(self, issuance_line):
        """
        Credential Subject Achievement `type` property.
        """
        expected_type = AchievementSchema.TYPE

        composed_obv3 = OpenBadgesDataModel(issuance_line).data

        assert composed_obv3["credentialSubject"]["achievement"]["type"] == expected_type

    @pytest.mark.django_db
    def test_credential_subject_achievement_default_name(self, issuance_line):
        """
        Credential Subject Achievement default `name` property.
        """
        expected_default_name = "Program certificate for passing a program TestProgram1"

        composed_obv3 = OpenBadgesDataModel(issuance_line).data

        assert composed_obv3["credentialSubject"]["achievement"]["name"] == expected_default_name

    @pytest.mark.django_db
    def test_credential_subject_achievement_overridden_name(self, monkeypatch, issuance_line):
        """
        Credential Subject Achievement overridden `name` property.
        """
        expected_overridden_name = "Explicit Credential Title"
        monkeypatch.setattr(issuance_line.user_credential.credential, "title", expected_overridden_name)

        composed_obv3 = OpenBadgesDataModel(issuance_line).data

        assert composed_obv3["credentialSubject"]["achievement"]["name"] == expected_overridden_name

    @pytest.mark.django_db
    def test_credential_subject_achievement_description(
        self, monkeypatch, issuance_line, user_credential, site_configuration
    ):  # pylint: disable=unused-argument
        """
        Credential Subject Achievement `description` property.
        """
        expected_description = "Program certificate is granted on program TestProgram1 completion offered by TestOrg1, TestOrg2, in collaboration with TestPlatformName1. The TestProgram1 program includes 2 course(s)."  # pylint: disable=line-too-long
        monkeypatch.setattr(issuance_line.user_credential.credential.program, "total_hours_of_effort", None)

        composed_obv3 = OpenBadgesDataModel(issuance_line).data

        assert composed_obv3["credentialSubject"]["achievement"]["description"] == expected_description

    @pytest.mark.django_db
    def test_credential_subject_achievement_description_with_effort(
        self, issuance_line, user_credential, site_configuration
    ):  # pylint: disable=unused-argument
        """
        Credential Subject Achievement `description` property (Program Certificate with Effort specified).
        """
        expected_description = "Program certificate is granted on program TestProgram1 completion offered by TestOrg1, TestOrg2, in collaboration with TestPlatformName1. The TestProgram1 program includes 2 course(s), with total 10 Hours of effort required to complete it."  # pylint: disable=line-too-long

        composed_obv3 = OpenBadgesDataModel(issuance_line).data

        assert composed_obv3["credentialSubject"]["achievement"]["description"] == expected_description

    @pytest.mark.django_db
    def test_credential_subject_achievement_criteria(
        self, monkeypatch, issuance_line, user, site_configuration
    ):  # pylint: disable=unused-argument
        """
        Credential Subject Achievement `criteria` property.
        """
        expected_narrative_value = "TestUser1 FullName successfully completed all courses and received passing grades for a Professional Certificate in TestProgram1 a program offered by TestOrg1, TestOrg2, in collaboration with TestPlatformName1."  # pylint: disable=line-too-long
        monkeypatch.setattr(issuance_line.user_credential, "username", user.username)

        composed_obv3 = OpenBadgesDataModel(issuance_line).data

        assert composed_obv3["credentialSubject"]["achievement"]["criteria"]["narrative"] == expected_narrative_value
