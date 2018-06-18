import 'babel-polyfill'; // Needed to support Promises on legacy browsers
import React from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';
import Cookies from 'js-cookie';
import { Button, Icon, InputText, Modal, StatusAlert } from '@edx/paragon';
import { CopyToClipboard } from 'react-copy-to-clipboard';

class ShareProgramRecordModal extends React.Component {
  constructor(props) {
    super(props);

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
    const { username, uuid } = this.props;

    const headers = {
      withCredentials: true,
      headers: {
        'X-CSRFToken': Cookies.get('credentials_csrftoken'),
      },
    };

    axios.post('/records/new/', {
      username,
      uuid,
    }, headers)
      .then(this.setProgramRecordUrl)
      .catch(this.setUrlError);
  }

  setProgramRecordUrl(response) {
    // TODO: remove console.log once API integration verified
    console.log(`setProgramRecordUrl: ${response}`); // eslint-disable-line no-console
    this.setState({
      programRecordUrl: response.uuid,
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
        parentSelector={parentSelector}
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
                    <h3>{ gettext('We were unable to create your record link.') }</h3>
                    <p>{ gettext('You can close this window and try again.') }</p>
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
            <p>{ gettext('Instead of sharing a link, you can also directly send your program record to edX partners for credit or application purposes.') }</p>
            {urlReturned &&
              <div>
                <InputText
                  value={programRecordUrl}
                  name="program-record-share-url"
                  label={<span className="sr-only">{gettext('Program Record URL')}</span>}
                  disabled
                />
                <CopyToClipboard
                  text={programRecordUrl}
                  onCopy={this.setUrlAsCopied}
                >
                  <Button
                    label={gettext('Copy Link')}
                    className={['btn-primary']}
                  />
                </CopyToClipboard>
              </div>
            }
            {!urlReturned && !urlError &&
              <div className="loading-wrapper d-inline-flex">
                <Icon className={['fa', 'fa-spinner', 'fa-spin']} />
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
  parentSelector: PropTypes.string.isRequired,
  username: PropTypes.string.isRequired,
  uuid: PropTypes.string.isRequired,
};

ShareProgramRecordModal.defaultProps = {
  onClose: () => {},
};

export default ShareProgramRecordModal;
