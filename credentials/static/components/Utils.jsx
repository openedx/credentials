class StringUtils {
  // Make a human readable string of string items concatenated with ','s and 'and'
  // e.g. 'first, second, third, and last' or 'first and second'
  static formatStringList(items) {
    const { length } = items;

    switch (length) {
      case 0:
        return '';
      default:
        return items[0];
    }
  }
}

export default StringUtils;
