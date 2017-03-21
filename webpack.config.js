const BundleTracker = require('webpack-bundle-tracker'),
    ExtractTextPlugin = require('extract-text-webpack-plugin'),
    fs = require('fs'),
    path = require('path'),
    webpack = require('webpack'),
    loaders = [
        {
            loader: 'css-loader',
            options: {
                minimize: true
            }
        },
        {
            loader: 'sass-loader',
            options: {
                includePaths: [path.resolve('./credentials/static/sass/')]
            }
        }
    ];

// TODO Update documentation
// TODO Update configuration to install themes package via npm
// TODO Update configuration to set THEME_DIR environment variable when calling `make static`
// TODO Finish https://github.com/edx/edx-themes/tree/webpack-theming

/**
 * Generates theme entries from a specified external module.
 *
 * Given a directory, this function finds all all subdirectories with a main.scss file. If the file exists,
 * the subdirectory name is used as a key in a new entry pointing to the main.scss file.
 */
function getThemeEntries() {
    const themeDir = process.env.THEME_DIR;
    let themeEntries = {};

    if (!themeDir) {
        console.log('THEME_DIR not defined. Skipping theme compilation.')
    }
    else {
        const themePath = path.resolve(themeDir);
        const subDirs = fs.readdirSync(themePath).filter(file => fs.statSync(path.join(themePath, file)).isDirectory());

        subDirs.forEach((directory) => {
            let mainStyle = path.join(themePath, directory, 'main.scss');

            if (!fs.existsSync(mainStyle)) {
                console.log(`${mainStyle} does not exist. No theme will be created for ${directory}!`);
            }
            else {
                themeEntries[directory] = mainStyle;
                console.log(`Added theme for ${directory} from ${mainStyle}`);
            }
        });
    }

    return themeEntries;
}

const themeEntries = getThemeEntries();
console.log(`Included theme entries: ${JSON.stringify(themeEntries, null, 4)}`);

module.exports = {
    context: __dirname,

    entry: Object.assign({
        'base.style-ltr': './credentials/static/sass/main-ltr.scss',
        'base.style-rtl': './credentials/static/sass/main-rtl.scss',
        'sharing': './credentials/static/js/sharing.js',
        'analytics': './credentials/static/js/analytics.js'
    }, themeEntries),

    output: {
        path: path.resolve('./credentials/static/bundles/'),
        filename: '[name]-[hash].js'
    },

    plugins: [
        // TODO Add commons chunk plugin to de-dup themes
        new BundleTracker({filename: './webpack-stats.json'}),
        new ExtractTextPlugin('[name]-[hash].css')
    ],

    module: {
        rules: [
            {
                test: /\.s?css$/,
                loader: ExtractTextPlugin.extract({fallbackLoader: 'style-loader', loader: loaders})
            },
            {
                test: /\.woff2?$/,
                // Inline small woff files and output them below font
                loader: 'url-loader',
                query: {
                    name: 'font/[name]-[hash].[ext]',
                    limit: 5000,
                    mimetype: 'application/font-woff'
                }
            },
            {
                test: /\.(ttf|eot|svg)$/,
                loader: 'file-loader',
                query: {
                    name: 'font/[name]-[hash].[ext]'
                }
            },
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: [{
                    loader: 'babel-loader',
                    options: {presets: ['latest']}
                }],
            }
        ]
    },
    resolve: {
        modules: ['./node_modules'],
        extensions: ['.css', '.js', '.scss']
    }
};
