"""Best-effort, dependency-free environment inspection (spec section 47).

Used by `research-os status`. Works cross-platform without adding a
dependency like psutil; falls back to "unknown" rather than raising, since
this is diagnostic information, not something the pipeline depends on.
"""
from __future__ import annotations

import os
import platform
import shutil
import subprocess


def cpu_info() -> str:
    return f"{platform.processor() or platform.machine()} ({os.cpu_count()} logical cores)"


def ram_info_gb() -> float | None:
    try:
        if platform.system() == "Linux":
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return round(kb / (1024 * 1024), 1)
        elif platform.system() == "Windows":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))  # type: ignore[attr-defined]
            return round(stat.ullTotalPhys / (1024**3), 1)
        elif platform.system() == "Darwin":
            out = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=3)
            return round(int(out.stdout.strip()) / (1024**3), 1)
    except Exception:  # noqa: BLE001
        return None
    return None


def gpu_info() -> str:
    if shutil.which("nvidia-smi"):
        try:
            out = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=3,
            )
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.strip().splitlines()[0]
        except Exception:  # noqa: BLE001
            pass
    if shutil.which("rocm-smi"):
        return "AMD ROCm GPU detected (rocm-smi present)"
    if platform.system() == "Windows":
        try:
            out = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name"],
                capture_output=True, text=True, timeout=5,
            )
            lines = [ln.strip() for ln in out.stdout.splitlines() if ln.strip() and "Name" not in ln]
            if lines:
                return ", ".join(lines)
        except Exception:  # noqa: BLE001
            pass
    return "unknown (no nvidia-smi/rocm-smi/wmic detected on this machine)"


def disk_free_gb(path: str = ".") -> float | None:
    try:
        usage = shutil.disk_usage(path)
        return round(usage.free / (1024**3), 1)
    except Exception:  # noqa: BLE001
        return None


def python_version() -> str:
    return platform.python_version()


def os_info() -> str:
    return f"{platform.system()} {platform.release()}"


def summary() -> dict:
    return {
        "os": os_info(),
        "python": python_version(),
        "cpu": cpu_info(),
        "ram_gb": ram_info_gb(),
        "gpu": gpu_info(),
        "disk_free_gb": disk_free_gb(),
    }
