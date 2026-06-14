"""
Compatibility matrix: will inference stack X run on architecture Y?

This encodes the toolchain traps that bite homelab/AI builders — the ones the
DARQ-IR-001 analysis flagged (prebuilt vLLM/flash-attn wheels target CUDA 12.x
x86 and fail on the GB10's sm_121 / CUDA 13 / aarch64), plus ROCm maturity,
Apple Metal, and Vulkan/CPU fallbacks.

Status: "ok" | "partial" | "unsupported".
"""
from __future__ import annotations

# architecture families a machine can present
ARCHS = [
    "cuda12_x86",     # RTX 40/50 + CUDA 12.x on x86 — the mature path
    "cuda13_aarch64", # GB10 / Jetson Thor — sm_121 / CUDA 13 / arm64
    "rocm_x86",       # AMD Radeon / Strix Halo
    "metal_arm64",    # Apple Silicon
    "cpu",            # CPU-only fallback
]

# stack -> {arch: (status, note)}
MATRIX = {
    "ollama": {
        "cuda12_x86": ("ok", "First-class."),
        "cuda13_aarch64": ("ok", "Ships arm64 builds; bundles its own llama.cpp."),
        "rocm_x86": ("ok", "ROCm builds supported."),
        "metal_arm64": ("ok", "Native Metal."),
        "cpu": ("ok", "Falls back to CPU."),
    },
    "llama.cpp": {
        "cuda12_x86": ("ok", "CUDA backend."),
        "cuda13_aarch64": ("ok", "Build from source for CUDA 13/arm64; well supported."),
        "rocm_x86": ("ok", "HIP/ROCm or Vulkan backend."),
        "metal_arm64": ("ok", "Metal backend (and the basis for MLX-adjacent flows)."),
        "cpu": ("ok", "Optimized CPU backend."),
    },
    "vllm": {
        "cuda12_x86": ("ok", "Primary target; prebuilt wheels."),
        "cuda13_aarch64": ("partial", "TRAP: prebuilt wheels target CUDA 12.x x86; "
                           "needs source build against CUDA 13/arm64 — flash-attn often "
                           "the blocker. Plan build time."),
        "rocm_x86": ("partial", "ROCm fork/build exists; less mature."),
        "metal_arm64": ("unsupported", "No Metal backend."),
        "cpu": ("partial", "CPU backend exists but slow."),
    },
    "tensorrt-llm": {
        "cuda12_x86": ("ok", "NVIDIA-optimized."),
        "cuda13_aarch64": ("partial", "Supported on Grace-Blackwell but version-sensitive."),
        "rocm_x86": ("unsupported", "NVIDIA-only."),
        "metal_arm64": ("unsupported", "NVIDIA-only."),
        "cpu": ("unsupported", "GPU-only."),
    },
    "onnxruntime": {
        "cuda12_x86": ("ok", "CUDA execution provider."),
        "cuda13_aarch64": ("partial", "CUDA EP on arm64 needs a matching build."),
        "rocm_x86": ("partial", "ROCm/MIGraphX EP."),
        "metal_arm64": ("partial", "CoreML EP."),
        "cpu": ("ok", "Strong CPU EP."),
    },
    "exllamav2": {
        "cuda12_x86": ("ok", "CUDA."),
        "cuda13_aarch64": ("partial", "Source build."),
        "rocm_x86": ("partial", "ROCm community support."),
        "metal_arm64": ("unsupported", "CUDA-oriented."),
        "cpu": ("unsupported", ""),
    },
    "mlx": {
        "cuda12_x86": ("unsupported", "Apple-only."),
        "cuda13_aarch64": ("unsupported", "Apple-only."),
        "rocm_x86": ("unsupported", "Apple-only."),
        "metal_arm64": ("ok", "Apple's native array/LLM framework."),
        "cpu": ("partial", "Runs but Metal is the point."),
    },
}


def check(stack: str, arch: str) -> dict:
    s = MATRIX.get((stack or "").lower())
    if not s:
        return {"stack": stack, "arch": arch, "status": "unknown",
                "note": f"unknown stack; known: {', '.join(MATRIX)}"}
    status, note = s.get(arch, ("unknown", f"unknown arch; known: {', '.join(ARCHS)}"))
    return {"stack": stack, "arch": arch, "status": status, "note": note}


def stacks_for(arch: str) -> list[dict]:
    return [{"stack": k, **{"status": v.get(arch, ("unknown", ""))[0],
                            "note": v.get(arch, ("", ""))[1]}}
            for k, v in MATRIX.items()]


def matrix() -> dict:
    return {k: {a: {"status": v[a][0], "note": v[a][1]} for a in v} for k, v in MATRIX.items()}
