import React from 'react';
import { mount } from 'enzyme';
import RecordsList from '../RecordsList';

let wrapper;

const defaultProps = {
  helpUrl: 'https://edx.org/help/records',
  programs: [
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
  ],
};

const testRowData = (row, index) => {
  expect(row.at(0).text()).toEqual(`Program${index}`);
  expect(row.at(0).key()).toEqual('name');
  expect(row.at(1).text()).toEqual(`Partner${index}`);
  expect(row.at(1).key()).toEqual('partner');
};

describe('<RecordsList />', () => {
  it('has empty state message', () => {
    wrapper = mount(<RecordsList />);

    expect(wrapper.find('.record p').text()).toContain('No records yet');
    expect(wrapper.find('table').exists()).toEqual(false);
  });

  it('does not show faq footer if link is not provided', () => {
    wrapper = mount(<RecordsList />);
    expect(wrapper.find('.faq').length).toBe(0);
  });

  it('lists programs', () => {
    wrapper = mount(<RecordsList {...defaultProps} />);
    const programRows = wrapper.find('#program-records .table-responsive tbody tr');

    testRowData(programRows.at(0).find('td'), 1);
    testRowData(programRows.at(1).find('td'), 2);
  });

  it('links to program records', () => {
    wrapper = mount(<RecordsList {...defaultProps} />);
    const programRows = wrapper.find('#program-records .table-responsive tbody tr');

    const firstProgramLink = programRows.at(0).find('td').at(2).find('a');
    expect(firstProgramLink.prop('href')).toContain('/UUID1');

    const secondProgramLink = programRows.at(1).find('td').at(2).find('a');
    expect(secondProgramLink.prop('href')).toContain('/UUID2');
  });

  it('links to records help url', () => {
    wrapper = mount(<RecordsList {...defaultProps} />);
    expect(wrapper.find('.faq span').html()).toContain(`href="${defaultProps.helpUrl}"`);
  });
});
