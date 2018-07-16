import 'babel-polyfill'; // Needed to support Promises on legacy browsers
import React from 'react';
import PropTypes from 'prop-types';
import { Button, CheckBoxGroup, CheckBox, Modal } from '@edx/paragon';
import trackEvent from './Analytics';

class SendLearnerRecordModal extends React.Component {
  constructor(props) {
    super(props);
    this.sendRecord = this.sendRecord.bind(this);
    this.updateState = this.updateState.bind(this);
    this.state = {
      pathways: props.pathways,
    };
  }

  // Get the organizations we are sharing for the analytics event
  getCheckedOrganizations() {
    const organizations = [];
    this.state.pathways.forEach((pathway) => {
      organizations.push(pathway.org_name);
    });
    return organizations;
  }

  updateState(checked, name) {
    this.setState({
      [name]: !this.state[name],
    });
  }

  sendRecord() {
    this.setState({
      recordSent: true,
    });
    trackEvent('edx.bi.credentials.program_record.send_finished', {
      category: 'records',
      'program-uuid': this.props.uuid,
      organizations: this.getCheckedOrganizations(),
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
              {this.state.pathways.map(pathway =>
                (<CheckBox
                  name={pathway.name}
                  label={pathway.name}
                  onChange={this.updateState}
                />) // eslint-disable-line comma-dangle
              )}
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

SendLearnerRecordModal.propTypes = {
  onClose: PropTypes.func,
  parentSelector: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.bool,
  ]),
  uuid: PropTypes.string.isRequired,
  pathways: PropTypes.arrayOf(PropTypes.object).isRequired,
};

SendLearnerRecordModal.defaultProps = {
  onClose: () => {},
  parentSelector: false,
};

export default SendLearnerRecordModal;
