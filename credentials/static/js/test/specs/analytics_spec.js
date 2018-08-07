describe('analytics module', () => {
  let analyticsTestButton;

  beforeEach(() => {
    jasmine.getFixtures().fixturesPath = '/base/credentials/static/js/test/fixtures';
    loadFixtures('analytics.html');
    analyticsTestButton = document.getElementById('analyticsTestBtn');
    spyOn(window.analytics, 'track');
  });

  it('should pull attributes from data attributes and call window.analytics.track', () => {
    setupClickHandlers(); // eslint-disable-line no-undef
    analyticsTestButton.click();

    const expectedProperties = {
      category: 'certificates',
    };

    expect(window.analytics.track).toHaveBeenCalledWith('edx.bi.test', expectedProperties);
  });
});
