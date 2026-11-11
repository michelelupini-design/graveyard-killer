"""Fixtures for the post script: fake network tools, real ffmpeg, built media."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

SCRIPT = Path(__file__).parent.parent / "plugin/skills/graveyard-killer/scripts/post.py"
FAKE = Path(__file__).parent / "fakes/fake_tool.py"
FAKE_NAMES = ("yt-dlp", "gallery-dl", "parakeet-mlx", "mlx_whisper", "whisper-ctranslate2", "uv")


def ffmpeg(*args: str) -> None:
    subprocess.run(["ffmpeg", "-v", "error", "-y", *args], check=True)


@pytest.fixture(scope="session")
def media(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """Small real media files, built once per test session."""
    if not shutil.which("ffmpeg"):
        pytest.skip("ffmpeg is needed to build test media")
    d = tmp_path_factory.mktemp("media")
    # Three scenes of 2 seconds each, with a tone, so there are scene changes and audio.
    ffmpeg(
        "-f", "lavfi", "-i", "color=red:s=1280x720:d=2:r=25",
        "-f", "lavfi", "-i", "color=green:s=1280x720:d=2:r=25",
        "-f", "lavfi", "-i", "color=blue:s=1280x720:d=2:r=25",
        "-f", "lavfi", "-i", "sine=frequency=440:duration=6",
        "-filter_complex", "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]",
        "-map", "[v]", "-map", "3:a", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        str(d / "scenes.mp4"),
    )
    # Twelve half-second scenes in twelve different colours.
    ffmpeg("-f", "lavfi", "-i", "color=black:s=320x240:d=6:r=25,format=rgb24,"
           "geq=r='mod(floor(T*2)*40,256)':g='mod(floor(T*2)*90,256)':b='mod(floor(T*2)*150,256)'",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", str(d / "twelve_scenes.mp4"))
    ffmpeg("-f", "lavfi", "-i", "color=gray:s=640x360:d=4:r=25",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", str(d / "silent.mp4"))
    ffmpeg("-f", "lavfi", "-i", "color=orange:s=640x640", "-frames:v", "1", str(d / "thumb.jpg"))
    # Noise compresses badly, so this JPEG is well over Notion's 5 MiB limit.
    ffmpeg("-f", "lavfi", "-i", "nullsrc=s=4000x4000,geq=random(1)*255:random(2)*255:random(3)*255",
           "-frames:v", "1", "-q:v", "1", str(d / "big_thumb.jpg"))
    for name, color in (("slide1.jpg", "white"), ("slide2.jpg", "black"), ("slide3.jpg", "yellow")):
        ffmpeg("-f", "lavfi", "-i", f"color={color}:s=1080x1350", "-frames:v", "1", str(d / name))
    return {p.stem: p for p in d.iterdir()}


@dataclass
class Run:
    exit_code: int
    output: dict[str, Any]
    calls: list[dict[str, Any]]

    def called(self, tool: str) -> list[list[str]]:
        return [c["argv"] for c in self.calls if c["tool"] == tool]


@pytest.fixture
def post(tmp_path: Path) -> Iterator[Callable[..., Run]]:
    """Run the post script as the agent does, with a scenario for the fake tools."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name in FAKE_NAMES:
        target = bin_dir / name
        shutil.copy(FAKE, target)
        target.chmod(0o755)
    for real in ("ffmpeg", "ffprobe"):
        found = shutil.which(real)
        if found:
            link = bin_dir / Path(found).name
            try:
                link.symlink_to(found)
            except OSError:
                # Windows makes symlinks only with Developer Mode or admin rights.
                shutil.copy(found, link)
    log = tmp_path / "calls.jsonl"

    def run(
        *args: str,
        scenario: dict[str, Any] | None = None,
        without: tuple[str, ...] = (),
        stdin: str = "",
        env: dict[str, str] | None = None,
    ) -> Run:
        for name in without:
            (bin_dir / name).unlink(missing_ok=True)
        scenario_file = tmp_path / "scenario.json"
        scenario_file.write_text(json.dumps(scenario or {}))
        log.write_text("")
        temp = tmp_path / "temp"  # work folders land here, inside pytest's own cleaned-up folder
        temp.mkdir(exist_ok=True)
        full_env = {
            **os.environ,
            "TMPDIR": str(temp),
            **(env or {}),
            "PATH": os.pathsep.join([str(bin_dir), str(Path(sys.executable).parent)]),
            "GK_FAKE_SCENARIO": str(scenario_file),
            "GK_FAKE_LOG": str(log),
        }
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *args], input=stdin, capture_output=True, text=True, env=full_env
        )
        assert result.stdout, result.stderr
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        return Run(result.returncode, json.loads(result.stdout), calls)

    yield run
