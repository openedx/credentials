var BundleTracker = require('webpack-bundle-tracker'),
    ExtractTextPlugin = require('extract-text-webpack-plugin'),
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

module.exports = {
    context: __dirname,

    entry: {
        'base.style-ltr': './credentials/static/sass/main-ltr.scss',
        'base.style-rtl': './credentials/static/sass/main-rtl.scss',
        'sharing': './credentials/static/js/sharing.js',
        'analytics': './credentials/static/js/analytics.js'
    },

    output: {
        path: path.resolve('./credentials/static/bundles/'),
        filename: '[name]-[hash].js'
    },

    plugins: [
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
