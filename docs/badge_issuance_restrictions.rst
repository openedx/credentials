Badge Issuance Restrictions
===========================

Credentials supports an optional external restriction check for Credly badge issuance.

Overview
--------

When a learner completes all requirements for a Credly badge, Credentials normally
issues the badge immediately. Some deployments need an additional validation step
before badge issuance, based on business rules managed outside of Credentials.

When badge issuance restrictions are enabled, Credentials checks an external API
before issuing the badge. The API is queried using the course context associated
with each fulfillment that contributed to badge completion.

If the external API indicates that badge issuance is not allowed for a matching
course, Credentials does not issue the badge.

This feature is optional and disabled by default.

Configuration
-------------

To enable badge issuance restrictions, configure the following settings:

* ``BADGES_ENABLE_ISSUANCE_RESTRICTIONS``
  Enables the restriction check.

  Example::

    BADGES_ENABLE_ISSUANCE_RESTRICTIONS = True

* ``BADGES_ISSUANCE_RESTRICTIONS_API_URL``
  The external API endpoint used to validate whether badge issuance is allowed
  for a fulfillment course.

  Example::

    BADGES_ISSUANCE_RESTRICTIONS_API_URL = "https://example.com/api/v1/restrictions/"

* ``BADGES_ISSUANCE_RESTRICTIONS_FLAG_NAME``
  The name of the response field that Credentials reads from the matched API
  result to determine whether badge issuance is allowed.

  Example::

    BADGES_ISSUANCE_RESTRICTIONS_FLAG_NAME = "allow_badges"

Credentials uses the existing backend service OAuth client configuration for
authenticated inter-service requests:

* ``BACKEND_SERVICE_EDX_OAUTH2_PROVIDER_URL``
* ``BACKEND_SERVICE_EDX_OAUTH2_KEY``
* ``BACKEND_SERVICE_EDX_OAUTH2_SECRET``

Behavior
--------

When enabled, the restriction check behaves as follows:

#. Badge completion is detected for a Credly badge.
#. Credentials loads the learner's badge progress.
#. Credentials inspects the related fulfillments.
#. For each fulfillment with a ``course_key``, Credentials calls the configured
   external API.
#. Credentials searches the API response for an exact match on ``ccx_id``.
#. Credentials reads the configured restriction flag from the matching result.
#. If the flag indicates badge issuance is not allowed, the badge is not issued.
#. Otherwise, issuance proceeds normally.

Default behavior
----------------

This feature is disabled by default.

If the feature is disabled, Credentials behaves exactly as before and no external
restriction check is performed.

If the feature is enabled but:

* no matching restriction data is returned
* the external API returns an error
* the external API response cannot be parsed
* no fulfillment has a course key

then Credentials allows badge issuance by default.

Scope
-----

This feature currently applies only to the Credly badge issuance flow.

It does not change the Accredible badge issuance flow.

Expected API response
---------------------

Example response:

.. code-block:: json

   {
     "results": [
       {
         "ccx_id": "course-v1:ORG+COURSE+RUN+ccx@1",
         "allow_badges": false
       }
     ]
   }

In this example:

* ``ccx_id`` is compared against the fulfillment ``course_key``
* ``allow_badges`` is an example restriction flag
* the actual flag name is defined by ``BADGES_ISSUANCE_RESTRICTIONS_FLAG_NAME``

Notes for operators
-------------------

This feature is intended for deployments that need to integrate badge issuance with
externally managed business rules.

Operators enabling this feature should ensure that:

* the configured API is reachable from Credentials
* the backend service OAuth settings are valid
* the API returns stable course identifiers that match fulfillment course keys
* the configured restriction flag is present in the API response
