import React from 'react';
import { mount } from 'enzyme';
import axios from 'axios';
import ShareProgramRecordModal from '../ShareProgramRecordModal';

jest.mock('axios');
let wrapper;
let promise;

const defaultProps = {
  parentSelector: 'body',
  username: 'Pennywise',
  uuid: '1a2b3c4d',
};

describe('<ShareProgramRecordModal />', () => {
  describe('Happy Path', () => {
    beforeEach(() => {
      promise = Promise.resolve({ uuid: '21366aa129514333a4a9f32161ad3a69' });
      axios.post.mockImplementation(() => promise);
      wrapper = mount(<ShareProgramRecordModal {...defaultProps} />);
    });

    it('displays the program record url if API returns successfully', () => {
      expect(wrapper.find('.modal-dialog').length).toBe(1);
      expect(wrapper.find('.modal-header .modal-title').text()).toBe('Share Link to Record');
      expect(wrapper.find('.modal-header button').length).toBe(1);
      expect(wrapper.find('.modal-footer button').length).toBe(1);

      expect(wrapper.find('.modal-body .loading-wrapper').length).toBe(1);
      expect(wrapper.find('.modal-body button.btn-primary').length).toBe(0);

      return promise.then(() => {
        wrapper.update();
        expect(wrapper.find('.modal-body .form-group input').props().value).toBe(wrapper.state('programRecordUrl'));
        expect(wrapper.find('.modal-body .loading-wrapper').length).toBe(0);
        expect(wrapper.find('.modal-body button.btn-primary').length).toBe(1);
      });
    });

    it('closes if the header close button is clicked', () => {
      expect(wrapper.find('.modal-dialog').length).toBe(1);

      return promise.then(() => {
        wrapper.update();
        expect(wrapper.find('.modal-dialog').length).toBe(1);
        wrapper.find('.modal-header button').simulate('click');
        expect(wrapper.find('.modal-dialog').length).toBe(0);
      });
    });

    it('closes if the footer close button is clicked', () => {
      expect(wrapper.find('.modal-dialog').length).toBe(1);

      return promise.then(() => {
        wrapper.update();
        expect(wrapper.find('.modal-dialog').length).toBe(1);
        wrapper.find('.modal-footer button').simulate('click');
        expect(wrapper.find('.modal-dialog').length).toBe(0);
      });
    });

    it('updates state if the url is copied to the clipboard', () => {
      expect(wrapper.state('urlCopied')).toBe(false);

      return promise.then(() => {
        wrapper.update();
        expect(wrapper.state('urlCopied')).toBe(false);
        wrapper.instance().setUrlAsCopied('text', 'result');
        expect(wrapper.state('urlCopied')).toBe(true);
      });
    });
  });

  describe('Sad Path', () => {
    beforeEach(() => {
      promise = Promise.resolve({
        status: 400,
        response: { message: 'problem' },
      });
      axios.post.mockImplementation(() => promise);
      wrapper = mount(<ShareProgramRecordModal {...defaultProps} />);
    });


    it('shows error message if API call to get url fails', () => {
      expect(wrapper.find('.modal-body .alert-danger').length).toBe(0);
      expect(wrapper.find('.modal-body .loading-wrapper').length).toBe(1);

      return promise.then(() => {
        wrapper.setState({ urlError: true });
        wrapper.update();

        expect(wrapper.find('.modal-body .loading-wrapper').length).toBe(0);
        expect(wrapper.find('.modal-body .alert-danger').length).toBe(1);

        const errorText = 'We were unable to create your record link.';
        expect(wrapper.find('.modal-body .alert-danger h3').text()).toBe(errorText);
      });
    });
  });
});
