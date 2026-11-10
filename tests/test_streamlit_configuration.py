from pathlib import Path
import tomllib

import streamlit


ROOT = Path(__file__).resolve().parents[1]


def test_streamlit_configuration_is_valid_and_keeps_light_portal_theme():
    # Parsing catches duplicate TOML sections, which previously disabled theming.
    config = tomllib.loads((ROOT / ".streamlit/config.toml").read_text(encoding="utf-8"))
    assert config["theme"]["base"] == "light"
    assert config["theme"]["primaryColor"] == "#087F8C"
    assert config["theme"]["textColor"] == "#122C50"
    assert config["client"]["toolbarMode"] == "viewer"


def test_cloud_installs_the_same_streamlit_version_used_for_validation():
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
    assert f"streamlit=={streamlit.__version__}" in requirements
