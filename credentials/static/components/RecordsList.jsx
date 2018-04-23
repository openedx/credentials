import PropTypes from 'prop-types';
import React from 'react';

import { Button } from '@edx/paragon';

import FoldingTable from './FoldingTable';

class RecordsList extends React.Component {
  static convertPropsDataToTableData(propsData) {
    return propsData.map(x => ({
      ...x,
      button: RecordsList.renderProgramButton(x.uuid),
    }));
  }

  static renderEmpty() {
    return (
      <p>No records yet. Try enrolling in a program.</p>
    );
  }

  static renderFAQ() {
    return (
      <footer className="faq">
        <h3 className="hd-3">FAQ</h3>
        <ul>
          <li>
            <a href="/help/who">Who can I share this with?</a>
          </li>
          <li>
            <a href="/help/what">What will they be able to see when I share it?</a>
          </li>
          <li>
            <a href="/help/stop">Can I stop sharing with someone after I’ve shared with them?</a>
          </li>
        </ul>
      </footer>
    );
  }

  static renderProgramButton(uuid) {
    const link = `/records/programs/${uuid}`;
    return (
      <a href={link}>
        <Button label="View Program Record" className={['btn', 'block']} />
      </a>
    );
  }

  static renderRecordsList(id, title, help, data) {
    return (
      <section id={id}>
        <header>
          <h3 className="hd-3">{title}</h3>
          <p>{help}</p>
        </header>
        <FoldingTable
          columns={[
            { key: 'name', label: 'Program Name' },
            { key: 'partner', label: 'School' },
            { key: 'button', label: 'Record Link', hideHeader: true },
          ]}
          foldedColumns={[
            { key: 'name', className: 'hd-5 emphasized' },
            { key: 'partner' },
            { key: 'button' },
          ]}
          data={data}
          dataKey="uuid"
        />
        <hr />
      </section>
    );
  }

  constructor(props) {
    super(props);
    this.state = {
      programs: RecordsList.convertPropsDataToTableData(this.props.programs),
    };
  }

  renderPrograms() {
    return RecordsList.renderRecordsList(
      'program-records',
      'Program Records',
      'Here you’ll see programs in which you have certificates.',
      this.state.programs,
    );
  }

  render() {
    const hasPrograms = this.state.programs.length > 0;
    const hasContent = hasPrograms; // will check for courses when we show those too
    return (
      <main className="record">
        <header>
          <h2 className="hd-2">My Records</h2>
        </header>
        {hasPrograms && this.renderPrograms()}
        {hasContent || RecordsList.renderEmpty()}
        {hasContent && RecordsList.renderFAQ()}
      </main>
    );
  }
}

RecordsList.propTypes = {
  programs: PropTypes.arrayOf(PropTypes.object),
};

RecordsList.defaultProps = {
  programs: [],
};

export default RecordsList;
