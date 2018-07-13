import React from 'react';
import PropTypes from 'prop-types';

import MicroMastersIcon from '../images/icons/micromasters.svg';
import XseriesIcon from '../images/icons/xseries.svg';
import ProfessionalIcon from '../images/icons/professional.svg';

const ProgramIcon = (props) => {
  const { className, element, type } = props;

  let icon = false;

  if (type === 'micromasters') {
    icon = MicroMastersIcon;
  } else if (type === 'xseries') {
    icon = XseriesIcon;
  } else if (type === 'professional-certificate') {
    icon = ProfessionalIcon;
  }

  if (icon) {
    const html = { __html: icon };
    return React.createElement(element, {
      'aria-hidden': true,
      className,
      dangerouslySetInnerHTML: html,
    });
  }

  return null;
};

ProgramIcon.propTypes = {
  className: PropTypes.string,
  element: PropTypes.string,
  type: PropTypes.string.isRequired,
};

ProgramIcon.defaultProps = {
  className: '',
  element: 'span',
};

export default ProgramIcon;
