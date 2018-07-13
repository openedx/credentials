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

  it('correctly processes 2 items', () => {
    const items = ['first', 'second'];
    const result = StringUtils.formatStringList(items);

    expect(result).toEqual('first and second');
  });

  it('correctly processes 3 items', () => {
    const items = ['first', 'second', 'third'];
    const result = StringUtils.formatStringList(items);

    expect(result).toEqual('first, second, and third');
  });
});
