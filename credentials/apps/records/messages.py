from edx_ace import MessageType


# This code also exists in the Credentials app `messages.py` file. Any changes here should be duplicated there as well
# until we can come back around and create a common base Messaging class that the Credentials and Records app will
# utilize.
class ProgramCreditRequest(MessageType):
    def __init__(self, site, user_email=None, *args, **kwargs):  # pylint: disable=keyword-arg-before-vararg
        super().__init__(*args, **kwargs)

        if site.siteconfiguration.partner_from_address:
            from_address = site.siteconfiguration.partner_from_address
        else:
            from_address = 'no-reply@' + site.domain

        if user_email:
            self.options.update({
                'reply_to': [user_email],
            })

        self.options.update({
            'from_address': from_address,
        })
        self.context.update({
            'platform_name': site.siteconfiguration.platform_name,
        })
