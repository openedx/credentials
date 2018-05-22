class StringUtils {

  static interpolate(formatString, parameters) {
    return formatString.replace(/{\w+}/g, (parameter) => {
      const parameterName = parameter.slice(1, -1);
      return String(parameters[parameterName]);
    });
  }

}

export default StringUtils;
