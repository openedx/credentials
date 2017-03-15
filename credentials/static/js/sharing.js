import $ from "jquery";

$(document).ready(function () {
    var $shareButton = $('.action-facebook');

    $.ajaxSetup({cache: true});
    $.getScript('//connect.facebook.net/en_US/sdk.js', function () {
        FB.init({
            appId: window.edx.facebook.appId,
            version: 'v2.7'
        });

        // Activate the sharing button
        $shareButton.removeAttr('disabled');
    });

    $shareButton.click(function () {
        FB.ui({
            method: 'share',
            href: window.edx.facebook.href,
            quote: window.edx.facebook.quote,
        }, function (response) {
            // TODO Log to Segment. The response will be empty since we don't use Facebook login.
        });
    });
});
