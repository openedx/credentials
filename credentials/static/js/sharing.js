var facebookAppId = window.edx.facebook.appId;

if (facebookAppId) {
    window.fbAsyncInit = function () {
        var shareButton = document.getElementsByClassName('action-facebook')[0];

        FB.init({
            appId: facebookAppId,
            xfbml: true,
            version: 'v2.8'
        });
        FB.AppEvents.logPageView();

        // Activate the sharing button
        shareButton.removeAttribute('disabled');

        shareButton.onclick = function () {
            FB.ui({
                method: 'share',
                href: window.edx.facebook.href
            }, function (response) {
                // TODO Log to Segment. The response will be empty since we don't use Facebook login.
            });
        };
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
