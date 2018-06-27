/**
 * Click event handler.
 *
 * Emits a tracking event via window.analytics.track().
 */
function handleClick(event) {
  const target = event.target;

  const attributes = target.attributes;
  const eventName = target.getAttribute('data-track-event');
  const eventProperties = {};
  const eventPropertyPrefix = 'data-track-event-property-';

  // Build the properties hash by looking at all attributes with the specified prefix
  for (let i = 0, len = attributes.length; i < len; i += 1) {
    const attribute = attributes[i];
    const attributeName = attribute.name;

    if (attributeName.startsWith(eventPropertyPrefix)) {
      eventProperties[attributeName.replace(eventPropertyPrefix, '')] = attribute.value;
    }
  }

  window.analytics.track(eventName, eventProperties);
}

/**
 * Sets up click handlers for all elements with the attribute data-track-type set to "click".
 */
function setupClickHandlers() {
  const clickElements = document.querySelectorAll('[data-track-type="click"]');

  for (let i = 0, len = clickElements.length; i < len; i += 1) {
    const clickElement = clickElements[i];
    clickElement.addEventListener('click', handleClick);
  }
}

/*eslint-disable*/
!function(){var analytics=window.analytics=window.analytics||[];if(!analytics.initialize)if(analytics.invoked)window.console&&console.error&&console.error("Segment snippet included twice.");else{analytics.invoked=!0;analytics.methods=["trackSubmit","trackClick","trackLink","trackForm","pageview","identify","reset","group","track","ready","alias","debug","page","once","off","on"];analytics.factory=function(t){return function(){var e=Array.prototype.slice.call(arguments);e.unshift(t);analytics.push(e);return analytics}};for(var t=0;t<analytics.methods.length;t++){var e=analytics.methods[t];analytics[e]=analytics.factory(e)}analytics.load=function(t){var e=document.createElement("script");e.type="text/javascript";e.async=!0;e.src=("https:"===document.location.protocol?"https://":"http://")+"cdn.segment.com/analytics.js/v1/"+t+"/analytics.min.js";var n=document.getElementsByTagName("script")[0];n.parentNode.insertBefore(e,n)};analytics.SNIPPET_VERSION="4.0.0";
/*eslint-enable*/

  analytics.load(window.edx.segment.key);

  analytics.page();
  setupClickHandlers();
}
}();
