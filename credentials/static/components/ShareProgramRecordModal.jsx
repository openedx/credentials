import '@babel/polyfill'; // Needed to support Promises on legacy browsers
import React from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';
import Cookies from 'js-cookie';
import { Button, Icon, InputText, Modal, StatusAlert } from '@edx/paragon';
import { CopyToClipboard } from 'react-copy-to-clipboard';
import trackEvent from './Analytics';
import StringUtils from './Utils';

class ShareProgramRecordModal extends React.Component {
  constructor(props) {
    super(props);

    this.checkUrlCopied = this.checkUrlCopied.bind(this);
    this.setProgramRecordUrl = this.setProgramRecordUrl.bind(this);
    this.setUrlError = this.setUrlError.bind(this);
    this.setUrlAsCopied = this.setUrlAsCopied.bind(this);
    this.state = {
      urlReturned: false,
      urlCopied: false,
      urlError: false,
    };
  }

  componentDidMount() {
    this.getRecordUrl();
  }

  getRecordUrl() {
    const { username, uuid } = this.props;

    const headers = {
      withCredentials: true,
      headers: {
        'X-CSRFToken': Cookies.get('credentials_csrftoken'),
      },
    };

    axios.post('/records/programs/' + uuid + '/share', {
      username,
    }, headers)
      .then(this.setProgramRecordUrl)
      .catch(this.setUrlError);
  }

  setProgramRecordUrl(response) {
    this.setState({
      programRecordUrl: response.data.url,
      urlReturned: true,
      urlError: false,
    });
  }

  setUrlAsCopied(text, result) {
    if (result) {
      this.setState({ urlCopied: true });
    }
  }

  setUrlError() {
    this.setState({ urlError: true });
  }

  getSelectedText(inputField, inputValue) {
    return inputValue.substring(inputField.selectionStart, inputField.selectionEnd);
  }

  checkUrlCopied(event) {
    const urlInput = event.target;
    const url = this.state.programRecordUrl;

    // If the full url is copied, behave as if the "Copy Link" button was clicked
    if (this.getSelectedText(urlInput, url) === url) {
      this.setUrlAsCopied(this.state.programRecordUrl, true);
      trackEvent('edx.bi.credentials.program_record.share_url_copied', {
        category: 'records',
        'program-uuid': this.props.uuid,
      });
    }
  }

  // This logic is a bit complicated, so we separate it out
  renderSwitchToSendParagraph() {
    let text = gettext('Instead of sharing a link, you can also {start_anchor}directly send your program record to {platform} partners{end_anchor} for credit or application purposes.');
    text = StringUtils.interpolate(text, { platform: this.props.platformName });

    // Because we are inserting a complicated link with javascript logic into a gettext sentence,
    // we have to be a little crazy here.
    const startOpen = text.indexOf('{start_anchor}');
    const endOpen = text.indexOf('{end_anchor}', startOpen);
    if (startOpen >= 0 && endOpen >= 0 && this.props.onSwitchToSend) {
      const startClose = text.indexOf('}', startOpen) + 1;
      const endClose = text.indexOf('}', endOpen) + 1;
      // We use a link-that-acts-like-a-button rather than a Button because a Button won't wrap
      return (
        <p>
          {text.slice(0, startOpen)}
          <a
            className="switch-to-send"
            tabIndex={0}
            onClick={this.props.onSwitchToSend}
            onKeyPress={this.props.onSwitchToSend}
            role="button"
          >
            {text.slice(startClose, endOpen)}
          </a>
          {text.slice(endClose)}
        </p>
      );
    }

    return (<p>{text}</p>);
  }

  render() {
    const {
      programRecordUrl,
      urlCopied,
      urlError,
      urlReturned,
    } = this.state;
    const { onClose, parentSelector } = this.props;

    return (
      <Modal
        title={gettext('Share Link to Record')}
        {...(parentSelector && { parentSelector })}
        onClose={onClose}
        body={(
          <div>
            {urlError &&
              <StatusAlert
                alertType="danger"
                open
                dismissible={false}
                dialog={(
                  <div>
                    <span className="h6">{ gettext('We were unable to create your record link.') }</span>
                    <p className="alert-body">{ gettext('You can close this window and try again.') }</p>
                  </div>
                )}
              />
            }
            {urlCopied &&
              <StatusAlert
                alertType="success"
                open
                dismissible={false}
                dialog={gettext('Successfully copied program record link.')}
              />
            }
            <p>{ gettext('Copy this link to share your record with a university, employer, or anyone else of you choosing. Anyone you share this link with will have access to your record forever.') }</p>
            {this.renderSwitchToSendParagraph()}
            {urlReturned &&
              <div className="url-group">
                <div onCopy={this.checkUrlCopied}>
                  <InputText
                    value={programRecordUrl}
                    name="program-record-share-url"
                    className={['program-record-share-url']}
                    label={<span className="sr-only">{gettext('Program Record URL')}</span>}
                    readOnly
                  />
                </div>
                <CopyToClipboard
                  text={programRecordUrl}
                  onCopy={this.setUrlAsCopied}
                >
                  <Button.Deprecated
                    label={gettext('Copy Link')}
                    className={['btn-primary']}
                    onClick={trackEvent('edx.bi.credentials.program_record.share_url_copied', {
                      category: 'records',
                      'program-uuid': this.props.uuid,
                    })}
                  />
                </CopyToClipboard>
              </div>
            }
            {!urlReturned && !urlError &&
              <div className="loading-wrapper d-inline-flex">
                <Icon id="ShareModalIcon" className={['fa', 'fa-spinner', 'fa-spin']} />
                <p>{ gettext('Loading record link...') }</p>
              </div>
            }
          </div>
        )}
        open
      />
    );
  }
}

ShareProgramRecordModal.propTypes = {
  onClose: PropTypes.func,
  onSwitchToSend: PropTypes.func,
  parentSelector: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.bool,
  ]),
  username: PropTypes.string.isRequired,
  uuid: PropTypes.string.isRequired,
  platformName: PropTypes.string.isRequired,
};

ShareProgramRecordModal.defaultProps = {
  onClose: () => {},
  onSwitchToSend: null,
  parentSelector: false,
};

export default ShareProgramRecordModal;
