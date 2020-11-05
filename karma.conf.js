const webpackConfig = require('./webpack.config.js');
delete webpackConfig.entry;

module.exports = function (config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    // NOTE (CCB): We only use jasmine-jquery to load fixtures.
    frameworks: ['jasmine-jquery', 'jasmine',],


    // list of files / patterns to load in the browser
    files: [
      'credentials/static/js/test/spec-runner.js',
      'credentials/static/js/**/*.js',
      {pattern: 'credentials/static/js/test/fixtures/**/*.html', included: false, served: true, watched: true},

    ],

    // list of files to exclude
    exclude: [],

    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
      'credentials/static/js/**/(!StringUtils).js': ['coverage'], // Exclude StringUtils as ES6 not support by Karma Cov
      'credentials/static/components/**/*.js': ['webpack'],
      'credentials/static/js/StringUtils.js': ['webpack'], // Explicitly include webpack for StringUtils for Karma
    },

    // enabled plugins
    plugins: [
      'karma-jasmine-jquery-2',
      'karma-jasmine',
      'karma-firefox-launcher',
      'karma-coverage',
      'karma-spec-reporter',
      'karma-webpack',
    ],

    // Karma coverage config
    coverageReporter: {
      reporters: [
        {type: 'text'},
        {type: 'lcov', subdir: 'report-lcov'}
      ]
    },

    webpack: webpackConfig,

    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['spec', 'coverage'],

    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: false,


    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['Firefox'],


    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: true,

    // Concurrency level
    // how many browser should be started simultaneous
    concurrency: Infinity
  })
}
