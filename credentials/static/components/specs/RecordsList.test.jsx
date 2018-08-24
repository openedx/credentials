import React from 'react';
import { mount } from 'enzyme';
import RecordsList from '../RecordsList';

// Remove once xgettext supports backticks and this rule is removed
/* eslint-disable no-restricted-syntax */

let wrapper;

const defaultProps = {
  helpUrl: 'https://edx.org/help/records',
  profileUrl: 'https://example.com',
  icons: {
    micromasters: 'micromasters-icon',
    professional_certificate: 'professional-certificate-icon',
    xseries: 'xseries-icon',
  },
  title: 'Records List',
  programHelp: 'Help text for programs',
  programs: [
    {
      name: 'Program1',
      partner: 'Partner1',
      uuid: 'UUID1',
      type: 'micromasters',
      completed: true,
      empty: false,
    },
    {
      name: 'Program2',
      partner: 'Partner2',
      uuid: 'UUID2',
      type: 'professional-certificate',
      completed: true,
      empty: false,
    },
    {
      name: 'Program3',
      partner: 'Partner3',
      uuid: 'UUID3',
      type: 'xseries',
      completed: false,
      empty: false,
    },
    {
      name: 'Program4',
      partner: 'Partner4',
      uuid: 'UUID4',
      type: 'non-edx',
      completed: false,
      empty: false,
    },
    {
      name: 'Program5',
      partner: 'Partner5',
      uuid: 'UUID5',
      type: 'micromasters',
      completed: false,
      empty: true,
    },
  ],
};

const testRowData = (row, index) => {
  expect(row.find('.program-title').text()).toEqual(defaultProps.programs[index].name);
  expect(row.find('span').at(1).text()).toEqual(defaultProps.programs[index].partner);
  if (defaultProps.programs[index].empty) {
    expect(row.find('span').length).toEqual(1); // nothing after partner
  } else {
    expect(row.find('span').at(3).text()).toEqual(defaultProps.programs[index].completed ?
      'Completed' : 'Partially Complete');
  }
};

describe('<RecordsList />', () => {
  it('has empty state message', () => {
    wrapper = mount(<RecordsList />);

    expect(wrapper.find('.record p').text()).toContain('No records yet');
    expect(wrapper.find('.card-list').exists()).toEqual(false);
  });

  it('does not show faq footer if link is not provided', () => {
    wrapper = mount(<RecordsList />);
    expect(wrapper.find('.faq').length).toBe(0);
  });

  it('shows custom header strings', () => {
    wrapper = mount(<RecordsList {...defaultProps} />);
    expect(wrapper.find('#main-content > header').text()).toEqual('Records List');
    expect(wrapper.find('#program-records-list > header p').text()).toEqual('Help text for programs');
  });

  it('lists programs', () => {
    wrapper = mount(<RecordsList {...defaultProps} />);
    const programRows = wrapper.find('.record-card');

    testRowData(programRows.at(0).find('.record-data-col'), 0);
    testRowData(programRows.at(1).find('.record-data-col'), 1);
  });

  it('links to program records', () => {
    wrapper = mount(<RecordsList {...defaultProps} />);
    const programRows = wrapper.find('.record-card');

    const firstProgramLink = programRows.at(0).find('.record-btn-col').find('a');
    expect(firstProgramLink.prop('href')).toContain(`/${defaultProps.programs[0].uuid}`);

    const secondProgramLink = programRows.at(1).find('.record-btn-col').find('a');
    expect(secondProgramLink.prop('href')).toContain(`/${defaultProps.programs[1].uuid}`);

    const thirdProgramLink = programRows.at(2).find('.record-btn-col').find('a');
    expect(thirdProgramLink.prop('href')).toContain(`/${defaultProps.programs[2].uuid}`);

    // Check text of button
    expect(programRows.at(3).find('.record-btn-col').text()).toEqual('View Program Record');
    expect(programRows.at(4).find('.record-btn-col').text()).toEqual('View Example');
  });

  it('no icon for programs with non-edx certificate type', () => {
    wrapper = mount(<RecordsList {...defaultProps} />);

    expect(wrapper.find('.record-card').at(3).contains('certificate-icon')).toBe(false);
  });

  it('links to records help url', () => {
    wrapper = mount(<RecordsList {...defaultProps} />);
    expect(wrapper.find('.faq span').html()).toContain(`href="${defaultProps.helpUrl}"`);
  });
});
