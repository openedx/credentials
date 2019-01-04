import React from 'react';
import PropTypes from 'prop-types';
import StringUtils from './Utils';

const RecordsHelp = (props) => {
  const { helpUrl } = props;

  return (
    <footer className="faq pad-text-block">
      <h1 className="h5 text-black">{gettext('Questions about Learner Records?')}</h1>
      {StringUtils.renderDangerousHtml(
        gettext('To learn more about records you can {start_anchor}read more in our records help area.{end_anchor}'),
        { start_anchor: '<a href=' + helpUrl + '>', end_anchor: '</a>' },
      )}
    </footer>
  );
};

RecordsHelp.propTypes = {
  helpUrl: PropTypes.string.isRequired,
};

export default RecordsHelp;
