import 'babel-polyfill'; // Needed to support Promises on legacy browsers
import React from 'react';
import PropTypes from 'prop-types';
import { Button, CheckBoxGroup, CheckBox, Modal } from '@edx/paragon';
import StringUtils from './Utils';

class SendLearnerRecordModal extends React.Component {
  constructor(props) {
    super(props);
    this.updateState = this.updateState.bind(this);
    this.getCheckedOrganizations = this.getCheckedOrganizations.bind(this);
    this.callSendHandler = this.callSendHandler.bind(this);
    this.state = {
      RIT: false,
      MIT: false,
    };
  }

  // Get the organizations we are sharing for the analytics event
  // TODO: remove hardcoded values once the state is no longer hardcoded
  getCheckedOrganizations() {
    const organizations = [];

    if (this.state.RIT) { organizations.push('RIT'); }
    if (this.state.MIT) { organizations.push('MIT'); }
    return organizations;
  }

  updateState(checked, name) {
    this.setState({
      [name]: !this.state[name],
    });
  }

  callSendHandler() {
    this.props.sendHandler(this.getCheckedOrganizations());
  }

  render() {
    const { onClose, parentSelector, typeName, platformName } = this.props;

    return (
      <Modal
        title={StringUtils.interpolate(
          gettext('Send to {platform} Credit Partner'),
          { platform: platformName },
        )}
        {...(parentSelector && { parentSelector })}
        onClose={onClose}
        body={(
          <div>
            <p>{ StringUtils.interpolate(
              gettext('You can directly share your program record with {platform} partners that accept credit for this {type} Program. Once you send your record you cannot unsend it.'),
              {
                platform: platformName,
                type: typeName,
              },
            )}</p>
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
            onClick={this.callSendHandler}
          />,
        ]}
      />
    );
  }
}

SendLearnerRecordModal.propTypes = {
  onClose: PropTypes.func,
  sendHandler: PropTypes.func.isRequired,
  parentSelector: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.bool,
  ]),
  uuid: PropTypes.string.isRequired,
  typeName: PropTypes.string.isRequired,
  platformName: PropTypes.string.isRequired,
};

SendLearnerRecordModal.defaultProps = {
  onClose: () => {},
  parentSelector: false,
};

export default SendLearnerRecordModal;
