import 'babel-polyfill'; // Needed to support Promises on legacy browsers
import React from 'react';
import PropTypes from 'prop-types';
import { Button, CheckBoxGroup, CheckBox, Modal } from '@edx/paragon';

class ShareProgramRecordModal extends React.Component {
  constructor(props) {
    super(props);
    this.sendRecord = this.sendRecord.bind(this);
    this.updateState = this.updateState.bind(this);
    this.state = {
      RIT: false,
      MIT: false,
    };
  }

  sendRecord() {
    this.setState({
      recordSent: true,
    });
  }

  updateState(checked, name) {
    this.setState({
      [name]: !this.state[name],
    });
  }

  render() {
    const { onClose, parentSelector } = this.props;

    return (
      <Modal
        title={gettext('Send to edX Credit Partner')}
        {...(parentSelector && { parentSelector })}
        onClose={onClose}
        body={(
          <div>
            <p>{ gettext('You can directly share your program record with an edX partner that accepts credit transfer for this MicroMasters Program. Once you send your record you cannot unsend it.') }</p>
            <p>{ gettext('Select organization(s) you wish to send this record to:') }</p>
            <CheckBoxGroup>
              <CheckBox
                id="checkbox1"
                name="RIT"
                label="RIT"
                onChange={this.updateState}
                checked={this.state.RIT}
              />
              <CheckBox
                id="checkbox2"
                name="MIT"
                label="MIT"
                onChange={this.updateState}
                checked={this.state.MIT}
              />
            </CheckBoxGroup>
          </div>
        )}
        open
        buttons={[
          <Button
            label={gettext('Send')}
            buttonType="primary"
            onClick={this.sendRecord}
          />,
        ]}
      />
    );
  }
}

ShareProgramRecordModal.propTypes = {
  onClose: PropTypes.func,
  parentSelector: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.bool,
  ]),
};

ShareProgramRecordModal.defaultProps = {
  onClose: () => {},
  parentSelector: false,
};

export default ShareProgramRecordModal;
