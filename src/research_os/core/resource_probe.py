"""Best-effort RAM/VRAM measurement for the local LLM benchmark (spec
section 9/16). No new dependency (no psutil) — shells out to whatever the
OS already provides, and returns None rather than guessing when a value
can't actually be measured. Never raises: a probe failure must not fail
the benchmark run around it.
"""
from __future__ import annotations

import platform
import re
import shutil
import subprocess

from research_os.core.logging_setup import get_logger

logger = get_logger("core.resource_probe")


def process_ram_mb(process_name: str = "ollama") -> float | None:
    """Resident memory of a running process, in MB. Best-effort:
    - Windows: `tasklist /FI "IMAGENAME eq <name>*"`
    - Linux/macOS: `ps -eo comm,rss`
    Returns None if the process isn't found or the tool isn't available —
    this is expected on a machine where Ollama isn't running, and is
    reported as such rather than as a measured 0.
    """
    try:
        system = platform.system()
        if system == "Windows":
            exe = process_name if process_name.endswith(".exe") else f"{process_name}.exe"
            out = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {exe}", "/FO", "CSV", "/NH"],
                capture_output=True, text=True, timeout=5,
            )
            if out.returncode != 0 or "No tasks" in out.stdout:
                return None
            # CSV: "image name","PID","session name","session#","mem usage"
            line = out.stdout.strip().splitlines()[0]
            fields = [f.strip('"') for f in line.split('","')]
            if len(fields) < 5:
                return None
            mem_str = fields[4].replace(",", "").replace(" K", "").strip()
            return round(int(mem_str) / 1024, 1) if mem_str.isdigit() else None
        else:
            if not shutil.which("ps"):
                return None
            out = subprocess.run(["ps", "-eo", "comm,rss"], capture_output=True, text=True, timeout=5)
            total_kb = 0
            found = False
            for line in out.stdout.splitlines()[1:]:
                parts = line.split()
                if len(parts) != 2:
                    continue
                comm, rss = parts
                if process_name in comm:
                    try:
                        total_kb += int(rss)
                        found = True
                    except ValueError:
                        continue
            return round(total_kb / 1024, 1) if found else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("process_ram_mb probe failed: %s", exc)
        return None


def gpu_vram_usage_mb() -> float | None:
    """Best-effort current VRAM usage. Supports nvidia-smi and rocm-smi
    (AMD). Returns None if neither is available — this is expected on the
    target RX 6600 unless ROCm tooling is installed, and must be reported
    as UNKNOWN, not guessed."""
    try:
        if shutil.which("nvidia-smi"):
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5,
            )
            if out.returncode == 0 and out.stdout.strip():
                return float(out.stdout.strip().splitlines()[0])
        if shutil.which("rocm-smi"):
            out = subprocess.run(["rocm-smi", "--showmeminfo", "vram"], capture_output=True, text=True, timeout=5)
            match = re.search(r"Used Memory.*?:\s*(\d+)", out.stdout)
            if match:
                return round(int(match.group(1)) / (1024 * 1024), 1)
    except Exception as exc:  # noqa: BLE001
        logger.warning("gpu_vram_usage_mb probe failed: %s", exc)
    return None
