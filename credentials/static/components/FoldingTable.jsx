import PropTypes from 'prop-types';
import React from 'react';

import { Table } from '@edx/paragon';

/**
 *  Depending on view width, either renders as a normal everyday
 *  table or as a vertical series of cards.
 */

class FoldingTable extends React.Component {
  renderCards() {
    return this.props.data.map(row => (
      <div className="folding-table-card" key={row[this.props.dataKey]}>
        {this.props.foldedColumns.map(col => (
          <div className={col.className} key={col.key}>
            {col.format ? col.format.replace('{}', row[col.key]) : row[col.key]}
          </div>
        ))}
      </div>
    ));
  }

  renderTable() {
    return (
      <Table
        className={['table-borderless', 'table-responsive']}
        {...this.props}
      />
    );
  }

  render() {
    return (
      <div className="folding-table">
        <div className="folding-table-big">
          {this.renderTable()}
        </div>
        <div className="folding-table-small">
          {this.renderCards()}
        </div>
      </div>
    );
  }
}

FoldingTable.propTypes = {
  data: PropTypes.arrayOf(PropTypes.object).isRequired,
  dataKey: PropTypes.string.isRequired,
  foldedColumns: PropTypes.arrayOf(PropTypes.shape({
    key: PropTypes.string.isRequired,
    format: PropTypes.string,
    className: PropTypes.string,
  })).isRequired,
};

FoldingTable.defaultProps = {
};

export default FoldingTable;
