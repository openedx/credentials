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
