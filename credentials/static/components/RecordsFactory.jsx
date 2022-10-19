// TODO: We should be able to remove this as part of https://github.com/openedx/credentials/issues/1722
import React from 'react';
import ReactDOM from 'react-dom';

import RecordsList from './RecordsList';

function RecordsFactory(parent, props) {
  ReactDOM.render(
    React.createElement(RecordsList, props, null),
    document.getElementById(parent),
  );
}

export { RecordsFactory }; // eslint-disable-line import/prefer-default-export
