import os
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = ROOT / ".github/workflows/server-compat.yml"


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        ([], None),
        (["v1.0.0rc1", "v2.0.0.dev1", "v3.0.0PRE1"], None),
        (["v1.9.0", "v1.10.0", "v2.0.0rc1"], "v1.10.0"),
        ([f"v1.0.{number}" for number in range(1500)], "v1.0.1499"),
    ],
)
def test_resolve_latest_tag(tmp_path, tags, expected):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(tmp_path),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.test",
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "initial",
        ],
        check=True,
    )
    commit = subprocess.check_output(
        ["git", "-C", str(tmp_path), "rev-parse", "HEAD"], text=True
    ).strip()
    subprocess.run(
        ["git", "-C", str(tmp_path), "update-ref", "--stdin"],
        input="".join(f"create refs/tags/{tag} {commit}\n" for tag in tags),
        text=True,
        check=True,
    )
    workflow = yaml.safe_load(WORKFLOW.read_text())
    step = workflow["jobs"]["resolve-latest"]["steps"][1]
    output = tmp_path / "output"
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=tmp_path,
        env=os.environ | {"GITHUB_OUTPUT": str(output)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    if expected:
        assert output.read_text() == f"latest_tag={expected}\n"
    else:
        assert not output.exists()


def test_smoke_jobs_require_a_resolved_tag():
    jobs = yaml.safe_load(WORKFLOW.read_text())["jobs"]
    for name in (
        "compat-smoke-config1",
        "compat-smoke-config2",
        "compat-smoke-ui-config-a",
        "compat-smoke-ui-config-b",
    ):
        assert jobs[name]["needs"] == "resolve-latest"
        assert jobs[name]["if"] == "needs.resolve-latest.outputs.latest_tag != ''"


def test_tag_lookup_failure_is_not_ignored(tmp_path):
    step = yaml.safe_load(WORKFLOW.read_text())["jobs"]["resolve-latest"]["steps"][1]
    result = subprocess.run(
        ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", step["run"]],
        cwd=tmp_path,
        env=os.environ | {"GITHUB_OUTPUT": str(tmp_path / "output")},
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
