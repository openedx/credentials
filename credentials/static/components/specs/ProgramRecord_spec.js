/* globals setFixtures */

import React from 'react';
import ReactDOM from 'react-dom';
import ProgramRecord from '../ProgramRecord';

describe('program record', () => {
  beforeEach(() => {
    setFixtures('<div id="wrapper"></div>');
  });

  function init(record) {
    ReactDOM.render(
      React.createElement(ProgramRecord, {
        record,
      }, null),
      document.getElementById('wrapper'),
    );
  }

  function programData() {
    return {
      learner: {
        full_name: 'Firsty Lasty',
        username: 'edxIsGood',
        email: 'edx@example.com',
      },
      program: {
        name: 'Test Program',
        school: 'TestX',
      },
      grades: [
        {
          name: 'Course 1',
          school: 'TestX',
          attempts: 1,
          course_id: 'course1x',
          start: '2018-01-01',
          end: '2018-02-01',
          percent_grade: '98%',
          letter_grade: 'A',
        },
        {
          name: 'Course 2',
          school: 'TestX',
          attempts: 1,
          course_id: 'course2x',
          start: '2018-01-01',
          end: '2018-02-01',
          percent_grade: '98%',
          letter_grade: 'A',
        },
      ],
    };
  }

  function find(selector) {
    return document.querySelector(selector);
  }

  it('lists grades in a table', () => {
    init(programData());

    expect(find('#program-record tbody tr:nth-child(1)')).toContainText('Course 1');
    expect(find('#program-record tbody tr:nth-child(2)')).toContainText('Course 2');
  });
});
