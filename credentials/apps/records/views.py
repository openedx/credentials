import csv
import io
import json
import logging
import urllib.parse
from typing import TYPE_CHECKING, Dict
from uuid import uuid4

from django import http
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import AccessMixin, LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
from django.views.generic import TemplateView, View
from django_ratelimit.decorators import ratelimit
from edx_ace import Recipient, ace
from segment.analytics.client import Client as SegmentClient

from credentials.apps.catalog.models import Pathway, Program
from credentials.apps.core.api import get_user_by_username
from credentials.apps.core.views import ThemeViewMixin
from credentials.apps.credentials.models import ProgramCertificate, UserCredential
from credentials.apps.records.api import get_program_record_data
from credentials.apps.records.constants import UserCreditPathwayStatus
from credentials.apps.records.messages import ProgramCreditRequest
from credentials.apps.records.models import ProgramCertRecord, UserCreditPathway
from credentials.shared.constants import PathwayType

from .constants import RECORDS_RATE_LIMIT


if TYPE_CHECKING:
    from credentials.apps.core.models import SiteConfiguration

log = logging.getLogger(__name__)
User = get_user_model()


def rate_limited(request, exception):  # pylint: disable=unused-argument
    log.warning("Credentials records endpoint is being throttled.")
    return JsonResponse({"error": "Too Many Requests"}, status=429)


class RecordsEnabledMixin:
    """Only allows view if records are enabled for the installation & site.
    Note that the API views are will still be active even if records is disabled.
    You may want to disable records support in the LMS if you want to stop data being sent over.
    If the user is not logged in, we direct them to a login page first."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if not request.site.siteconfiguration.records_enabled:
                raise http.Http404()
        return super().dispatch(request, *args, **kwargs)


class ConditionallyRequireLoginMixin(AccessMixin):
    """Variant of LoginRequiredMixin that allows a user not to be logged in if is_public argument is true"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated and not kwargs["is_public"]:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)


class RecordsListBaseView(LoginRequiredMixin, RecordsEnabledMixin, TemplateView, ThemeViewMixin):
    def _get_programs(self):
        """Returns a list of relevant program data (in get_user_program_data format)"""
        return []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_template = self.try_select_theme_template(["_base_style.html"])
        context.update(
            {
                "child_templates": {
                    "footer": self.select_theme_template(["_footer.html"]),
                    "header": self.select_theme_template(["_header.html"]),
                },
                "programs": json.dumps(self._get_programs(), sort_keys=True),
                "render_language": self.request.LANGUAGE_CODE,
                "request": self.request,
                "base_style_template": base_template,
            }
        )

        return context


class RecordsView(RecordsListBaseView):
    """
    The RecordsView view continues to be required after converting our legacy frontend to the Learner Record MFE. This
    is so we can redirect learners coming from their Learner Profile or the LMS to the Learner Record MFE. This also
    allows us to redirect users to the new MFE who may have bookmarked or shared their legacy records to others (e.g.
    through a Credit Pathway).
    """

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(settings.LEARNER_RECORD_MFE_RECORDS_PAGE_URL)


class ProgramRecordView(ConditionallyRequireLoginMixin, RecordsEnabledMixin, TemplateView, ThemeViewMixin):
    """
    The ProgramRecordView view continues to be required after converting our legacy frontend to the Learner Record MFE.
    This is so we can redirect learners coming from their Learner Profile or the LMS to the Learner Record MFE. This
    also allows us to redirect users to the new MFE who may have bookmarked or shared their legacy records to others
    (e.g. through a Credit Pathway).
    """

    def get(self, request, *args, **kwargs):
        uuid = kwargs["uuid"]

        # ensure that we are redirecting users to the correct route depending on the privacy level of the program record
        is_public = kwargs["is_public"]
        if is_public:
            url = urllib.parse.urljoin(settings.LEARNER_RECORD_MFE_RECORDS_PAGE_URL, f"shared/{uuid}")
        else:
            url = urllib.parse.urljoin(settings.LEARNER_RECORD_MFE_RECORDS_PAGE_URL, f"{uuid}")

        return HttpResponseRedirect(url)


@method_decorator(ratelimit(key="user", rate=RECORDS_RATE_LIMIT, method="POST", block=True), name="dispatch")
class ProgramSendView(LoginRequiredMixin, RecordsEnabledMixin, View):
    """
    Sends a program via email to a requested partner
    """

    def post(self, request, **kwargs):
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)

        username = body["username"]
        pathway_id = body["pathway_id"]
        program_uuid = kwargs["uuid"]

        # verify that the user or an admin is making the request
        if username != request.user.get_username() and not request.user.is_staff:
            return JsonResponse({"error": "Permission denied"}, status=403)

        credential = UserCredential.objects.filter(
            username=username, status=UserCredential.AWARDED, program_credentials__program_uuid=program_uuid
        )
        program = get_object_or_404(Program, uuid=program_uuid, site=request.site)
        pathway = get_object_or_404(
            Pathway,
            id=pathway_id,
            programs__uuid=program_uuid,
            pathway_type=PathwayType.CREDIT.value,
        )
        certificate = get_object_or_404(ProgramCertificate, program_uuid=program_uuid, site=request.site)
        user = get_object_or_404(User, username=username)
        preexisting_program_cert_record = ProgramCertRecord.objects.filter(user=user, program=program).exists()
        public_record, _ = ProgramCertRecord.objects.get_or_create(user=user, program=program)

        record_path = reverse("records:public_programs", kwargs={"uuid": public_record.uuid.hex})
        record_link = request.build_absolute_uri(record_path)
        csv_link = urllib.parse.urljoin(record_link, "csv")

        msg = ProgramCreditRequest(request.site, user.email).personalize(
            recipient=Recipient(lms_user_id=None, email_address=pathway.email),
            language=certificate.language,
            user_context={
                "pathway_name": pathway.name,
                "program_name": program.title,
                "record_link": record_link,
                "user_full_name": request.user.get_full_name() or request.user.username,
                "program_completed": credential.exists(),
                "previously_sent": False,
                "csv_link": csv_link,
            },
        )

        log.info(
            f"[Share Program Record] Internal Credentials User [{user.id}] is sharing their progress in program "
            f"[{program_uuid}] with pathway [{pathway_id}]"
        )
        ace.send(msg)

        # Create a record of this email
        if UserCreditPathway.objects.filter(user=user, pathway=pathway, program=program).exists():
            UserCreditPathway.objects.update_or_create(
                user=user,
                pathway=pathway,
                program=program,
                defaults={"status": UserCreditPathwayStatus.SENT},
            )
        elif (
            preexisting_program_cert_record
            and UserCreditPathway.objects.filter(user=user, pathway=pathway, program=None).exists()
        ):
            # A program for this user already existed, and a pathway for this user without a program exists.
            # Search for the entry without a program, and then update the status and program.
            UserCreditPathway.objects.update_or_create(
                user=user,
                pathway=pathway,
                program=None,
                defaults={"status": UserCreditPathwayStatus.SENT, "program": program},
            )
        else:
            UserCreditPathway.objects.update_or_create(
                user=user,
                pathway=pathway,
                program=program,
                defaults={"status": UserCreditPathwayStatus.SENT},
            )

        return http.HttpResponse(status=200)


@method_decorator(ratelimit(key="user", rate=RECORDS_RATE_LIMIT, method="POST", block=True), name="dispatch")
class ProgramRecordCreationView(LoginRequiredMixin, RecordsEnabledMixin, View):
    """
    Creates a new Program Certificate Record from given username and program uuid

    POST: /programs/:program_uuid/share/

    Returns:
        Dict: Dictionary containing the URL for the program certificate record instance

    If Learner Record MFE is enabled, the URL will route there instead.
    Make sure to include a base URL for the MFE in the `LEARNER_RECORD_MFE_RECORDS_PAGE_URL` environment variable
    """

    def post(self, request, **kwargs):
        body_unicode = request.body.decode("utf-8")
        body = json.loads(body_unicode)

        username = body["username"]

        user = get_user_by_username(username)
        if not user:
            return JsonResponse({"error": "User does not exist"}, status=404)

        # verify that the user or an admin is making the request
        if username != request.user.get_username() and not request.user.is_staff:
            return JsonResponse({"error": "Permission denied"}, status=403)

        program_uuid = kwargs["uuid"]
        program = get_object_or_404(Program, uuid=program_uuid, site=request.site)
        pcr, created = ProgramCertRecord.objects.get_or_create(user=user, program=program)
        status_code = 201 if created else 200

        url = request.build_absolute_uri(reverse("records:public_programs", kwargs={"uuid": pcr.uuid.hex}))
        return JsonResponse({"url": url}, status=status_code)


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
            self.event = kwargs.pop("event")
            self.properties = kwargs.pop("properties")
            self.context = kwargs.pop("context")
            self.anonymous_id = kwargs.pop("anonymous_id")
            self.segment_client = kwargs.pop("segment_client")
            super(ProgramRecordCsvView.SegmentHttpResponse, self).__init__(*args, **kwargs)

        def close(self):
            if self.segment_client:
                self.segment_client.track(
                    self.anonymous_id, event=self.event, properties=self.properties, context=self.context
                )
            super(ProgramRecordCsvView.SegmentHttpResponse, self).close()

    def get(self, request: HttpRequest, *args, **kwargs):
        site_configuration = request.site.siteconfiguration  # type: SiteConfiguration
        segment_client = None

        program_cert_record = get_object_or_404(ProgramCertRecord, uuid=kwargs.get("uuid"))
        try:
            record = get_program_record_data(
                program_cert_record.user,
                program_cert_record.program.uuid,
                request.site,
                platform_name=site_configuration.platform_name,
            )
        except Exception:
            log.error(
                "get_program_record failed for:\n"
                "   user: %s\n"
                "   program: %s\n"
                "   site: %s\n"
                "   platform_name: %s\n",
                program_cert_record.user.id,
                program_cert_record.program.uuid,
                request.site,
                site_configuration.platform_name,
            )
            raise

        program = record.get("program", None)  # type: Dict
        platform_name = record.get("platform_name", None)  # type: str
        learner = record.get("learner", None)  # type: Dict
        if not (program and platform_name and learner):
            log.info("get_program_record failed to find all program record data: %s", record)
            raise Http404

        user_metadata = [
            ["Program Name", program.get("name", None)],
            ["Program Type", program.get("type_name", None)],
            ["Platform Provider", platform_name],
            ["Authoring Organization(s)", program.get("school", None)],
            ["Learner Name", learner.get("full_name", None)],
            ["Username", learner.get("username", None)],
            ["Email", learner.get("email", None)],
            [""],
        ]

        properties = {
            "category": "records",
            "program_uuid": program_cert_record.program.uuid.hex,
            "record_uuid": program_cert_record.uuid.hex,
        }
        context = {
            "page": {
                "path": request.path,
                "referrer": request.headers.get("referer"),
                "url": request.build_absolute_uri(),
            },
            "userAgent": request.headers.get("user-agent"),
        }

        # continue gracefully in the absence of segment
        # 1. Use the value of 'ajs_anonymous_id' as the anonymous id if the cookie exists, otherwise generate a UUID to
        #    use as the anonymous id. See https://segment.com/docs/guides/how-to-guides/collect-pageviews-serverside/.
        # 2. If you fail on the segment client call, log the error but continue.
        anonymous_id = request.COOKIES.get("ajs_anonymous_id", str(uuid4()))
        if segment_key := site_configuration.segment_key:
            segment_client = SegmentClient(write_key=segment_key)
            try:
                segment_client.track(
                    None,  # anonymous_id,
                    context=context,
                    event="edx.bi.credentials.program_record.download_started",
                    properties=properties,
                )
            except AssertionError:
                log.exception("get_program_record failed calling segment")

        string_io = io.StringIO()
        writer = csv.writer(string_io, quoting=csv.QUOTE_ALL)
        writer.writerows(user_metadata)
        writer = csv.DictWriter(string_io, record["grades"][0].keys(), quoting=csv.QUOTE_ALL)
        writer.writeheader()
        writer.writerows(record["grades"])
        string_io.seek(0)
        filename = "{username}_{program_name}_grades".format(
            username=record["learner"]["username"], program_name=record["program"]["name"]
        )
        response = ProgramRecordCsvView.SegmentHttpResponse(
            string_io,
            anonymous_id=anonymous_id,
            content_type="text/csv",
            context=context,
            event="edx.bi.credentials.program_record.download_finished",
            properties=properties,
            segment_client=segment_client,
        )
        filename = filename.replace(" ", "_").lower()
        response["Content-Disposition"] = 'attachment; filename="{filename}.csv"'.format(filename=filename)
        return response
