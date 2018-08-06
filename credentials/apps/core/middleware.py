"""
Middleware for segment user identification.
"""

from analytics.client import Client as SegmentClient


class SegmentMiddleware(object):
    """
    Middleware that parse `_ga` cookie and save/update in user tracking context.
    """

    def process_request(self, request):
        user = request.user
        if user.is_authenticated():
            # import pdb; pdb.set_trace()
            print(user.id)
#             user_tracking_id = None
#             if user_tracking_id is None:
#                 # Even if we cannot extract a good platform user ID from the context, we can still track the
#                 # event with an arbitrary local user ID. However, we need to disambiguate the ID we choose
#                 # since there's no guarantee it won't collide with a platform user ID that may be tracked
#                 # at some point.
#                 user_tracking_id = 'credentials-{}'.format(user.id)



#             SegmentClient.identify(
#                 user_tracking_id,
#                 {
#                     name: user.name,
#                     email: user.email,
#                 },
#                 {
#                     integrations: {
#                     # Disable MailChimp because we don't want to update the user's email
#                     # and username in MailChimp based on this request. We only need to capture
#                     # this data in MailChimp on registration/activation.
#                         MailChimp: false
#                     }
#                 }
#             )



# if hasattr(settings, 'LMS_SEGMENT_KEY') and settings.LMS_SEGMENT_KEY:
#         tracking_context = tracker.get_tracker().resolve_context()
#         analytics.identify(
#             user.id,
#             {
#                 'email': request.POST['email'],
#                 'username': user.username
#             },
#             {
#                 # Disable MailChimp because we don't want to update the user's email
#                 # and username in MailChimp on every page load. We only need to capture
#                 # this data on registration/activation.
#                 'MailChimp': False
#             }
#         )
