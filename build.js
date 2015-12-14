/* jshint asi:true, expr:true */
({
    mainConfigFile: 'credentials/static/js/config.js',
    baseUrl: 'credentials/static',
    dir: 'credentials/static/build',
    removeCombined: true,
    findNestedDependencies: true,

    // Disable all optimization. django-compressor will handle that for us.
    optimizeCss: false,
    optimize: 'none',
    normalizeDirDefines: 'all',
    skipDirOptimize: true,

    preserveLicenseComments: true,
    modules: [
        {
            name: 'js/common'
        },
        {
            name: 'js/config'
        },
    ]
})
