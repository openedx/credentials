Analytics
=========

The credentials IDA uses Segment.io to track events.  If you set the ``segment_key`` variable in your site_configuration, a variety of events (segment API calls) will be triggered when navigating through the UI.

Analytics for legacy/template pages
===================================
``static/js/analytics.js``

For pages with static DOM elements, we add event specific ``data-track-event-*`` HTML attributes directly, and the analytics.js script parses them on page load.

For example (from ``templates/_actions.html``):

.. code-block:: HTML

       <button title="{% trans 'Share this certificate via Facebook' as tmsg %} {{tmsg | htmlescape}}" class="action btn icon-only action-facebook"
              disabled data-track-type="click"
              data-track-event="edx.bi.credentials.facebook_share.attempted"
              data-track-event-property-category="certificates"
              data-track-event-property-credential-uuid="{{ user_credential.uuid }}"
              data-track-event-property-program-uuid="{{ user_credential.credential.program_uuid }}">
        <span class="fa fa-facebook" aria-hidden="true"></span>
        <span class="action-label">{% trans 'Share this certificate via Facebook' as tmsg %}{{ tmsg | htmlescape }}</span>
      </button>
       

Analytics for react pages
=========================
``static/components/Analytics.jsx``

For newer react-based UIs, we use the ``trackEvent()`` function defined in Analytics.jsx.  This function is intended to be added as an event listener (e.g. onClick) on a component.  However, trackEvent() still relies on analytics.js being loaded on the page, as it access the ``window.edx.analytics.track`` segment function.

for example (from ``static/components/ShareProgramRecordModal.jsx``)

.. code-block:: JSX

        <Button
            label={gettext('Copy Link')}
            className={['btn-primary']}
            onClick={trackEvent('edx.bi.credentials.program_record.share_url_copied', {
              category: 'records',
              'program-uuid': this.props.uuid,
            })}
          />

