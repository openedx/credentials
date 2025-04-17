const BundleTracker = require('webpack-bundle-tracker');
const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const webpack = require('webpack');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');

const isDevstack = (process.env.DJANGO_SETTINGS_MODULE === 'credentials.settings.devstack');
// Conditionally add all of the plugins
function getPlugins() {
  const plugins = [];
  plugins.push(new BundleTracker({ path: '.', filename: 'webpack-stats.json' }));
  plugins.push(new MiniCssExtractPlugin({ filename: '[name]-[contenthash].css' }));
  return plugins;
}
module.exports = {
  mode: 'production',
  cache: true,
  context: __dirname,
  entry: {
    'base.style-ltr': './credentials/static/sass/main-ltr.scss',
    'base.style-rtl': './credentials/static/sass/main-rtl.scss',
    'override-style': './credentials/static/sass/overrides.scss',
    'openedx.certificate.style-ltr': './credentials/apps/credentials_theme_openedx/static/sass/certificate-ltr.scss',
    'openedx.certificate.style-rtl': './credentials/apps/credentials_theme_openedx/static/sass/certificate-rtl.scss',
    sharing: './credentials/static/js/sharing.js',
    analytics: './credentials/static/js/analytics.js',
    fontawesome: './credentials/static/js/fontawesome.js',
  },
  output: {
    path: path.resolve('./credentials/static/bundles/'),
    filename: '[name]-[contenthash].js',
    libraryTarget: 'window'
  },
  plugins: getPlugins(),
  externals: {
    gettext: 'gettext',
  },
  module: {
    rules: [
      {
        test: /\.s?css$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader', 'sass-loader'],
      },
      {
        test: /\.woff2?$/,
        // Inline small woff files and output them below font
        use: [
          {
            loader: 'url-loader',
            options: {
              name: 'font/[name]-[contenthash].[ext]',
              limit: 5000,
              mimetype: 'font/woff2',
            }
          }
        ]
      },
      {
        test: /\.(ttf|eot|svg)$/,
        use: [
          {
            loader: 'file-loader',
            options: {
              name: 'font/[name]-[contenthash].[ext]'
            }
          }
        ]
      },
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: ['babel-loader']
      },
    ],
  },
  optimization: {
    minimizer: [
      new CssMinimizerPlugin(),
    ],
  },
  resolve: {
    modules: ['./node_modules'],
    extensions: ['.css', '.js', '.jsx', '.scss'],
  },
};
