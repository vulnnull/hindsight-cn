"""`release-tool.sh` must bump the manifest version with the host sed, GNU or BSD.

It used BSD-only `sed -i ''`, which GNU sed reads as an empty script and fails before the bump.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

SOURCE_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("manifest", ["package.json", "pyproject.toml"])
def test_release_tool_updates_version_with_host_sed(tmp_path: Path, manifest: str) -> None:
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    shutil.copy2(SOURCE_ROOT / "scripts" / "release-tool.sh", scripts / "release-tool.sh")
    tool = tmp_path / "hindsight-tools" / "hindsight-agent-sdk"
    tool.mkdir(parents=True)
    old = '{"name": "fixture", "version": "0.1.0"}\n' if manifest == "package.json" else 'version = "0.1.0"\n'
    (tool / manifest).write_text(old)

    # Stub git/npm so the script runs for real but commits, tags, pushes and builds nothing.
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for command, body in (("git", '[ "$1" = branch ] && echo main\nexit 0'), ("npm", "exit 0")):
        stub = bin_dir / command
        stub.write_text(f"#!/bin/sh\n{body}\n")
        stub.chmod(0o755)

    result = subprocess.run(
        ["bash", str(scripts / "release-tool.sh"), "hindsight-agent-sdk", "0.2.0"],
        env=os.environ | {"PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tool / manifest).read_text() == old.replace("0.1.0", "0.2.0")
    assert not list(tool.glob("*.bak"))
