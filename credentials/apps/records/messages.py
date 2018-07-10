from edx_ace import MessageType


class ProgramCreditRequest(MessageType):
    def __init__(self, site, *args, **kwargs):
        super(ProgramCreditRequest, self).__init__(*args, **kwargs)

        if site.siteconfiguration.partner_from_address:
            from_address = site.siteconfiguration.partner_from_address
        else:
            from_address = 'no-reply@' + site.domain

        self.options.update({  # pylint: disable=no-member
            'from_address': from_address,
        })
        self.context.update({  # pylint: disable=no-member
            'platform_name': site.siteconfiguration.platform_name,
        })
