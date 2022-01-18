# Copyright Contributors to the Packit project.
# SPDX-License-Identifier: MIT

from logging import getLogger

import pytest
from flexmock import flexmock

from packit.actions import ActionName
from packit.config.package_config import PackageConfig
from packit.distgit import DistGit
from packit.utils.changelog_helper import ChangelogHelper

logger = getLogger(__name__)


@pytest.fixture
def package_config():
    yield PackageConfig()


@pytest.fixture
def upstream(upstream_instance):
    _, ups = upstream_instance
    yield ups


@pytest.fixture
def downstream():
    yield flexmock(DistGit)


def test_srpm_action(upstream, downstream):
    package_config = upstream.package_config
    package_config.actions = {
        ActionName.changelog_entry: [
            "echo - hello from test_srpm_action   ",
        ]
    }

    ChangelogHelper(upstream, downstream, package_config).prepare_upstream_locally(
        "0.1.0", "abc123a", True, None
    )
    assert "- hello from test_srpm_action" in upstream._specfile.spec_content.section(
        "%changelog"
    )


def test_srpm_commits(upstream, downstream):
    package_config = upstream.package_config
    ChangelogHelper(upstream, downstream, package_config).prepare_upstream_locally(
        "0.1.0", "abc123a", True, None
    )
    assert (
        "- Development snapshot (abc123a)"
        in upstream._specfile.spec_content.section("%changelog")
    )


def test_srpm_no_tags(upstream, downstream):
    package_config = upstream.package_config
    flexmock(upstream).should_receive("get_last_tag").and_return(None).once()

    ChangelogHelper(upstream, downstream, package_config).prepare_upstream_locally(
        "0.1.0", "abc123a", True, None
    )
    assert (
        "- Development snapshot (abc123a)"
        in upstream._specfile.spec_content.section("%changelog")
    )


def test_srpm_no_bump(upstream, downstream):
    package_config = upstream.package_config
    flexmock(upstream).should_receive("get_last_tag").and_return(None).once()

    ChangelogHelper(upstream, downstream, package_config).prepare_upstream_locally(
        "0.1.0", "abc123a", False, None
    )
    assert (
        "- Development snapshot (abc123a)"
        not in upstream._specfile.spec_content.section("%changelog")
    )


def test_update_distgit_when_copy_upstream_release_description(
    upstream, distgit_instance
):
    _, downstream = distgit_instance
    package_config = upstream.package_config
    package_config.copy_upstream_release_description = True
    upstream.local_project.git_project = (
        flexmock()
        .should_receive("get_release")
        .with_args(tag_name="0.1.0", name="0.1.0")
        .and_return(flexmock(body="Some release 0.1.0"))
        .mock()
    )

    ChangelogHelper(upstream, downstream, package_config).update_dist_git(
        upstream_tag="0.1.0", full_version="0.1.0"
    )

    assert "Some release 0.1.0" in downstream._specfile.spec_content.section(
        "%changelog"
    )