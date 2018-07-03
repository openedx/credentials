import React from 'react';
import { mount } from 'enzyme';
import Cookies from 'js-cookie';
import ProgramRecord from '../ProgramRecord';
import StringUtils from '../Utils';

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
    progress: 'Partially Completed',
    type: 'MicroMasters',
    last_updated: '2018-06-29T18:15:01.805131+00:00',
  },
  grades: [
    {
      attempts: 1,
      course_id: 'Course-1',
      issue_date: '2018-06-29T18:15:01.805131+00:00',
      letter_grade: 'B',
      name: 'Course 1',
      percent_grade: 0.82,
      school: 'Test-Org-1',
    },
    {
      attempts: 1,
      course_id: 'Course-2',
      issue_date: '2018-06-29T18:15:01.808927+00:00',
      letter_grade: 'B',
      name: 'Course 2',
      percent_grade: 0.82,
      school: 'Test-Org-2',
    },
    {
      attempts: 0,
      course_id: 'course-3',
      issue_date: null,
      letter_grade: null,
      name: 'Course 3',
      percent_grade: null,
      school: 'TestX',
    },
  ],
  uuid: '1a2b3c4d',
  platform_name: 'testX',
  loadModalsAsChildren: false,
};

// eslint-disable-next-line no-useless-escape
const cookieJSON = '{\"username\": \"edx\"\\054 \"version\": 1\\054 \"header_urls\": {\"learner_profile\": \"http://localhost:18000/u/edx\"\\054 \"resume_block\": \"sample\"}}';

describe('<ProgramRecord />', () => {
  describe('User viewing own record', () => {
    beforeEach(() => {
      wrapper = mount(<ProgramRecord {...defaultProps} />);
      wrapper.setState({ isPublic: false });
    });

    it('renders correct sections', () => {
      expect(wrapper.find('.program-record').length).toEqual(1);
      expect(wrapper.find('.program-record-header').length).toEqual(1);
      expect(wrapper.find('.learner-info').length).toEqual(1);
      expect(wrapper.find('.program-record-grades').length).toEqual(1);
      expect(wrapper.find('.program-record-actions button').length).toEqual(2);
      expect(wrapper.find('.program-record-actions button.btn-primary').text()).toBe('Send Learner Record');
      expect(wrapper.find('.program-record-actions button.btn-secondary').text()).toBe('Share');
    });

    it('renders correct records', () => {
      const programRows = wrapper.find('.program-record-grades tbody tr');
      const { grades } = defaultProps;

      const firstRowData = programRows.at(0).find('td');
      expect(firstRowData.at(0).text()).toEqual(grades[0].name);
      expect(firstRowData.at(0).key()).toEqual('name');
      expect(firstRowData.at(1).text()).toEqual(grades[0].school);
      expect(firstRowData.at(2).text()).toEqual(grades[0].course_id);
      expect(firstRowData.at(3).text()).toEqual('82%');
      expect(firstRowData.at(4).text()).toEqual('B');
      expect(firstRowData.at(5).text()).toEqual('1');
      expect(firstRowData.at(6).text()).toEqual('6/29/18');
      expect(firstRowData.at(7).text()).toEqual('Earned');

      const thirdRowData = programRows.at(2).find('td');
      expect(thirdRowData.at(0).text()).toEqual(grades[2].name);
      expect(thirdRowData.at(0).key()).toEqual('name');
      expect(thirdRowData.at(1).text()).toEqual(grades[2].school);
      expect(thirdRowData.at(2).text()).toEqual('');
      expect(thirdRowData.at(3).text()).toEqual('');
      expect(thirdRowData.at(4).text()).toEqual('');
      expect(thirdRowData.at(5).text()).toEqual('');
      expect(thirdRowData.at(6).text()).toEqual('');
      expect(thirdRowData.at(7).text()).toEqual('Not Earned');
    });

    it('loads the send learner record modal', () => {
      expect(wrapper.find('.modal-dialog').length).toBe(0);
      wrapper.find('.program-record-actions button.btn-primary').simulate('click');
      wrapper.update();
      expect(wrapper.find('.modal-dialog').length).toBe(1);
    });

    it('closes the send learner record modal', () => {
      expect(wrapper.find('.modal-dialog').length).toBe(0);
      wrapper.find('.program-record-actions button.btn-primary').simulate('click');
      wrapper.update();
      expect(wrapper.find('.modal-dialog').length).toBe(1);
      wrapper.find('.modal-dialog .modal-header button').simulate('click');
      wrapper.update();
      expect(wrapper.find('.modal-dialog').length).toBe(0);
      expect(wrapper.find('.program-record-actions button.btn-primary').html()).toEqual(document.activeElement.outerHTML);
    });

    it('loads the share program url modal', () => {
      expect(wrapper.find('.modal-dialog').length).toBe(0);
      wrapper.find('.program-record-actions button.btn-secondary').simulate('click');
      wrapper.update();
      expect(wrapper.find('.modal-dialog').length).toBe(1);
    });

    it('closes the share program url modal', () => {
      expect(wrapper.find('.modal-dialog').length).toBe(0);
      wrapper.find('.program-record-actions button.btn-secondary').simulate('click');
      wrapper.update();
      expect(wrapper.find('.modal-dialog').length).toBe(1);
      wrapper.find('.modal-dialog .modal-header button').simulate('click');
      wrapper.update();
      expect(wrapper.find('.modal-dialog').length).toBe(0);
      expect(wrapper.find('.program-record-actions button.btn-secondary').html()).toEqual(document.activeElement.outerHTML);
    });

    it('correctly parses cookie JSON', () => {
      const parsed = StringUtils.parseDirtyJSON(cookieJSON);

      expect(parsed.username).toEqual('edx');
      expect(parsed.version).toBe(1);
      expect(parsed.header_urls.resume_block).toBe('sample');
    });
  });

  describe('Public view of record', () => {
    beforeEach(() => {
      Cookies.set('prod-edx-user-info', cookieJSON, { path: '' });
      wrapper = mount(<ProgramRecord {...defaultProps} />);
    });

    it('renders correct sections', () => {
      expect(wrapper.find('.program-record').length).toEqual(1);
      expect(wrapper.find('.program-record-header').length).toEqual(1);
      expect(wrapper.find('.learner-info').length).toEqual(1);
      expect(wrapper.find('.program-record-grades').length).toEqual(1);
      expect(wrapper.find('.program-record-actions button').length).toEqual(1);
      expect(wrapper.find('.program-record-actions button.btn-primary').text()).toBe('Download Record');
    });

    it('downloads record', () => {
      expect(wrapper.state('recordDownloaded')).toBe(false);
      wrapper.find('.program-record-actions button.btn-primary').simulate('click');
      wrapper.update();
      expect(wrapper.state('recordDownloaded')).toBe(true);
    });
  });
});
