import React from 'react';
import { mount } from 'enzyme';
import ProgramRecord from '../ProgramRecord';

let wrapper;

const defaultProps = {
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
  uuid: '1a2b3c4d',
  platform_name: 'testX',
};

describe('<ProgramRecord />', () => {
  it('renders correct sections', () => {
    wrapper = mount(<ProgramRecord {...defaultProps} />);

    expect(wrapper.find('.program-record').length).toEqual(1);
    expect(wrapper.find('#program-record-title-bar').length).toEqual(1);
    expect(wrapper.find('#learner-info').length).toEqual(1);
    expect(wrapper.find('#program-record').length).toEqual(1);
  });

  it('renders correct records', () => {
    wrapper = mount(<ProgramRecord {...defaultProps} />);
    const programRows = wrapper.find('#program-record .table-responsive tbody tr');

    const firstRowData = programRows.at(0).find('td');
    expect(firstRowData.at(0).text()).toEqual('Course 1');
    expect(firstRowData.at(0).key()).toEqual('name');

    const secondRowData = programRows.at(1).find('td');
    expect(secondRowData.at(0).text()).toEqual('Course 2');
    expect(secondRowData.at(0).key()).toEqual('name');
  });
});
