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
}

export default StringUtils;
