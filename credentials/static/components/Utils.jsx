class StringUtils {
  static interpolate(formatString, parameters) {
    return formatString.replace(/{\w+}/g, (parameter) => {
      const parameterName = parameter.slice(1, -1);
      if (parameterName in parameters) {
        return String(parameters[parameterName]);
      }
      return '{' + parameterName + '}';
    });
  }

  // Make a human readable string of string items concatenated with ','s and 'and'
  // e.g. 'first, second, third, and last' or 'first and second'
  static formatStringList(items) {
    const { length } = items;

    switch (length) {
      case 0:
        return '';
      case 1:
        return items[0];
      default: {
        const firstItems = items.slice(0, length - 1).join(', ');
        return StringUtils.interpolate(gettext('{firstItems}, and {lastItem}'), { firstItems, lastItem: items[length - 1] });
      }
    }
  }
}

export default StringUtils;
