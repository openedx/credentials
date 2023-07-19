module.exports = {
  "plugins": [
    "@babel/plugin-transform-object-assign",
    "@babel/plugin-proposal-object-rest-spread",
    [
      "@babel/plugin-transform-modules-commonjs",
      {
        "allowTopLevelThis": true
      }
    ]
  ],
  "presets": [
    [
      "@babel/preset-env",
      {
        "targets": {
          "browsers": [
            "last 2 versions",
            "IE >= 11"
          ]
        }
      }
    ],
    "@babel/preset-react"
  ]
}