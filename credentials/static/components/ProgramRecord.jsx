import PropTypes from 'prop-types';
import React from 'react';

import { Button } from '@edx/paragon';

import FoldingTable from './FoldingTable';

import StringUtils from '../js/StringUtils';

class ProgramRecord extends React.Component {

  static renderBackLink() {
    return (
      <a href="/records/" className={['top-bar-link', 'flex-4'].join(' ')}>{gettext('< Back to My Records')}</a>
    );
  }

  static renderShareButton() {
    const link = '/share'; // TODO placeholder
    return (
      <a href={link}>
        <Button label={gettext('Share')} className={['top-bar-button', 'flex-1'].join(' ')} />
      </a>
    );
  }

  static renderTopBar(id) {
    return (
      <section id={id} className={['program-record-row']}>
        {this.renderBackLink()}
        {this.renderShareButton()}
      </section>
    );
  }

  static renderProgramName(data) {
    return (
      <div name="program-name" className={['hd-3', 'flex-1'].join(' ')}>
        { StringUtils.interpolate(gettext('{program_name} Record'), { program_name: data.program.name }) }
      </div>
    );
  }

  static renderSchoolName(data) {
    return (
      <div name="school-name" className={['hd-3']}>
        { StringUtils.interpolate(gettext('{platform} | {school}'), { platform: data.platform_name, school: data.program.school }) }
      </div>
    );
  }

  static renderRecordTitleBar(id, data) {
    return (
      <section id={id} className={['program-record-row']}>
        {this.renderProgramName(data)}
        {this.renderSchoolName(data)}
      </section>
    );
  }

  static renderLearnerInfo(id, data) {
    // Convert the data to an array despite being a single object to use the FoldingTable styles
    const dataArr = [data.learner];
    return (
      <section id={id} className={['learner-info']}>
        <FoldingTable
          columns={[
            { key: 'full_name', label: gettext('Name') },
            { key: 'username',
              label: StringUtils.interpolate(gettext('{platform} User ID'), { platform: data.platform_name }),
            },
            { key: 'email', label: gettext('Email') },
          ]}
          foldedColumns={[
            { key: 'full_name', className: 'hd-5 emphasized', format: gettext('Name: {}') },
            { key: 'username', className: 'hd-5 emphasized', format: StringUtils.interpolate(gettext('{platform} User ID: {}'), { platform: data.platform_name }) },
            { key: 'email', className: 'hd-5 emphasized', format: gettext('Email: {}') },
          ]}
          data={dataArr}
          dataKey="username"
        />
      </section>
    );
  }

  static renderProgramRecordList(id, data) {
    return (
      <section id={id}>
        <FoldingTable
          columns={[
            { key: 'name', label: gettext('Course Name') },
            { key: 'school', label: gettext('School') },
            { key: 'attempts', label: gettext('Verified Attempts') },
            { key: 'course_id', label: gettext('Course ID') },
            { key: 'issue_date', label: gettext('Issue Date') },
            { key: 'percent_grade', label: gettext('Highest Grade Earned') },
            { key: 'letter_grade', label: gettext('Letter Grade') },
          ]}
          foldedColumns={[
            { key: 'name', className: 'hd-5 emphasized' },
            { key: 'school' },
            { key: 'attempts', format: gettext('Verified Attempts: {}') },
            { key: 'course_id', format: gettext('Course ID: {}') },
            { key: 'start', format: gettext('Start Date: {}') },
            { key: 'end', format: gettext('End Date: {}') },
            { key: 'percent_grade', format: gettext('Percent Grade: {}') },
            { key: 'letter_grade', format: gettext('Letter Grade: {}') },
          ]}
          data={data}
          dataKey="name"
        />
        <hr />
      </section>
    );
  }

  constructor(props) {
    super(props);
    this.state = {
      record: this.props.record,
    };
  }

  render() {
    return (
      <main className="program-record">
        {this.state.record && ProgramRecord.renderTopBar('program-record-actions')}
        {this.state.record && ProgramRecord.renderRecordTitleBar(
          'program-record-title-bar',
          this.state.record,
        )}
        {this.state.record && ProgramRecord.renderLearnerInfo(
          'learner-info',
          this.state.record,
        )}
        {this.state.record && ProgramRecord.renderProgramRecordList(
          'program-record',
          this.state.record.grades,
        )}
      </main>
    );
  }
}

ProgramRecord.propTypes = {
  record: PropTypes.shape({
    learner: {},
    program: {},
    grades: [],
  }),
};

ProgramRecord.defaultProps = {
  record: [],
};

export default ProgramRecord;
