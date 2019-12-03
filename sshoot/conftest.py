from pathlib import Path

import pytest

from .config import Config
from .manager import Manager


@pytest.fixture
def config_dir(tmpdir):
    """A directory for configuration files. """
    path = Path(tmpdir / "config")
    path.mkdir()
    yield path


@pytest.fixture
def config_file(config_dir):
    """The configuration file."""
    yield config_dir / "config.yaml"


@pytest.fixture
def profiles_file(config_dir):
    """A Path for profiles configuration file."""
    yield config_dir / "profiles.yaml"


@pytest.fixture
def config(config_dir):
    """A Config object configured with a temp path."""
    yield Config(config_dir)


@pytest.fixture
def run_dir(tmpdir):
    path = Path(tmpdir / "run")
    path.mkdir()
    yield path


@pytest.fixture
def sessions_dir(run_dir):
    path = run_dir / "sessions"
    path.mkdir()
    yield path


@pytest.fixture
def profile_manager(config_dir, run_dir):
    yield Manager(config_path=config_dir, rundir=run_dir)
