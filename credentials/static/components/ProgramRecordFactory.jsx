import React from 'react';
import ReactDOM from 'react-dom';

import ProgramRecord from './ProgramRecord';

function ProgramRecordFactory(parent, props) {
  ReactDOM.render(
    React.createElement(ProgramRecord, props, null),
    document.getElementById(parent),
  );
}

export { ProgramRecordFactory }; // eslint-disable-line import/prefer-default-export
