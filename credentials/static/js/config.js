require.config({
    baseUrl: '/static/',
    paths: {
        'backbone': 'bower_components/backbone/backbone',
        'jquery': 'bower_components/jquery/dist/jquery',
        'requirejs': 'bower_components/requirejs/require',
        'text': 'bower_components/text/text',
        'underscore': 'bower_components/underscore/underscore',
        'afontgarde': 'bower_components/edx-pattern-library/pattern-library/js/afontgarde',
        'modernizr-custom': 'bower_components/edx-pattern-library/pattern-library/js/modernizr-custom'
    },
    shim: {
        'afontgarde' : {
            deps: ['modernizr-custom'],
            exports: 'AFontGarde'
        }
    }
});
