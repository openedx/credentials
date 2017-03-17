let facebookAppId = window.edx.facebook.appId;

if (facebookAppId) {
    window.fbAsyncInit = function () {
        let shareButton = document.querySelector('.action-facebook');

        FB.init({
            appId: facebookAppId,
            xfbml: true,
            version: 'v2.8'
        });
        FB.AppEvents.logPageView();

        // Activate the sharing button
        shareButton.removeAttribute('disabled');

        shareButton.addEventListener('click', function () {
            FB.ui({
                method: 'share',
                href: window.edx.facebook.href
            }, function (response) {
                // NOTE (CCB): We intentionally do nothing here. The click handler in analytics.js
                // is responsible for firing analytics events.
            });
        });
    };

    (function (d, s, id) {
        var js, fjs = d.getElementsByTagName(s)[0];
        if (d.getElementById(id)) {
            return;
        }
        js = d.createElement(s);
        js.id = id;
        js.src = "//connect.facebook.net/en_US/sdk.js";
        fjs.parentNode.insertBefore(js, fjs);
    }(document, 'script', 'facebook-jssdk'));
}
