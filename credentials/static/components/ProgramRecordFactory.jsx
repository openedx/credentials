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

  // TODO: Update the backend to provide the data
  formattedProps.program.progress = 'Partially Completed';
  formattedProps.program.type = 'MicroMasters';
  formattedProps.program.last_updated = '2018-06-29T18:15:01.805131+00:00';

  // Update sample data to include incomplete course
  formattedProps.grades.push({
    attempts: 0,
    course_id: 'course6x',
    issue_date: null,
    letter_grade: null,
    name: 'Course 6',
    percent_grade: null,
    school: 'TestX',
  });

  ReactDOM.render(
    React.createElement(ProgramRecord, { ...formattedProps }, null),
    document.getElementById(parent),
  );
}

export { ProgramRecordFactory }; // eslint-disable-line import/prefer-default-export
