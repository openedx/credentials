// Setup global namespace
window.edx = {
  facebook: {
    appId: 'test',
    href: 'http://example.com',
  },
  segment: {},
  user: {},
};

// Mock the Facebook SDK
FB = {
  AppEvents: {
    logPageView: null,
  },
  init: null,
  ui: null,
};
