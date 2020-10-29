describe('sharing module', () => {
  let facebookShareButton;
  const facebookAppId = window.edx.facebook.appId;
  const facebookHref = window.edx.facebook.href;

  beforeEach(() => {
    jasmine.getFixtures().fixturesPath = '/base/credentials/static/js/test/fixtures';
    loadFixtures('sharing.html'); // eslint-disable-line no-undef
    facebookShareButton = document.querySelector('.action-facebook');
    window.edx.facebook = {
      appId: facebookAppId,
      href: facebookHref,
    };

    spyOn(FB, 'init');
    spyOn(FB, 'ui');
    spyOn(FB.AppEvents, 'logPageView');

    initializeFacebook(); // eslint-disable-line no-undef
  });

  describe('initializeFacebook', () => {
    it('should initialize the Facebook SDK', () => {
      const expected = {
        appId: facebookAppId,
        xfbml: true,
        version: 'v2.8',
      };

      expect(FB.init).toHaveBeenCalledWith(expected);
    });

    it('should log a page view', () => {
      expect(FB.AppEvents.logPageView).toHaveBeenCalled();
    });

    it('should update the share button', () => {
      const expected = {
        method: 'share',
        href: window.edx.facebook.href,
      };

      expect(facebookShareButton.getAttribute('disabled')).toBeFalsy();

      facebookShareButton.click();

      expect(FB.ui).toHaveBeenCalledWith(expected);
    });

    it('should handle the share button not existing', () => {
      facebookShareButton.remove();
      initializeFacebook(); // eslint-disable-line no-undef
    });
  });
});
