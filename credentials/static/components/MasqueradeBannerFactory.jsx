// TODO: We should be able to remove this as part of https://github.com/openedx/credentials/issues/1722
import React from 'react';
import ReactDOM from 'react-dom';

import MasqueradeBanner from './MasqueradeBanner';

function MasqueradeBannerFactory(parent, props) {
  ReactDOM.render(
    React.createElement(MasqueradeBanner, props, null),
    document.getElementById(parent),
  );
}

export { MasqueradeBannerFactory }; // eslint-disable-line import/prefer-default-export
