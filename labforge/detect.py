"""
Local hardware detection — cross-OS, best-effort, standard library only.

Reports the current machine's CPU/RAM/GPU/VRAM so `fit` can tell you what you can
run today. Mirrors the approach in the Cognis `edgemesh` project's hardware probe;
if edgemesh is importable, labforge will defer to its richer detector (interop).
"""
from __future__ import annotations
import os
import platform
import re
import shutil
import subprocess


def _run(cmd, timeout=8):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.stdout if p.returncode == 0 else ""
    except Exception:
        return ""


def _ram_gb() -> float | None:
    try:
        if hasattr(os, "sysconf") and "SC_PAGE_SIZE" in os.sysconf_names:
            return round(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9, 1)
    except Exception:
        pass
    if platform.system() == "Darwin":
        out = _run(["sysctl", "-n", "hw.memsize"])
        if out.strip().isdigit():
            return round(int(out) / 1e9, 1)
    if platform.system() == "Windows":
        out = _run(["wmic", "ComputerSystem", "get", "TotalPhysicalMemory"])
        m = re.search(r"(\d{6,})", out)
        if m:
            return round(int(m.group(1)) / 1e9, 1)
    return None


def _gpus() -> list[dict]:
    gpus = []
    if shutil.which("nvidia-smi"):
        out = _run(["nvidia-smi", "--query-gpu=name,memory.total",
                    "--format=csv,noheader,nounits"])
        for line in out.strip().splitlines():
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 2 and parts[1].replace(".", "").isdigit():
                gpus.append({"name": parts[0], "vram_gb": round(float(parts[1]) / 1024, 1),
                             "vendor": "nvidia"})
    if platform.system() == "Darwin" and not gpus:
        out = _run(["sysctl", "-n", "machdep.cpu.brand_string"])
        if "Apple" in out:
            gpus.append({"name": out.strip(), "vram_gb": None, "vendor": "apple",
                         "note": "unified memory (Metal)"})
    return gpus


def _arch_family(gpus: list[dict]) -> str:
    sysname = platform.machine().lower()
    if any(g["vendor"] == "apple" for g in gpus):
        return "metal_arm64"
    if any(g["vendor"] == "nvidia" for g in gpus):
        return "cuda13_aarch64" if "aarch64" in sysname or "arm" in sysname else "cuda12_x86"
    if any(g.get("vendor") == "amd" for g in gpus):
        return "rocm_x86"
    return "cpu"


def detect() -> dict:
    """Return this machine's profile. Prefers edgemesh's detector if available."""
    try:
        import edgemesh.hardware as eh  # cognis interop
        if hasattr(eh, "detect"):
            prof = eh.detect()
            prof["_source"] = "edgemesh"
            return prof
    except Exception:
        pass
    gpus = _gpus()
    ram = _ram_gb()
    # usable inference memory: max VRAM, or unified RAM on Apple/unified boxes
    vram = max([g["vram_gb"] for g in gpus if g.get("vram_gb")], default=None)
    inference_memory_gb = vram if vram else ram
    return {
        "_source": "labforge",
        "os": platform.system(), "machine": platform.machine(),
        "cpu": platform.processor() or platform.machine(),
        "ram_gb": ram, "gpus": gpus,
        "inference_memory_gb": inference_memory_gb,
        "arch_family": _arch_family(gpus),
    }
