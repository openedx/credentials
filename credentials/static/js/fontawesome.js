// for cherry picking only the icons used in the Credentials UI, so that we don't have to import ALL icons from FA
import { library, dom } from '@fortawesome/fontawesome-svg-core';
import { faFacebook, faTwitter, faLinkedin } from '@fortawesome/free-brands-svg-icons';
import { faPrint } from '@fortawesome/free-solid-svg-icons';

library.add(faFacebook, faTwitter, faLinkedin, faPrint);
dom.watch();
