const facebookAppId = window.edx.facebook.appId;

function addFacebookClickHandler() {
  FB.ui({
    method: 'share',
    href: window.edx.facebook.href,
  });
}

function initializeFacebook() {
  const shareButton = document.querySelector('.action-facebook');

  FB.init({
    appId: facebookAppId,
    xfbml: true,
    version: 'v2.8',
  });
  FB.AppEvents.logPageView();

  // Activate the sharing button
  if (shareButton !== null) {
    shareButton.removeAttribute('disabled');
    shareButton.addEventListener('click', addFacebookClickHandler);
  }
}

window.fbAsyncInit = initializeFacebook;
