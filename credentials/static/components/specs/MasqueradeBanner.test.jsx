import React from 'react';
import axios from 'axios';
import { mount } from 'enzyme';
import MasqueradeBanner from '../MasqueradeBanner';

let wrapper;
jest.mock('axios');
delete window.location;
window.location = { reload: jest.fn() };
const defaultProps = {
  masquerading: true,
  user: 'test-user',
};


describe('<MasqueradeBanner />', () => {
  describe('Masquerader viewing masquerade banner', () => {
    beforeEach(() => {
      wrapper = mount(<MasqueradeBanner {...defaultProps} />);
    });

    it('renders correct sections', () => {
      expect(wrapper.find('.masquerade-form').length).toEqual(1);
      expect(wrapper.find('.masquerade-select').length).toEqual(1);
      expect(wrapper.find('.masquerade-select').props().value).toEqual('Specific Learner');
      expect(wrapper.find('.masquerade-input').length).toEqual(0);
      expect(wrapper.find('.masquerade-info-text').length).toEqual(1);
      expect(wrapper.find('.masquerade-info-text').text()).toBe('You are currently viewing as: test-user');
      expect(wrapper.find('.btn-masquerade').length).toEqual(2);
      expect(wrapper.find('button.btn-masquerade').text()).toBe('Change user');
    });

    it('shows the failure alert', () => {
      expect(wrapper.find('.alert-danger').prop('hidden')).toBe(true);
      wrapper.setState({ masqueradeFailureAlertOpen: true });
      wrapper.update();
      expect(wrapper.find('.alert-danger').prop('hidden')).toBe(false);
    });

    it('closes the failure alert', () => {
      expect(wrapper.find('.alert-danger').prop('hidden')).toBe(true);
      wrapper.setState({ masqueradeFailureAlertOpen: true });
      wrapper.update();
      expect(wrapper.find('.alert-danger').prop('hidden')).toBe(false);
      wrapper.find('.alert-danger .close').simulate('click');
      expect(wrapper.find('.alert-danger').prop('hidden')).toBe(true);
    });

    it('handles releasing masquerade', () => {
      const postPromise = Promise.resolve({ status: 200 });
      axios.post.mockImplementation(() => postPromise);
      wrapper.find('.masquerade-form').simulate('submit');

      return postPromise.then(() => {
        wrapper.update();
        expect(wrapper.find('.alert-danger').prop('hidden')).toBe(true);
      });
    });
  });

  describe('Non-masquerading staff viewing masquerade banner', () => {
    beforeEach(() => {
      const nonMasqueradingProps = {
        masquerading: false,
        user: 'staff',
      };
      wrapper = mount(<MasqueradeBanner {...nonMasqueradingProps} />);
    });

    it('renders correct sections', () => {
      expect(wrapper.find('.masquerade-select').props().value).toEqual('Staff');
      expect(wrapper.find('.masquerade-input').length).toEqual(0);
      expect(wrapper.find('.masquerade-info-text').length).toEqual(0);
      expect(wrapper.find('.btn-masquerade').length).toEqual(2);
      expect(wrapper.find('button.btn-masquerade').text()).toBe('Submit');
    });

    it('renders text input on selecting specific learner', () => {
      expect(wrapper.find('.masquerade-input').length).toEqual(0);
      wrapper.find('.masquerade-select').simulate('change', { target: { value: 'Specific Learner' } });
      expect(wrapper.find('.masquerade-input').length).toEqual(1);
    });

    it('handles masquerading as user', () => {
      wrapper.find('.masquerade-select').simulate('change', { target: { value: 'Specific Learner' } });
      const masqueradeTarget = 'target-user@example.com';
      wrapper.find('.masquerade-input').simulate('change', { target: { value: masqueradeTarget } });
      expect(wrapper.state().identifier).toBe(masqueradeTarget);

      const postPromise = Promise.resolve({ status: 200 });
      axios.post.mockImplementation(() => postPromise);
      wrapper.find('.masquerade-form').simulate('submit');

      return postPromise.then(() => {
        wrapper.update();
        expect(wrapper.find('.alert-danger').prop('hidden')).toBe(true);
      });
    });

    it('shows the failure alert on masquerade failure', () => {
      expect(wrapper.find('.alert-danger').prop('hidden')).toBe(true);
      const postPromise = Promise.resolve({ status: 400, response: { message: 'error' } });
      axios.post.mockImplementation(() => postPromise);
      wrapper.find('.masquerade-form').simulate('submit');

      return postPromise.catch(() => {
        wrapper.update();
        expect(wrapper.find('.alert-danger').prop('hidden')).toBe(false);
      });
    });
  });
});
