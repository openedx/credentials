import PropTypes from 'prop-types';
import React from 'react';

import ProgramIcon from './ProgramIcon';
import RecordsHelp from './RecordsHelp';

class RecordsList extends React.Component {
  static renderEmpty() {
    return (
      <p className="paragraph-grey pad-text-block">{gettext('No records yet. Program records are created once you have earned at least one course certificate in a program.')}</p>
    );
  }

  static renderProfile(profileUrl) {
    return (
      <a href={profileUrl} className="top-bar-link flex-4 pad-text-block">
        <span className="fa fa-caret-left" aria-hidden="true" />
        <span className="fa fa-caret-right" aria-hidden="true" /> {gettext('Back to My Profile')}
      </a>
    );
  }

  static renderRows(data, icons) {
    return data.map(row => (
      <li className="record-card" key={row.uuid}>
        <div className="record-container">
          <div className="row">
            <div className="col-md record-data-col">
              <div className="program-title">{row.name}</div>
              <div className="record-data-inline">
                <ProgramIcon type={row.type} iconDict={icons} className="inline-data certificate-icon" />
                <span className="record-partner inline-data">{row.partner}</span>
                { row.empty || <span className="inline-data"> {' | '} </span>}
                { row.empty ||
                  <span className="font-weight-bold inline-data">{
                    row.completed ? gettext('Completed') : gettext('Partially Completed')
                  }</span>
                }
              </div>
            </div>
            <div className="col-md-3 record-btn-col">
              <div className="view-record-container">
                <a href={'/records/programs/' + row.uuid + '/'} className="btn view-record-btn font-weight-bold">
                  {row.empty ? gettext('View Example') : gettext('View Program Record')}
                </a>
              </div>
            </div>
          </div>
        </div>
      </li>
        ),
    );
  }

  static renderResponsiveList(id, title, help, data, icons) {
    return (
      <section id={id} className="responsive-list">
        <header className="pad-text-block">
          <h3 className="h4 text-black">{title}</h3>
          <p className="paragraph-grey">{help}</p>
        </header>
        <ul className="list-unstyled">
          {this.renderRows(data, icons)}
        </ul>
      </section>
    );
  }

  render() {
    const { programs, helpUrl, profileUrl, icons } = this.props;
    const hasPrograms = programs.length > 0;
    const hasHelpUrl = helpUrl !== '';
    const hasProfileUrl = profileUrl !== '';
    const hasContent = hasPrograms; // will check for courses when we show those too
    return (
      <main id="main-content" className="record" tabIndex="-1">
        {hasProfileUrl && RecordsList.renderProfile(profileUrl)}
        <header className="pad-text-block">
          <h2 className="h3 mb-4 text-black">{this.props.title}</h2>
        </header>
        {hasPrograms &&
          RecordsList.renderResponsiveList(
            'program-records-list',
            gettext('Program Records'),
            this.props.programHelp,
            programs,
            icons,
          )
        }
        {hasContent || RecordsList.renderEmpty()}
        {hasHelpUrl && <RecordsHelp helpUrl={helpUrl} />}
      </main>
    );
  }
}

RecordsList.propTypes = {
  title: PropTypes.string,
  programs: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    partner: PropTypes.string.isRequired,
    uuid: PropTypes.string.isRequired,
    type: PropTypes.string.isRequired,
    completed: PropTypes.bool.isRequired,
    empty: PropTypes.bool.isRequired,
  })).isRequired,
  programHelp: PropTypes.string,
  helpUrl: PropTypes.string,
  profileUrl: PropTypes.string,
  icons: PropTypes.shape(),
};

RecordsList.defaultProps = {
  title: '',
  programs: [],
  programHelp: '',
  helpUrl: '',
  profileUrl: '',
  icons: {},
};

export default RecordsList;
