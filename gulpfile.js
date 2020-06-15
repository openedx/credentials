'use strict';

const eslint = require('gulp-eslint');
const gulp = require('gulp');
const jsPath = 'credentials/static/{components,js}/**/*.{js,jsx}';
const Server = require('karma').Server;

gulp.task('lint', () => {
  // ESLint ignores files with "node_modules" paths.
  // So, it's best to have gulp ignore the directory as well.
  // Also, Be sure to return the stream from the task;
  // Otherwise, the task may end before the stream has finished.


  return gulp.src([jsPath, '!node_modules/**'])

    // eslint() attaches the lint output to the "eslint" property
    // of the file object so it can be used by other modules.
    .pipe(eslint())

    // eslint.format() outputs the lint results to the console.
    // Alternatively use eslint.formatEach() (see Docs).
    .pipe(eslint.format())

    // To have the process exit with an error code (1) on
    // lint error, return the stream and pipe to failAfterError last.
    .pipe(eslint.failAfterError());
});

gulp.task('test', function (done) {
  new Server({
    configFile: __dirname + '/karma.conf.js',
  }, done).start();
});

/**
 * Monitors the source and test files, running tests and linters when changes detected.
 */
gulp.task('watch', function () {
  gulp.watch(jsPath, ['lint', 'test',]);
});

gulp.task('default', gulp.series('test'));
