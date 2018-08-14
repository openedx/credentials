Credentials Pull Request
---

Make sure that the following steps are done before rebasing/merging

  - [ ] Request a review if desired
  - [ ] Squash/Fixup your branch to one commit
  - Config/Dependency Changes (e.g. config files, scripts that are used for provisioning etc.)
    - [ ] Make sure you have updated [edx/configuration](https://github.com/edx/configuration) and [edx/devstack](https://github.com/edx/devstack) if necessary
    - [ ] Make sure the change builds successfully in a sandbox
  - UI Changes 
    - [ ] Consider other browsers (e.g. Firefox)
    - [ ] Check mobile view
    - [ ] Consider accessibility (e.g. Run aXe on the page)
