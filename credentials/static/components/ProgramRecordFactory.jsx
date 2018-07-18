import React from 'react';
import ReactDOM from 'react-dom';

import ProgramRecord from './ProgramRecord';

function ProgramRecordFactory(parent, props) {
  const formattedProps = {
    ...props.record,
    isPublic: props.isPublic,
    icons: props.icons,
    uuid: props.uuid,
    helpUrl: props.helpUrl,
  };

  ReactDOM.render(
    React.createElement(ProgramRecord, { ...formattedProps }, null),
    document.getElementById(parent),
  );
}

export { ProgramRecordFactory }; // eslint-disable-line import/prefer-default-export
