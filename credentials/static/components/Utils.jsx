import React from 'react';

class StringUtils {

  static interpolate(formatString, parameters) {
    return formatString.replace(/{\w+}/g, (parameter) => {
      const parameterName = parameter.slice(1, -1);
      return String(parameters[parameterName]);
    });
  }

  // FIXME: Make sure that HTML is sanitized for XSS first
  // Reference: https://openedx.atlassian.net/browse/LEARNER-5537
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
}

export default StringUtils;
