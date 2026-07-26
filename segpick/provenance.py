from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

from segpick import __version__
from segpick.config import RunConfig
from segpick.models import AnalysisManifest


def _tool_version(command: str) -> str | None:
    path = shutil.which(command)
    if path is None:
        return None
    try:
        proc = subprocess.run([command, "--version"], capture_output=True, text=True, timeout=10, check=False)
    except OSError:
        return None
    text = (proc.stdout or proc.stderr).strip().splitlines()
    return text[0] if text else path


def write_provenance(
    config: RunConfig,
    path: str | Path,
    argv: list[str],
    manifest: AnalysisManifest | None = None,
) -> Path:
    """Write a reproducibility record for the current run."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "segpick_version": __version__,
        "generated_utc": datetime.now(UTC).isoformat(),
        "command": argv,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "minimap2": _tool_version("minimap2"),
        "resolved_config": config.to_dict(),
        "analysis_manifest": manifest.to_dict() if manifest is not None else None,
    }
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path
