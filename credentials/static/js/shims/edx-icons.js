define([
        'afontgarde'
    ],
    function( AFontGarde ) {
        'use strict';

        return new AFontGarde('edx-icons', {
            // Check a few random icons to see if our font loads
            glyphs: '\uE621\uE622\uE623',

            success: function() {
                console.log('Successfully loaded AFontGarde.');
            }
        });
    }
);
