'use strict';

const gulp = require('gulp');
const jsPath = 'credentials/static/{components,js}/**/*.{js,jsx}';
const Server = require('karma').Server;

gulp.task('test', function (done) {
  new Server({
    configFile: __dirname + '/karma.conf.js',
  }, done).start();
});

/**
 * Monitors the source and test files, running tests and linters when changes detected.
 */
gulp.task('watch', function () {
  gulp.watch(jsPath, ['test',]);
});

gulp.task('default', gulp.series('test'));
