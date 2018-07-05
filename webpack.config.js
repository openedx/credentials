const BundleTracker = require('webpack-bundle-tracker');
const path = require('path');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const webpack = require('webpack');

module.exports = {
    cache: true,

    context: __dirname,

    entry: {
        'base.style-ltr': './credentials/static/sass/main-ltr.scss',
        'base.style-rtl': './credentials/static/sass/main-rtl.scss',
        'openedx.certificate.style-ltr': './credentials/apps/credentials_theme_openedx/static/sass/certificate-ltr.scss',
        'openedx.certificate.style-rtl': './credentials/apps/credentials_theme_openedx/static/sass/certificate-rtl.scss',
        'sharing': './credentials/static/js/sharing.js',
        'analytics': './credentials/static/js/analytics.js',
        'records': './credentials/static/components/RecordsFactory.jsx',
        'programs': './credentials/static/components/ProgramRecordFactory.jsx'
    },

    output: {
        path: path.resolve('./credentials/static/bundles/'),
        filename: '[name]-[hash].js',
        libraryTarget: 'window',
    },

    plugins: [
        new BundleTracker({filename: './webpack-stats.json'}),
        new ExtractTextPlugin('[name]-[hash].css')
    ],

    externals: {
      gettext: 'gettext',
    },

    module: {
        rules: [
            {
                test: /\.s?css$/,
                use: ExtractTextPlugin.extract({
                    use: [
                        {
                            loader: 'css-loader',
                            options: {
                                minimize: true
                            }
                        },
                        {
                            loader: 'sass-loader'
                        }
                    ]
                })
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
                test: /\.(ttf|eot)$/,
                loader: 'file-loader',
                query: {
                    name: 'font/[name]-[hash].[ext]'
                }
            },
            {
                test: /\.(js|jsx)$/,
                exclude: /node_modules/,
                loader: 'babel-loader',
            },
            {
                test: /\.svg$/,
                oneOf: [

                    {
                        exclude: path.resolve('./credentials/static/bundles/fonts/'),
                        use: 'file-loader'
                    },
                    {
                        include: path.resolve('./credentials/static/images/'),
                        use: 'svg-inline-loader'
                    }
                ]
            }
        ]
    },
    resolve: {
        modules: ['./node_modules'],
        extensions: ['.css', '.js', '.jsx', '.scss'],
    }
};
