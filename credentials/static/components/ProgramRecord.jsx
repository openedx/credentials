import React from 'react';
import axios from 'axios';
import PropTypes from 'prop-types';
import { Button, Icon, StatusAlert } from '@edx/paragon';
import Cookies from 'js-cookie';

import FoldingTable from './FoldingTable';
import RecordsHelp from './RecordsHelp';
import ProgramIcon from './ProgramIcon';
import SendLearnerRecordModal from './SendLearnerRecordModal';
import ShareProgramRecordModal from './ShareProgramRecordModal';
import StringUtils from './Utils';
import trackEvent from './Analytics';

class ProgramRecord extends React.Component {
  constructor(props) {
    super(props);

    this.loadSendRecordModal = this.loadSendRecordModal.bind(this);
    this.loadShareModel = this.loadShareModel.bind(this);
    this.closeSendRecordModal = this.closeSendRecordModal.bind(this);
    this.closeShareModel = this.closeShareModel.bind(this);
    this.setActiveButton = this.setActiveButton.bind(this);
    this.downloadRecord = this.downloadRecord.bind(this);

    this.formatDate = this.formatDate.bind(this);
    this.formatGradeData = this.formatGradeData.bind(this);
    this.sendRecords = this.sendRecords.bind(this);
    this.updateCreditPathwaysSent = this.updateCreditPathwaysSent.bind(this);
    this.sendRecords = this.sendRecords.bind(this);
    this.formatPercentage = this.formatPercentage.bind(this);
    this.closeSendRecordFailureAlert = this.closeSendRecordFailureAlert.bind(this);
    this.closeSendRecordSuccessAlert = this.closeSendRecordSuccessAlert.bind(this);
    this.closeSendRecordLoadingAlert = this.closeSendRecordLoadingAlert.bind(this);
    this.creditPathways = this.parseCreditPathways();
    this.showSendRecordButton = this.props.pathways.length > 0;

    this.state = {
      focusActiveButton: false,
      buttonDisabled: false,
      shareModelOpen: false,
      sendRecordModalOpen: false,
      isPublic: true,
      recordDownloaded: false,
      sendRecordSuccessOrgs: [],
      sendRecordFailureOrgs: [],
      sendRecordSuccessAlertOpen: false,
      sendRecordFailureAlertOpen: false,
      sendRecordLoadingAlertOpen: false,
    };
  }

  componentDidUpdate() {
    if (this.state.focusActiveButton) {
      this.activeButton.focus();
      this.state.focusActiveButton = false;
    }
  }

  setActiveButton(button) {
    this.activeButton = button;
  }

  loadSendRecordModal(event) {
    this.setState({
      sendRecordModalOpen: true,
      shareModelOpen: false,
      buttonDisabled: true,
    });
    this.setActiveButton(event.target);
    trackEvent('edx.bi.credentials.program_record.send_started', {
      category: 'records',
      'program-uuid': this.props.uuid,
    });
  }

  loadShareModel(event) {
    this.setState({
      sendRecordModalOpen: false,
      shareModelOpen: true,
      buttonDisabled: true,
    });
    this.setActiveButton(event.target);
    trackEvent('edx.bi.credentials.program_record.share_started', {
      category: 'records',
      'program-uuid': this.props.uuid,
    });
  }

  closeSendRecordModal() {
    this.setState({
      sendRecordModalOpen: false,
      buttonDisabled: false,
      focusActiveButton: true,
    });
  }

  closeShareModel() {
    this.setState({
      shareModelOpen: false,
      buttonDisabled: false,
      focusActiveButton: true,
    });
  }

  downloadRecord(uuid) {
    this.setState({ recordDownloaded: true });
    window.location = '/records/programs/shared/' + uuid + '/csv';
  }


  formatDate(isoDate) {
    if (!isoDate) {
      return isoDate;
    }

    const date = new Date(isoDate);

    return StringUtils.interpolate('{month}/{date}/{year}', {
      month: date.getMonth() + 1,
      date: date.getDate(),
      year: date.getFullYear().toString().slice(2),
    });
  }

  formatPercentage(decimal) {
    if (!decimal) {
      return decimal;
    }

    return parseInt(Math.round(decimal * 100), 10).toString() + '%';
  }

  formatGradeData() {
    const { grades } = this.props;

    return grades.map(course => ({
      ...course,
      course_id: course.course_id.replace(/^course-v1:/, ''),
      // If certificate not earned hide some fields
      ...(!course.issue_date && { course_id: null }),
      ...(!course.issue_date && { letter_grade: null }),
      ...(!course.issue_date && { attempts: null }),
      percent_grade: course.issue_date ? this.formatPercentage(course.percent_grade) : '',
      issue_date: this.formatDate(course.issue_date),
      status: course.issue_date ?
        <span className="badge badge-success">{gettext('Earned')}</span> :
        <span className="badge badge-secondary">{gettext('Not Earned')}</span>,
    }));
  }

  // Once we send the records, we want to update the checkboxes
  updateCreditPathwaysSent(successOrgs) {
    for (let i = 0; i < successOrgs.length; i += 1) {
      const pathway = this.creditPathways[successOrgs[i]];
      pathway.sent = true;
      pathway.checked = true;
    }
  }

  // Parse the list of credit pathways into an object, filtering out all non-credit pathways
  parseCreditPathways() {
    const creditPathways = {};

    for (let i = 0; i < this.props.pathways.length; i += 1) {
      const pathway = this.props.pathways[i];
      const sent = (pathway.status === 'sent');

      if (pathway.pathway_type === 'credit') {
        creditPathways[pathway.name] = {
          sent,
          checked: sent,
          id: pathway.id,
          isActive: pathway.is_active,
        };
      }
    }

    return creditPathways;
  }

  // Posts to the send records API for each org that is selected
  // This functionality should be included in the Send Record Modal and
  // not passed as a callback; using redux to update global state
  sendRecords(orgs) {
    const headers = {
      withCredentials: true,
      headers: {
        'X-CSRFToken': Cookies.get('credentials_csrftoken'),
      },
    };

    const uuid = this.props.uuid;

    trackEvent('edx.bi.credentials.program_record.send_finished', {
      category: 'records',
      'program-uuid': this.props.uuid,
      organizations: orgs,
    });

    // Show the loading "info" alert
    this.setState({ sendRecordLoadingAlertOpen: true });

    const successOrgs = [];
    const failureOrgs = [];
    let showSuccess = false;
    let showFailure = false;

    // Send all requeests and update success and failure statuses
    // Disabling eslint error since make_translations fails when using backticks
    // eslint-disable-next-line prefer-template
    axios.all(orgs.map(org => axios.post('/records/programs/' + uuid + '/send',
      { username: this.props.learner.username, pathway_id: this.creditPathways[org].id },
      headers)
      .then((response) => {
        if (response.status >= 200 && response.status < 300) {
          successOrgs.push(org);
        } else {
          failureOrgs.push(org);
        }
      })
      .catch((() => {
        failureOrgs.push(org);
      })),
    ))
    .then(() => {
      if (successOrgs.length > 0) { showSuccess = true; }
      if (failureOrgs.length > 0) { showFailure = true; }
      this.setState({
        sendRecordSuccessOrgs: successOrgs,
        sendRecordFailureOrgs: failureOrgs,
        sendRecordSuccessAlertOpen: showSuccess,
        sendRecordFailureAlertOpen: showFailure,
        sendRecordLoadingAlertOpen: false,
      });
      this.updateCreditPathwaysSent(successOrgs);
    });
  }

  closeSendRecordFailureAlert() {
    this.setState({ sendRecordFailureOrgs: [], sendRecordFailureAlertOpen: false });
  }

  closeSendRecordSuccessAlert() {
    this.setState({ sendRecordSuccessOrgs: [], sendRecordSuccessAlertOpen: false });
  }

  closeSendRecordLoadingAlert() {
    this.setState({ sendRecordLoadingAlertOpen: false });
  }


  render() {
    const {
      learner,
      program,
      platform_name: platformName,
      isPublic,
      icons,
      uuid,
      loadModalsAsChildren,
      helpUrl,
    } = this.props;
    const { sendRecordModalOpen, shareModelOpen } = this.state;
    const recordWrapperClass = 'program-record-wrapper';
    const defaultModalProps = {
      ...(loadModalsAsChildren && { parentSelector: '.' + recordWrapperClass }),
    };
    const hasHelpUrl = helpUrl !== '';

    return (
      <main id="main-content" className={recordWrapperClass} tabIndex="-1">
        {!isPublic &&
          <div className="program-record-actions program-record-row">
            <a href="/records/" className="top-bar-link">
              <span className="fa fa-caret-left" aria-hidden="true" />
              <span className="fa fa-caret-right" aria-hidden="true" /> {gettext('Back to My Records')}
            </a>
            {this.showSendRecordButton &&
              <Button.Deprecated
                label={gettext('Send Learner Record')}
                className={['btn-primary']}
                onClick={this.loadSendRecordModal}
                disabled={this.state.buttonDisabled}
              />
            }
            <Button.Deprecated
              label={gettext('Share')}
              className={['btn-outline-primary']}
              onClick={this.loadShareModel}
              inputRef={this.setShareButton}
              disabled={this.state.buttonDisabled}
            />
          </div>
        }
        {isPublic &&
          <div className="program-record-actions program-record-row justify-content-end">
            <Button.Deprecated
              label={gettext('Download Record')}
              className={['btn-primary']}
              onClick={() => this.downloadRecord(uuid)}
              uuid={uuid}
            />
          </div>
        }
        {
          <StatusAlert
            alertType="info"
            open={this.state.sendRecordLoadingAlertOpen}
            onClose={this.closeSendRecordLoadingAlert}
            dialog={
              <div>
                <span className="h6">{ gettext('We are sending your program record.') }</span>
                <Icon id="StatusAlertIcon" className={['fa', 'fa-spinner', 'fa-spin']} />
              </div>
             }
          />
        }
        {
          <StatusAlert
            alertType="danger"
            open={this.state.sendRecordFailureAlertOpen}
            onClose={this.closeSendRecordFailureAlert}
            dialog={
              <div>
                <span className="h6">{ gettext('We were unable to send your program record.') }</span>
                <span className="alert-body">
                  {StringUtils.interpolate(gettext('We were unable to send your record to {orgs}.  You can attempt to send this record again.  Contact support if this issue persists.'),
                      { orgs: StringUtils.formatStringList(this.state.sendRecordFailureOrgs) })}
                </span>
              </div>
             }
          />
        }
        {
          <StatusAlert
            alertType="success"
            open={this.state.sendRecordSuccessAlertOpen}
            onClose={this.closeSendRecordSuccessAlert}
            dialog={
              <div>
                <span className="h6">{ gettext('You have successfully shared your Learner Record') }</span>
                <span className="alert-body">
                  {StringUtils.interpolate(gettext('You have sent your record to {orgs}.  Next, ensure you understand their application process.'),
                      { orgs: StringUtils.formatStringList(this.state.sendRecordSuccessOrgs) })}
                </span>
              </div>
             }
          />
        }
        <article className="program-record">
          <header className="d-flex justify-content-between program-record-header">
            <div className="program-overview">
              <div className="program-headings">
                <h1 className="program-title h2">{ StringUtils.interpolate(gettext('{name} Record'), { name: program.name }) }</h1>
                <div className="text-muted program-type">
                  <ProgramIcon type={program.type} iconDict={icons} className="program-icon" />
                  { StringUtils.interpolate(gettext('{type} Program Record'), { type: program.type_name }) }
                </div>
              </div>
              <div className="d-flex program-status">
                {
                  (program.completed &&
                    <span className="badge badge-success">{gettext('Completed')}</span>) ||
                  (program.empty &&
                    <span className="badge badge-secondary">{gettext('Not Earned')}</span>) ||
                  (<span className="badge badge-warning">{gettext('Partially Completed')}</span>)
                }
                <span className="updated">
                  { StringUtils.interpolate(
                      gettext('Last Updated {date}'), {
                        date: this.formatDate(program.last_updated),
                      },
                    )
                  }
                </span>
              </div>
            </div>
            <div name="school-name" className="h4 school-name">
              { StringUtils.interpolate('{platform} | {school}', { platform: platformName, school: program.school }) }
            </div>
          </header>

          <div className="learner-info">
            {learner.full_name && <span className="h4 font-weight-normal user">{learner.full_name}</span>}
            <div className="details-ltr">
              {learner.username}<span className="pipe">|</span>{learner.email}
            </div>
            <div className="details-rtl">
              {learner.email}<span className="pipe">|</span>{learner.username}
            </div>
          </div>

          <div className="program-record-grades">
            <FoldingTable
              columns={[
                // Note that when you change one of these strings, you should look at
                // the foldedColumns for any necessary changes there too.
                { key: 'name', label: gettext('Course Name') },
                { key: 'school', label: gettext('School') },
                { key: 'course_id', label: gettext('Course ID') },
                { key: 'percent_grade', label: gettext('Highest Grade Earned') },
                { key: 'letter_grade', label: gettext('Letter Grade') },
                { key: 'attempts', label: gettext('Verified Attempts') },
                { key: 'issue_date', label: gettext('Date Earned') },
                { key: 'status', label: gettext('Status') },
              ]}
              foldedColumns={[
                { key: 'name', className: 'h6 font-weight-bold' },
                { key: 'school' },
                { key: 'course_id', format: gettext('Course ID: {}') },
                { key: 'percent_grade', format: gettext('Highest Grade Earned: {}') },
                { key: 'letter_grade', format: gettext('Letter Grade: {}') },
                { key: 'attempts', format: gettext('Verified Attempts: {}') },
                { key: 'issue_date', format: gettext('Date Earned: {}') },
                { key: 'status', label: gettext('Status: {}') },
              ]}
              data={this.formatGradeData()}
              dataKey="name"
            />
          </div>
        </article>

        {hasHelpUrl && <RecordsHelp helpUrl={helpUrl} />}

        {sendRecordModalOpen &&
          <SendLearnerRecordModal
            {...defaultModalProps}
            onClose={this.closeSendRecordModal}
            sendHandler={this.sendRecords}
            uuid={uuid}
            typeName={program.type_name}
            platformName={platformName}
            // Using this JSON trick since the {...} syntax and Object.assign() both don't work here
            // For some reason they were not properly creating copies
            creditPathways={JSON.parse(JSON.stringify(this.creditPathways))}
            // Passing both a list and an object so that we can maintain pathway ordering
            creditPathwaysList={this.props.pathways.filter(pathway => pathway.pathway_type === 'credit')}
          />
        }
        {shareModelOpen &&
          <ShareProgramRecordModal
            {...defaultModalProps}
            onClose={this.closeShareModel}
            onSwitchToSend={this.loadSendRecordModal}
            username={learner.username}
            uuid={uuid}
            platformName={platformName}
          />
        }
      </main>
    );
  }
}

ProgramRecord.propTypes = {
  learner: PropTypes.shape({
    email: PropTypes.string,
    full_name: PropTypes.string,
    username: PropTypes.string,
  }).isRequired,
  program: PropTypes.shape({
    name: PropTypes.string,
    school: PropTypes.string,
    completed: PropTypes.bool,
    empty: PropTypes.bool,
    type: PropTypes.string,
    type_name: PropTypes.string,
    last_updated: PropTypes.string,
  }).isRequired,
  grades: PropTypes.arrayOf(PropTypes.object).isRequired,
  pathways: PropTypes.arrayOf(PropTypes.object),
  isPublic: PropTypes.bool,
  icons: PropTypes.shape(),
  uuid: PropTypes.string.isRequired,
  platform_name: PropTypes.string.isRequired,
  loadModalsAsChildren: PropTypes.bool,
  helpUrl: PropTypes.string,
};

ProgramRecord.defaultProps = {
  pathways: [],
  isPublic: true,
  icons: {},
  loadModalsAsChildren: true,
  helpUrl: '',
};

export default ProgramRecord;
