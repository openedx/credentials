import logging

from edx_ace import MessageType

log = logging.getLogger(__name__)


# This code also exists in the Records app `messages.py` file. Any changes here should be duplicated there as well
# until we can come back around and create a common base Messaging class that the Credentials and Records app will
# utilize.
class ProgramCertificateIssuedMessage(MessageType):
    def __init__(
        self, site, user_email=None, *args, **kwargs
    ):  # pylint: disable=unused-argument, keyword-arg-before-vararg
        super().__init__(*args, **kwargs)

        if site.siteconfiguration.partner_from_address:
            from_address = site.siteconfiguration.partner_from_address
        else:
            log.info(f"No partner from address found. Using default no-reply@{site.domain}")
            from_address = "no-reply@" + site.domain

        self.options.update(
            {
                "reply_to": [from_address],
            }
        )

        self.options.update(
            {
                "from_address": from_address,
            }
        )
        self.context.update(
            {
                "platform_name": site.siteconfiguration.platform_name,
            }
        )
