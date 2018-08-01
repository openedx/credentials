import React from 'react';

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

  // This is mostly safe, as i18n_tool will scan for xss attacks in translations
  static renderDangerousHtml(formatString, parameters) {
    let htmlString;

    if (typeof parameters === 'undefined') {
      htmlString = formatString;
    } else {
      htmlString = StringUtils.interpolate(formatString, parameters);
    }

    return (
      /* eslint-disable react/no-danger */
      <span dangerouslySetInnerHTML={{ __html: htmlString }} />
    );
  }

  // Make a human readable string of string items concatenated with ','s and 'and'
  // e.g. 'first, second, third, and last' or 'first and second'
  static formatStringList(items) {
    const length = items.length;

    switch (length) {
      case 0:
        return '';
      case 1:
        return items[0];
      case 2:
        return StringUtils.interpolate(gettext('{first} and {second}'), { first: items[0], second: items[1] });
      default: {
        const firstItems = items.slice(0, length - 1).join(', ');
        return StringUtils.interpolate(gettext('{firstItems}, and {lastItem}'), { firstItems, lastItem: items[length - 1] });
      }
    }
  }

}


export default StringUtils;
