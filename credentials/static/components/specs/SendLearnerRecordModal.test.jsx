import React from 'react';
import { mount } from 'enzyme';
import SendLearnerRecordModal from '../SendLearnerRecordModal';

let wrapper;

const defaultProps = {
  parentSelector: 'body',
  uuid: 'test-uuid',
};

describe('<SendLearnerRecordModal />', () => {
  beforeEach(() => {
    wrapper = mount(<SendLearnerRecordModal {...defaultProps} />);
  });

  it('displays the program record url if API returns successfully', () => {
    expect(wrapper.find('.modal-dialog').length).toBe(1);
    expect(wrapper.find('.modal-header .modal-title').text()).toBe('Send to edX Credit Partner');
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
    wrapper.find('.modal-footer button.btn-secondary').simulate('click');
    expect(wrapper.find('.modal-dialog').length).toBe(0);
  });

  it('sends a record if selected', () => {
    wrapper.find('.modal-body input').at(0).simulate('change', { target: { checked: true } });
    expect(wrapper.state('RIT')).toBe(true);
    wrapper.find('.modal-footer button.btn-primary').simulate('click');
    wrapper.update();
    expect(wrapper.state('recordSent')).toBe(true);
  });

  it('gets the correct checked organizations', () => {
    wrapper.find('.modal-body input').at(0).simulate('change', { target: { checked: true } });
    expect(wrapper.state('RIT')).toBe(true);
    expect(wrapper.instance().getCheckedOrganizations()).toEqual(['RIT']);
  });
});
