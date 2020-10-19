import React from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';
import Cookies from 'js-cookie';
import { Button, StatusAlert } from '@edx/paragon';

import StringUtils from './Utils';

class MasqueradeBanner extends React.Component {
  constructor(props) {
    super(props);
    this.closeMasqueradeFailureAlert = this.closeMasqueradeFailureAlert.bind(this);
    this.handleSelectChange = this.handleSelectChange.bind(this);
    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.state = {
      identifier: '',
      masqueradeFailureAlertOpen: false,
      masqueradeTarget: this.props.masquerading ? 'Specific Learner' : 'Staff',
    };
  }

  getButtonText() {
    return this.props.masquerading ? gettext('Change user') : gettext('Submit');
  }

  closeMasqueradeFailureAlert() {
    this.setState({ masqueradeFailureAlertOpen: false });
  }

  handleInputChange(event) {
    this.setState({ identifier: event.target.value });
  }

  handleSelectChange(event) {
    this.setState({ masqueradeTarget: event.target.value });
  }

  handleSubmit(event) {
    this.handleMasquerade();
    event.preventDefault();
  }

  targetingLearner() {
    return this.state.masqueradeTarget.startsWith('Specific Learner');
  }

  constructMasqueradeUrl() {
    let url = '/hijack/';
    if (!this.props.masquerading && this.targetingLearner()) {
      const user = this.state.identifier;
      url += this.state.identifier.includes('@') ? 'email/' : 'username/';
      url += user + '/';
    } else {
      url += 'release-hijack/';
    }
    return url;
  }

  handleMasquerade() {
    const headers = {
      withCredentials: true,
      headers: {
        'X-CSRFToken': Cookies.get('credentials_csrftoken'),
      },
    };

    const url = this.constructMasqueradeUrl();
    axios.post(url, {}, headers)
      .then((response) => {
        if (response.status >= 200 && response.status < 300) {
          window.location.reload();
        } else {
          this.setState({ masqueradeFailureAlertOpen: true });
        }
      })
      .catch(() => {
        this.setState({ masqueradeFailureAlertOpen: true });
      });
  }

  render() {
    const masqueradeBannerWrapperClass = 'masquerade-banner-wrapper';
    return (
      <nav className={masqueradeBannerWrapperClass}>
        <div className="masquerade-banner-actions">
          <form onSubmit={this.handleSubmit} className="masquerade-form form-group">
            <label htmlFor="masquerade-select" className="masquerade-label"> { gettext('View as: ') }
              <select className="masquerade-select" id="masquerade-select" onChange={this.handleSelectChange} value={this.state.masqueradeTarget} >
                <option value="Staff">{gettext('Staff')}</option>
                <option value="Specific Learner">{gettext('Specific Learner')}</option>
              </select>
            </label>
            {(this.targetingLearner() && !this.props.masquerading) &&
              <label htmlFor="masquerade-input" className="masquerade-label"> { gettext('Username or email: ') }
                <input type="text" className="masquerade-input" id="masquerade-input" onChange={this.handleInputChange} value={this.state.identifier} />
              </label>
            }
            {this.props.masquerading &&
              <span className="masquerade-info-text">{ StringUtils.interpolate(gettext('You are currently viewing as: {user}'), { user: this.props.user }) }</span>
            }
            <Button.Deprecated
              className={['btn-masquerade', 'btn-primary']}
              label={this.getButtonText()}
              type="submit"
            />
          </form>
        </div>
        {
          <StatusAlert
            alertType="danger"
            open={this.state.masqueradeFailureAlertOpen}
            onClose={this.closeMasqueradeFailureAlert}
            dialog={
              <div>
                <span className="h6">{ gettext('Masquerading failed') }</span>
                <span className="alert-body">{ gettext('You either do not have permission to masquerade as this user, or the user could not be found.') }</span>
              </div>
             }
          />
        }
      </nav>
    );
  }
}

MasqueradeBanner.propTypes = {
  masquerading: PropTypes.bool.isRequired,
  user: PropTypes.string.isRequired,
};

export default MasqueradeBanner;
