$(document).ready(function () {
    'use strict';
    $('#action-print-view').click(function() {
        event.preventDefault();
        window.print();
    });
});
