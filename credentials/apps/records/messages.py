from edx_ace import MessageType


class ProgramCreditRequest(MessageType):
    def __init__(self, site, user_email, *args, **kwargs):
        super(ProgramCreditRequest, self).__init__(*args, **kwargs)

        if not user_email:
            raise Exception("User email is missing.")

        from_address = user_email

        self.options.update({  # pylint: disable=no-member
            'from_address': from_address,
        })
        self.context.update({  # pylint: disable=no-member
            'platform_name': site.siteconfiguration.platform_name,
        })
