import '@babel/polyfill'; // Needed to support Promises on legacy browsers
import React from 'react';
import PropTypes from 'prop-types';
import { Button, CheckBoxGroup, CheckBox, Modal, StatusAlert } from '@edx/paragon';
import StringUtils from './Utils';

class SendLearnerRecordModal extends React.Component {
  constructor(props) {
    super(props);
    this.checkCreditPathway = this.checkCreditPathway.bind(this);
    this.getCheckedOrganizations = this.getCheckedOrganizations.bind(this);
    this.callSendHandler = this.callSendHandler.bind(this);
    this.getPathwayDisplayName = this.getPathwayDisplayName.bind(this);
    this.state = {
      creditPathways: this.props.creditPathways,
      numCheckedOrganizations: 0, // Used to decide if we should gray out the 'send' button
    };

    this.anyInactivePathways = this.checkAnyInactivePathways();
  }


  // Get the organizations that are currently checked off
  getCheckedOrganizations() {
    const organizations = [];

    for (let i = 0; i < this.props.creditPathwaysList.length; i += 1) {
      const name = this.props.creditPathwaysList[i].name;
      const pathway = this.state.creditPathways[name];

      if (pathway.checked && !pathway.sent) {
        organizations.push(name);
      }
    }

    return organizations;
  }


  getPathwayDisplayName(name) {
    const pathway = this.state.creditPathways[name];

    if (pathway.sent) {
      return StringUtils.interpolate(gettext('{name} - Sent'), { name });
    } else if (!pathway.isActive) {
      return StringUtils.interpolate(gettext('{name} - Not Yet Available'), { name });
    }

    return name;
  }


  // Check if there are any organizations that are inactive
  checkAnyInactivePathways() {
    for (let i = 0; i < this.props.creditPathwaysList.length; i += 1) {
      const pathway = this.props.creditPathwaysList[i];
      if (!this.state.creditPathways[pathway.name].isActive) {
        return true;
      }
    }

    return false;
  }


  callSendHandler() {
    this.props.sendHandler(this.getCheckedOrganizations());

    // Close the modal since the send status shows up on the ProgramRecord page
    this.props.onClose();
  }


  // Update a credit pathway's state when the checkbox is updated
  checkCreditPathway(checked, name) {
    let count = this.state.numCheckedOrganizations;
    if (checked) {
      count += 1;
    } else {
      count -= 1;
    }

    const creditPathways = { ...this.state.creditPathways };
    creditPathways[name].checked = checked;
    this.setState({
      numCheckedOrganizations: count,
      creditPathways,
    });
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
            {this.anyInactivePathways && <div>
              <StatusAlert
                alertType="danger"
                open
                dismissible={false}
                dialog={(
                  <div>
                    <span className="h6">{gettext('Not all credit partners are ready to receive records yet')}</span>
                    <p className="alert-body">{gettext('You can check back in the future or share your record link directly if you need to do so immediately.')}</p>
                  </div>)}
              />
            </div>
            }
            <p>{ gettext('Select organization(s) you wish to send this record to:') }</p>
            <CheckBoxGroup>
              {this.props.creditPathwaysList.map(pathway => (
                <CheckBox
                  id={'checkbox-' + pathway.id}
                  name={pathway.name}
                  label={this.getPathwayDisplayName(pathway.name)}
                  key={pathway.id}
                  disabled={this.state.creditPathways[pathway.name].sent ||
                      !this.state.creditPathways[pathway.name].isActive}
                  onChange={this.checkCreditPathway}
                  checked={this.state.creditPathways[pathway.name].checked}
                />
              ))}
            </CheckBoxGroup>
          </div>
        )}
        open
        buttons={[
          <Button.Deprecated
            label={gettext('Send')}
            buttonType="primary"
            onClick={this.callSendHandler}
            disabled={this.state.numCheckedOrganizations <= 0}
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
  // TODO: replace with redux global state variables
  // eslint-disable-next-line react/forbid-prop-types
  creditPathways: PropTypes.object,
  creditPathwaysList: PropTypes.arrayOf(PropTypes.object),
};

SendLearnerRecordModal.defaultProps = {
  onClose: () => {},
  parentSelector: false,
  creditPathways: {},
  creditPathwaysList: [],
};

export default SendLearnerRecordModal;
