const BundleTracker = require('webpack-bundle-tracker');
const path = require('path');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const webpack = require('webpack');
const HardSourceWebpackPlugin = require('hard-source-webpack-plugin');

const isDevstack = (process.env.DJANGO_SETTINGS_MODULE === 'credentials.settings.devstack');


// Conditionally add all of the plugins
function getPlugins() {
  const plugins = [];

  plugins.push(new BundleTracker({ filename: './webpack-stats.json' }));
  plugins.push(new ExtractTextPlugin('[name]-[hash].css'));
  
  // Only load this plugin in devstack since we are not sure if
  // caching could cause issues in production builds later on
  if (isDevstack) {
    plugins.push(new HardSourceWebpackPlugin());
  }

  return plugins;
}


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
        'programs': './credentials/static/components/ProgramRecordFactory.jsx',
        'masquerading': './credentials/static/components/MasqueradeBannerFactory.jsx',
    },

    output: {
        path: path.resolve('./credentials/static/bundles/'),
        filename: '[name]-[hash].js',
        libraryTarget: 'window',
    },

    plugins: getPlugins(),

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
                test: /\.(ttf|eot|svg)$/,
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

        ]
    },
    resolve: {
        modules: ['./node_modules'],
        extensions: ['.css', '.js', '.jsx', '.scss'],
    }
};
