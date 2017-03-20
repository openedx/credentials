const facebookAppId = window.edx.facebook.appId;

function addFacebookClickHandler() {
  'use strict';

  FB.ui({
    method: 'share',
    href: window.edx.facebook.href,
  });
}

function initializeFacebook() {
  'use strict';

  const shareButton = document.querySelector('.action-facebook');

  FB.init({
    appId: facebookAppId,
    xfbml: true,
    version: 'v2.8',
  });
  FB.AppEvents.logPageView();

  // Activate the sharing button
  shareButton.removeAttribute('disabled');
  shareButton.addEventListener('click', addFacebookClickHandler);
}

window.fbAsyncInit = initializeFacebook;
