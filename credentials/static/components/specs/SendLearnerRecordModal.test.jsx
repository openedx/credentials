import React from 'react';
import { mount } from 'enzyme';
import SendLearnerRecordModal from '../SendLearnerRecordModal';

let wrapper;

const defaultProps = {
  parentSelector: 'body',
  uuid: 'test-uuid',
  sendHandler: jest.fn(),
  creditPathways: {
    testX: {
      sent: false,
      checked: false,
      id: 1,
      isActive: true,
    },
    MITx: {
      sent: true,
      checked: false,
      id: 2,
      isActive: true,
    },
    HarvardX: {
      sent: false,
      checked: false,
      id: 3,
      isActive: false,
    },
  },
  creditPathwaysList: [
    {
      name: 'testX',
      status: '',
    },
    {
      name: 'MITx',
      status: 'sent',
    },
    { name: 'HarvardX',
      status: '',
    },
  ],
  typeName: 'MicroMasters',
  platformName: 'partnerX',
};

describe('<SendLearnerRecordModal />', () => {
  beforeEach(() => {
    wrapper = mount(<SendLearnerRecordModal {...defaultProps} />);
  });

  it('displays the program record url if API returns successfully', () => {
    expect(wrapper.find('.modal-dialog').length).toBe(1);
    expect(wrapper.find('.modal-header .modal-title').text()).toBe('Send to partnerX Credit Partner');
    expect(wrapper.find('.modal-header button').length).toBe(1);
    expect(wrapper.find('.modal-footer button').length).toBe(2);
  });

  it('closes if the header close button is clicked', () => {
    expect(wrapper.find('.modal-dialog').length).toBe(1);
    wrapper.find('.modal-header button').simulate('click');
    expect(wrapper.find('.modal-dialog').length).toBe(0);
  });

  it('closes if the footer close button is clicked', () => {
    expect(wrapper.find('.modal-dialog').length).toBe(1);
    wrapper.find('.modal-footer button.btn.btn-link').simulate('click');
    expect(wrapper.find('.modal-dialog').length).toBe(0);
  });

  it('calls sendHandler if selected', () => {
    wrapper.find('.modal-body input').at(0).simulate('change');
    const pathways = wrapper.state().creditPathways;
    pathways.testX.checked = true;
    const numCheckedOrganizations = 1;
    wrapper.instance().setState({ pathways, numCheckedOrganizations });
    wrapper.find('.modal-footer button.btn-primary').simulate('click');
    wrapper.update();
    expect(defaultProps.sendHandler.mock.calls.length).toBe(1);
  });

  it('gets the correct checked organizations', () => {
    wrapper.state().creditPathways.testX.checked = true;
    expect(wrapper.instance().getCheckedOrganizations()).toEqual(['testX']);
  });

  it('enables send button when at least one organization is checked', () => {
    expect(wrapper.find('.modal-footer button.btn-primary').prop('disabled')).toBe(true);
    wrapper.find('.modal-body input').at(0).simulate('change');
    expect(wrapper.find('.modal-footer button.btn-primary').prop('disabled')).toBe(false);
  });

  it('gets the correct organization display names', () => {
    expect(wrapper.instance().getPathwayDisplayName('testX')).toEqual('testX');
    expect(wrapper.instance().getPathwayDisplayName('MITx')).toEqual('MITx - Sent');
    expect(wrapper.instance().getPathwayDisplayName('HarvardX')).toEqual('HarvardX - Not Yet Available');
  });

  it('correctly determines inactive pathways', () => {
    expect(wrapper.instance().checkAnyInactivePathways()).toBe(true);
    wrapper.state().creditPathways.testX.isActive = true;
    wrapper.state().creditPathways.HarvardX.isActive = true;
    expect(wrapper.instance().checkAnyInactivePathways()).toBe(false);
  });
});
