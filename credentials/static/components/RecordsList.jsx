import PropTypes from 'prop-types';
import React from 'react';
import StringUtils from './Utils';

import MicroMastersIcon from '../images/icons/micromasters.svg';
import XseriesIcon from '../images/icons/xseries.svg';
import ProfessionalIcon from '../images/icons/professional.svg';

class RecordsList extends React.Component {
  static renderEmpty() {
    return (
      <p className="paragraph-grey">{gettext('No records yet. Try enrolling in a program.')}</p>
    );
  }

  static renderFAQ(helpUrl) {
    return (
      <footer className="faq pad-text-block">
        <h3 className="hd-4 text-black">{gettext('Questions about Learner Records?')}</h3>
        { StringUtils.renderDangerousHtml(gettext('To learn more about records you can {openTag} read more in our records help area.{closeTag}'),
            { openTag: `<a href=${helpUrl}>`, closeTag: '</a>' }) }
      </footer>
    );
  }

  static renderProgramIcon(type) {
    const lowerType = type.toLowerCase();
    let icon = false;
    if (lowerType === 'micromasters') {
      icon = MicroMastersIcon;
    } else if (lowerType === 'xseries') {
      icon = XseriesIcon;
    } else if (lowerType === 'professional-certificate') {
      icon = ProfessionalIcon;
    }
    if (icon) {
      // eslint-disable-next-line react/no-danger
      return (<span className="inline-data certificate-icon" aria-hidden="true" dangerouslySetInnerHTML={{ __html: icon }} />);
    }
    return null;
  }

  static renderRows(data) {
    return data.map(row => (
      <li className="record-card" key={row.uuid}>
        <div className="record-container">
          <div className="row">
            <div className="col-md record-data-col">
              <div className="program-title">{row.name}</div>
              <div className="record-data-inline">
                {RecordsList.renderProgramIcon(row.type)}
                <span className="record-partner inline-data">{row.partner}</span>
                <span className="inline-data"> {' | '} </span>
                <span className="font-weight-bold inline-data">{row.progress}</span>
              </div>
            </div>
            <div className="col-md record-btn-col">
              <div className="view-record-container">
                <a href={`/records/programs/${row.uuid}`} className="btn view-record-btn font-weight-bold">
                  {gettext('View Program Record')}
                </a>
              </div>
            </div>
          </div>
        </div>
      </li>
        ),
    );
  }

  static renderResponsiveList(id, title, help, data) {
    return (
      <section id={id} className="responsive-list">
        <header className="pad-text-block">
          <h3 className="hd-3 text-black">{title}</h3>
          <p className="paragraph-grey">{help}</p>
        </header>
        <ul className="list-unstyled">
          {this.renderRows(data)}
        </ul>
      </section>
    );
  }

  render() {
    const { programs, helpUrl } = this.props;
    const hasPrograms = programs.length > 0;
    const hasHelpUrl = helpUrl !== '';
    const hasContent = hasPrograms; // will check for courses when we show those too
    return (
      <main className="record">
        <header className="pad-text-block">
          <h2 className="hd-2 text-black">{
            // Translators: A 'record' here means something like a
            // Translators: transcript -- a list of courses and grades.
            gettext('My Learner Records')
          }</h2>
        </header>
        {hasPrograms &&
          RecordsList.renderResponsiveList(
            'program-records-list',
            gettext('Program Records'),
            gettext('A program record is created once you have earned at least one Verified Certificate in a program.'),
            programs,
          )
        }
        {hasContent || RecordsList.renderEmpty()}
        {hasContent && hasHelpUrl && RecordsList.renderFAQ(helpUrl)}
      </main>
    );
  }
}

RecordsList.propTypes = {
  programs: PropTypes.arrayOf(PropTypes.shape({
    name: PropTypes.string.isRequired,
    partner: PropTypes.string.isRequired,
    uuid: PropTypes.string.isRequired,
    type: PropTypes.string.isRequired,
    progress: PropTypes.string.isRequired,
  })).isRequired,
  helpUrl: PropTypes.string,
};

RecordsList.defaultProps = {
  programs: [],
  helpUrl: '',
};

export default RecordsList;
