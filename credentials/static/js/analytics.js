!function(){var analytics=window.analytics=window.analytics||[];if(!analytics.initialize)if(analytics.invoked)window.console&&console.error&&console.error("Segment snippet included twice.");else{analytics.invoked=!0;analytics.methods=["trackSubmit","trackClick","trackLink","trackForm","pageview","identify","reset","group","track","ready","alias","debug","page","once","off","on"];analytics.factory=function(t){return function(){var e=Array.prototype.slice.call(arguments);e.unshift(t);analytics.push(e);return analytics}};for(var t=0;t<analytics.methods.length;t++){var e=analytics.methods[t];analytics[e]=analytics.factory(e)}analytics.load=function(t){var e=document.createElement("script");e.type="text/javascript";e.async=!0;e.src=("https:"===document.location.protocol?"https://":"http://")+"cdn.segment.com/analytics.js/v1/"+t+"/analytics.min.js";var n=document.getElementsByTagName("script")[0];n.parentNode.insertBefore(e,n)};analytics.SNIPPET_VERSION="4.0.0";
    const eventPropertyPrefix = 'data-track-event-property-';
    let user = window.edx.user;

    analytics.load(window.edx.segment.key);

    if (user) {
        analytics.identify(user.trackingId, {
            name: user.name,
            email: user.email
        });
    }

    analytics.page();

    // Setup click handlers
    for (let clickElement of document.querySelectorAll('[data-track-type="click"]')) {
        clickElement.addEventListener('click', function (e) {
            let eventName = this.getAttribute('data-track-event'),
                eventProperties = {};

            // Build the properties hash by looking at all attributes with the specified prefix
            for (let attribute of this.attributes) {
                let attributeName = attribute.name;

                if (attributeName.startsWith(eventPropertyPrefix)) {
                    eventProperties[attributeName.replace(eventPropertyPrefix, '')] = attribute.value;
                }
            }

            analytics.track(eventName, eventProperties);
        });
    }
}}();
