import tomllib
from pathlib import Path


def test_package_imports() -> None:
    import agades_pqc_gym

    assert agades_pqc_gym.__version__ == "0.1.0"


def test_project_metadata_uses_pqc_naming() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text())

    assert metadata["project"]["name"] == "agades-pqc-gym"
    assert metadata["project"]["scripts"] == {
        "agades-pqc": "agades_pqc_gym.cli:app"
    }


def test_package_data_includes_all_public_reproduction_fixture_families() -> None:
    metadata = tomllib.loads(Path("pyproject.toml").read_text())

    assert metadata["tool"]["setuptools"]["package-data"]["agades_pqc_gym"] == [
        "families/code_based/fixtures/*.json",
        "families/hash_based/fixtures/*.json",
        "families/implementation_security/fixtures/*.json",
        "families/isogeny_historical/fixtures/*.json",
        "families/lattice/fixtures/*.json",
        "families/multivariate/fixtures/*.json",
        "formal/resources/docs/*.json",
        "formal/resources/formal/lean/*",
        "formal/resources/formal/lean/AgadesPQC/*.lean",
        "formal/resources/formal/lean/AgadesPQC/*/*.lean",
    ]
