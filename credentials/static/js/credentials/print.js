require([
        'jquery'
    ],
    function ($) {
        'use strict';

        $('#action-print-view').click(function (event) {
            event.preventDefault();
            window.print();
        });
    }
);
