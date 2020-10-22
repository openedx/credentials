import React from 'react';
import axios from 'axios';
import { mount } from 'enzyme';
import ProgramRecord from '../ProgramRecord';

let wrapper;
jest.mock('axios');

const defaultProps = {
  learner: {
    full_name: 'Firsty Lasty',
    username: 'edxIsGood',
    email: 'edx@example.com',
  },
  program: {
    name: 'Test Program',
    school: 'TestX',
    completed: false,
    empty: false,
    type: 'micromasters',
    type_name: 'MicroMasters',
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
  pathways: [
    {
      name: 'testX',
      id: 1,
      status: '',
      pathway_type: 'credit',
    },
    {
      name: 'MITx',
      id: 2,
      status: 'sent',
      pathway_type: 'credit',
    },
    {
      name: 'Dunder MifflinX',
      id: 3,
      status: '',
      pathway_type: 'industry',
    },
  ],
  isPublic: false,
  icons: {
    micromasters: 'micromasters-icon',
    professional_certificate: 'professional-certificate-icon',
    xseries: 'xseries-icon',
  },
  uuid: '1a2b3c4d',
  platform_name: 'testX',
  loadModalsAsChildren: false,
};


describe('<ProgramRecord />', () => {
  describe('User viewing own record', () => {
    beforeEach(() => {
      wrapper = mount(<ProgramRecord {...defaultProps} />);
    });

    it('renders correct sections', () => {
      expect(wrapper.find('.program-record').length).toEqual(1);
      expect(wrapper.find('.program-record-header').length).toEqual(1);
      expect(wrapper.find('.learner-info').length).toEqual(1);
      expect(wrapper.find('.program-record-grades').length).toEqual(1);
      expect(wrapper.find('.program-record-actions button').length).toEqual(2);
      expect(wrapper.find('.program-record-actions button.btn-primary').text()).toBe('Send Learner Record');
      expect(wrapper.find('.program-record-actions button.btn-outline-primary').text()).toBe('Share');
      expect(wrapper.find('.program-status .badge').text()).toBe('Partially Completed');
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

    it('filters out non-credit pathways', () => {
      const expectedCreditPathways = {
        MITx: {
          checked: true,
          id: 2,
          isActive: undefined,
          sent: true,
        },
        testX: {
          checked: false,
          id: 1,
          isActive: undefined,
          sent: false,
        },
      };
      expect(wrapper.instance().parseCreditPathways()).toEqual(expectedCreditPathways);
    });

    it('loads the send learner record modal', () => {
      expect(wrapper.find('.modal-dialog').length).toBe(0);
      wrapper.find('.program-record-actions button.btn.btn-primary').simulate('click');
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
    });

    it('loads the share program url modal', () => {
      const promise = Promise.resolve({ uuid: '21366aa129514333a4a9f32161ad3a69' });
      axios.post.mockImplementation(() => promise);

      expect(wrapper.find('.modal-dialog').length).toBe(0);
      wrapper.find('.program-record-actions button.btn-outline-primary').simulate('click');
      wrapper.update();
      expect(wrapper.find('.modal-dialog').length).toBe(1);
    });

    it('closes the share program url modal', () => {
      expect(wrapper.find('.modal-dialog').length).toBe(0);
      wrapper.find('.program-record-actions button.btn-outline-primary').simulate('click');
      wrapper.update();
      expect(wrapper.find('.modal-dialog').length).toBe(1);
      wrapper.find('.modal-dialog .modal-header button').simulate('click');
      wrapper.update();
      expect(wrapper.find('.modal-dialog').length).toBe(0);
    });

    it('switches from share to send', () => {
      expect(wrapper.find('.modal-dialog').length).toBe(0);
      wrapper.find('.program-record-actions button.btn-outline-primary').simulate('click');
      wrapper.update();
      expect(wrapper.find('.modal-dialog').length).toBe(1);
      wrapper.find('.modal-dialog .switch-to-send').simulate('click');
      wrapper.update();
      expect(wrapper.find('.modal-dialog').length).toBe(1);
      expect(wrapper.find('.modal-dialog .modal-header .modal-title').text()).toEqual('Send to testX Credit Partner');
    });

    it('shows the info alert', () => {
      expect(wrapper.find('.alert-info').prop('hidden')).toBe(true);
      wrapper.setState({ sendRecordLoadingAlertOpen: true });
      wrapper.update();
      expect(wrapper.find('.alert-info').prop('hidden')).toBe(false);
    });

    it('shows the success alert', () => {
      expect(wrapper.find('.alert-success').prop('hidden')).toBe(true);
      wrapper.setState({ sendRecordSuccessOrgs: ['RIT'], sendRecordSuccessAlertOpen: true });
      wrapper.update();
      expect(wrapper.find('.alert-success').prop('hidden')).toBe(false);
    });

    it('shows the failure alert', () => {
      expect(wrapper.find('.alert-danger').prop('hidden')).toBe(true);
      wrapper.setState({ sendRecordFailureOrgs: ['RIT'], sendRecordFailureAlertOpen: true });
      wrapper.update();
      expect(wrapper.find('.alert-danger').prop('hidden')).toBe(false);
    });

    it('closes the info alert', () => {
      expect(wrapper.find('.alert-info').prop('hidden')).toBe(true);
      wrapper.setState({ sendRecordLoadingAlertOpen: true });
      wrapper.update();
      expect(wrapper.find('.alert-info').prop('hidden')).toBe(false);
      wrapper.find('.alert-info .close').simulate('click');
      expect(wrapper.find('.alert-info').prop('hidden')).toBe(true);
    });

    it('closes the success alert', () => {
      expect(wrapper.find('.alert-success').prop('hidden')).toBe(true);
      wrapper.setState({ sendRecordSuccessOrgs: ['RIT'], sendRecordSuccessAlertOpen: true });
      wrapper.update();
      expect(wrapper.find('.alert-success').prop('hidden')).toBe(false);
      wrapper.find('.alert-success .close').simulate('click');
      expect(wrapper.find('.alert-success').prop('hidden')).toBe(true);
    });

    it('closes the failure alert', () => {
      expect(wrapper.find('.alert-danger').prop('hidden')).toBe(true);
      wrapper.setState({ sendRecordFailureOrgs: ['RIT'], sendRecordFailureAlertOpen: true });
      wrapper.update();
      expect(wrapper.find('.alert-danger').prop('hidden')).toBe(false);
      wrapper.find('.alert-danger .close').simulate('click');
      expect(wrapper.find('.alert-danger').prop('hidden')).toBe(true);
    });

    it('correctly categorizes send request success', () => {
      const postPromise = Promise.resolve({ status: 200 });
      axios.post.mockImplementation(() => postPromise);
      const allPromise = Promise.resolve();
      axios.all.mockImplementation(() => allPromise);

      wrapper.instance().sendRecords(['testX', 'MITx']);

      return allPromise.then(() => {
        wrapper.update();
        expect(wrapper.state('sendRecordSuccessAlertOpen')).toBe(true);
        expect(wrapper.state('sendRecordSuccessOrgs')).toEqual(['testX', 'MITx']);
      });
    });

    it('correctly categorizes send request failure', () => {
      const postPromise = Promise.resolve({ status: 400, response: { message: 'error' } });
      axios.post.mockImplementation(() => postPromise);
      const allPromise = Promise.resolve();
      axios.all.mockImplementation(() => allPromise);

      wrapper.instance().sendRecords(['testX', 'MITx']);

      return allPromise.then(() => {
        wrapper.update();
        expect(wrapper.state('sendRecordFailureAlertOpen')).toBe(true);
        expect(wrapper.state('sendRecordFailureOrgs')).toEqual(['testX', 'MITx']);
      });
    });
  });

  describe('Completed record', () => {
    beforeEach(() => {
      const completedProps = JSON.parse(JSON.stringify(defaultProps));
      completedProps.program.completed = true;
      wrapper = mount(<ProgramRecord {...completedProps} />);
    });

    it('labeled correctly', () => {
      expect(wrapper.find('.program-status .badge').text()).toBe('Completed');
    });
  });

  describe('Empty record', () => {
    beforeEach(() => {
      const completedProps = JSON.parse(JSON.stringify(defaultProps));
      completedProps.program.empty = true;
      wrapper = mount(<ProgramRecord {...completedProps} />);
    });

    it('labeled correctly', () => {
      expect(wrapper.find('.program-status .badge').text()).toBe('Not Earned');
    });
  });

  describe('Public view of record', () => {
    beforeEach(() => {
      wrapper = mount(<ProgramRecord {...defaultProps} isPublic />);
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
