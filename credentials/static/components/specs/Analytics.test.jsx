import trackEvent from '../Analytics';


let mockAnalytics;

describe('Track Event', () => {
  beforeEach(() => {
    mockAnalytics = jest.fn();
  });

  it('calls window analytics function if it exists', () => {
    window.analytics = { track: mockAnalytics };
    const eventName = 'testEvent';
    const eventProperties = { category: 'test' };
    trackEvent(eventName, eventProperties);

    expect(mockAnalytics.mock.calls.length).toBe(1);
    expect(mockAnalytics.mock.calls[0][0]).toBe(eventName);
    expect(mockAnalytics.mock.calls[0][1]).toBe(eventProperties);
  });
});
