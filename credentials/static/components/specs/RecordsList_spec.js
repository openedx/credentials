/* globals setFixtures */

import React from 'react';
import ReactDOM from 'react-dom';
import RecordsList from '../RecordsList';

describe('records list', () => {
  beforeEach(() => {
    setFixtures('<div id="wrapper"></div>');
  });

  function init(programs) {
    ReactDOM.render(
      React.createElement(RecordsList, {
        programs,
      }, null),
      document.getElementById('wrapper'),
    );
  }

  function programData() {
    return [
      {
        name: 'Program1',
        partner: 'Partner1',
        uuid: 'UUID1',
      },
      {
        name: 'Program2',
        partner: 'Partner2',
        uuid: 'UUID2',
      },
    ];
  }

  function find(selector) {
    return document.querySelector(selector);
  }

  it('has empty state message', () => {
    init([]);

    expect(find('#wrapper')).toContainText('No records yet');
    expect(find('#wrapper table')).not.toExist();
  });

  it('lists programs', () => {
    init(programData());

    expect(find('#program-records tbody tr:nth-child(1)')).toContainText('Program1');
    expect(find('#program-records tbody tr:nth-child(1)')).toContainText('Partner1');
    expect(find('#program-records tbody tr:nth-child(2)')).toContainText('Program2');
    expect(find('#program-records tbody tr:nth-child(2)')).toContainText('Partner2');
  });

  it('links to program records', () => {
    init(programData());

    const firstButton = find('#program-records tbody tr:nth-child(1) button');
    const secondButton = find('#program-records tbody tr:nth-child(2) button');

    expect(firstButton.parentElement.getAttribute('href')).toContain('/UUID1');
    expect(secondButton.parentElement.getAttribute('href')).toContain('/UUID2');
  });
});
