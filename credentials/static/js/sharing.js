import $ from "jquery";

$(document).ready(function () {
    var facebookAppId = window.edx.facebook.appId;

    if (facebookAppId) {
        $.ajaxSetup({cache: true});
        $.getScript('//connect.facebook.net/en_US/sdk.js', function () {
            var $shareButton = $('.action-facebook');

            FB.init({
                appId: facebookAppId,
                version: 'v2.7'
            });

            // Activate the sharing button
            $shareButton.removeAttr('disabled');

            $shareButton.click(function () {
                FB.ui({
                    method: 'share',
                    href: window.edx.facebook.href
                }, function (response) {
                    // TODO Log to Segment. The response will be empty since we don't use Facebook login.
                });
            });
        });
    }
});
