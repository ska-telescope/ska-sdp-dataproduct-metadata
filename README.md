# SKA SDP Data Product Metadata

## Introduction


## Standard CI machinery

The repository is set up to use [CI templates](https://gitlab.com/ska-telescope/templates-repository)
and [makefiles](https://gitlab.com/ska-telescope/sdi/ska-cicd-makefile) maintained by the System Team.

For any questions, please look at the repositories' documentation or ask for support on Slack
in the #team-system-support channel.

To keep the makefile modules up to date locally, follow the instructions at:
https://gitlab.com/ska-telescope/sdi/ska-cicd-makefile#keeping-up-to-date

## Creating a new release

When new release is ready:

  - checkout the master branch
  - create an issue in the [Release Management](https://jira.skatelescope.org/projects/REL/summary) project
  - bump the `.release` file version with
    - `make bump-patch-release`
    - `make bump-minor-release`, or
    - `make bump-major-release`
  - set the python version with `make python-set-release`
  - manually update the versions in
    - `docs/src/conf.py`
    - `ska_sdp_dataproduct_metadata/version.py`
  - create the git tag with `make create-git-tag`
  - push the changes using `make push-git-tag`