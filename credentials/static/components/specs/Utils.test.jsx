import StringUtils from '../Utils';

describe('String Utils formatStringList()', () => {
  it('correctly processes 0 items', () => {
    const items = [];
    const result = StringUtils.formatStringList(items);

    expect(result).toEqual('');
  });

  it('correctly processes 1 item', () => {
    const items = ['first'];
    const result = StringUtils.formatStringList(items);

    expect(result).toEqual('first');
  });
});
