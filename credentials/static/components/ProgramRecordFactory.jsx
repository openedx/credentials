import React from 'react';
import ReactDOM from 'react-dom';

import ProgramRecord from './ProgramRecord';

function getUUID() {
  const url = window.location.pathname;
  const urlPrefix = 'records/programs/';
  let uuid = url.substring(url.indexOf(urlPrefix) + urlPrefix.length);

  const queryIndex = uuid.indexOf('?');
  if (queryIndex > -1) {
    uuid = uuid.substring(0, queryIndex);
  }

  // Remove any trailing slashes
  return uuid.replace(/\//g, '');
}

function ProgramRecordFactory(parent, props) {
  const formattedProps = {
    ...props.record,
    isPublic: props.isPublic,
    uuid: getUUID(),
  };

  ReactDOM.render(
    React.createElement(ProgramRecord, { ...formattedProps }, null),
    document.getElementById(parent),
  );
}

export { ProgramRecordFactory }; // eslint-disable-line import/prefer-default-export
