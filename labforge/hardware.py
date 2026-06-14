"""
labforge hardware catalog.

A structured, AI/dev-relevant catalog of the compute hardware you'd actually
consider for a homelab or shared dev/AI lab: discrete GPUs, unified-memory AI
boxes, APU mini-PCs, edge SBCs, and the memory market. Each entry carries the
specs that decide what you can run — memory capacity (loads the model at all),
memory bandwidth (single-stream token speed), compute architecture (toolchain
compatibility), TDP, and a June-2026 price band reflecting the DRAM/GDDR7 shortage.

Seed data is grounded in current vendor figures (see SOURCES.md); the catalog is
extensible — `data/catalog.json` is merged over the seed at import.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Optional
import json
import os

TOOL_NAME = "labforge"
TOOL_VERSION = "0.1.0"

KINDS = ["gpu", "unified_box", "apu_mini_pc", "sbc_edge", "memory", "workstation"]


@dataclass
class Component:
    key: str
    name: str
    kind: str
    memory_gb: Optional[float] = None     # VRAM (gpu) or unified memory (box/apu)
    bandwidth_gbs: Optional[float] = None  # memory bandwidth, GB/s
    arch: str = ""                         # e.g. "sm_120 / CUDA 12.8 (Blackwell, x86)"
    tdp_w: Optional[int] = None
    price_low: Optional[int] = None
    price_high: Optional[int] = None
    ai_notes: str = ""                     # what it runs
    compat_notes: str = ""                 # toolchain / OS / wheel traps
    sources: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def price_band(self) -> str:
        if self.price_low and self.price_high:
            return f"${self.price_low:,}-${self.price_high:,}"
        if self.price_low:
            return f"~${self.price_low:,}"
        return "n/a"


# --- seed catalog (June 2026, DRAM/GDDR7 shortage in effect) ----------------
_SEED: list[Component] = [
    Component("rtx_5090", "NVIDIA RTX 5090", "gpu", 32, 1792,
              "sm_120 / CUDA 12.8+ (Blackwell, x86 PCIe)", 575, 2910, 4900,
              "Fastest single-stream local inference per dollar; 32GB runs up to ~32B "
              "dense or larger MoE at 4-bit; pair multiples for 70B+.",
              "Mature x86 CUDA toolchain; needs CUDA 12.8+ / recent drivers for sm_120. "
              "Power + PSU (≥1000W) and case clearance are the practical constraints.",
              ["https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/"]),
    Component("rtx_4090", "NVIDIA RTX 4090 (used)", "gpu", 24, 1008,
              "sm_89 / CUDA 12.x (Ada, x86 PCIe)", 450, 1600, 2200,
              "Still excellent for ≤32B at 4-bit; the value used-market AI GPU.",
              "Most mature CUDA target; everything has prebuilt wheels for it.",
              []),
    Component("rtx_5080", "NVIDIA RTX 5080", "gpu", 16, 960,
              "sm_120 / CUDA 12.8+ (Blackwell, x86)", 360, 1100, 1800,
              "16GB runs ≤13B at fp16, 34B at q4; strong mid-tier single-card.",
              "Use CUDA 12.9.1+ / cu128 image to avoid a PTX-JIT issue on 12.8.", []),
    Component("rtx_5070_ti", "NVIDIA RTX 5070 Ti", "gpu", 16, 896,
              "sm_120 / CUDA 12.8+ (Blackwell, x86)", 300, 880, 1200,
              "Same 16GB ceiling as the 5080 at lower compute; ≤32B at q4.",
              "sm_120 / PyTorch 2.7+.", []),
    Component("rtx_5070", "NVIDIA RTX 5070", "gpu", 12, 672,
              "sm_120 / CUDA 12.8+ (Blackwell, x86)", 250, 600, 700,
              "12GB: 7B fp16 / 13B q6 / 34B q4 with some CPU offload.",
              "sm_120; 750W PSU.", []),
    Component("rtx_5060_ti_16g", "NVIDIA RTX 5060 Ti (16GB)", "gpu", 16, 448,
              "sm_120 / CUDA 12.8+ (Blackwell, x86, PCIe x8)", 180, 429, 610,
              "Cheapest 16GB Blackwell: fits 13B fp16 / 34B q4; narrow 128-bit bus "
              "so slower tok/s — a capacity-over-speed budget pick.",
              "Single 8-pin; fits compact builds.", []),
    Component("rtx_pro_6000_blackwell", "NVIDIA RTX PRO 6000 Blackwell (96GB)", "gpu",
              96, 1792, "sm_120 / CUDA 12.8+ (Blackwell workstation, x86)", 600, 8000, 9200,
              "Single-card 96GB loads 70B at 8-bit or 120B-class MoE at 4-bit on one GPU.",
              "x86 CUDA; near whole-budget cost during the shortage.", []),
    Component("dgx_spark", "NVIDIA DGX Spark (GB10 Founders)", "unified_box", 128, 273,
              "GB10 Grace-Blackwell, sm_121 / CUDA 13 / aarch64", 240, 3999, 4699,
              "128GB unified loads 120B-class MoE (gpt-oss-120B MXFP4 ~38-50 tok/s "
              "single-stream); link two via ConnectX-7 to pool 256GB for 405B FP4.",
              "TRAP: sm_121/CUDA13/aarch64 — many prebuilt wheels (vLLM, flash-attn) "
              "target CUDA 12.x x86 and fail; unified-memory swap can freeze under OOM "
              "(disable swap before serving). Develop-to-deploy parity with GB200.",
              ["https://www.nvidia.com/en-us/products/workstations/dgx-spark/"]),
    Component("gb10_partners", "GB10 partner units (MSI EdgeXpert / ASUS Ascent GX10 / Dell Pro Max GB10)",
              "unified_box", 128, 273, "GB10 Grace-Blackwell, sm_121 / CUDA 13 / aarch64",
              240, 2999, 4658,
              "Identical GB10 chip + performance as DGX Spark; chassis/SSD/thermals differ.",
              "Same aarch64/CUDA13 software-maturity caveat as the Spark.", []),
    Component("jetson_thor", "NVIDIA Jetson AGX Thor Dev Kit", "unified_box", 128, 273,
              "Blackwell, CUDA 13 / aarch64 (robotics I/O)", 130, 3499, 3499,
              "Same 128GB/273GB/s memory class as Spark; robotics-oriented I/O.",
              "Redundant alongside a Spark for pure LLM work (DARQ-IR-001 §). aarch64.",
              []),
    Component("jetson_orin_nano", "NVIDIA Jetson Orin Nano Super", "sbc_edge", 8, 102,
              "Ampere, CUDA / aarch64", 25, 249, 299,
              "Edge inference node for small models (≤8B 4-bit), vision, always-on agents.",
              "aarch64; great low-power homelab edge/control node.", []),
    Component("mac_studio_m3_ultra", "Apple Mac Studio M3 Ultra (256GB)", "unified_box",
              256, 819, "Apple M3 Ultra, Metal (arm64)", 270, 5500, 6500,
              "256GB unified runs very large models via MLX/llama.cpp; 512GB tier "
              "discontinued Mar 2026.",
              "Metal backend (MLX, llama.cpp Metal); no CUDA — vLLM/TensorRT not "
              "applicable. Excellent perf-per-watt and bandwidth.", []),
    Component("strix_halo_395", "AMD Ryzen AI Max+ 395 (Strix Halo) mini-PC", "apu_mini_pc",
              128, 256, "AMD RDNA3.5 iGPU + XDNA2 NPU, ROCm / Vulkan (x86)", 120, 1800, 2500,
              "Up to 128GB unified at ~256GB/s in a mini-PC; runs 70B-class at 4-bit; "
              "the x86 low-power alternative to a Spark.",
              "ROCm maturity is improving but trails CUDA; llama.cpp Vulkan/ROCm is the "
              "reliable path. No CUDA-only stacks.", []),
    Component("ddr5_64gb_kit", "DDR5-6000 64GB kit", "memory", 64, None,
              "DDR5 UDIMM", None, 700, 1400,
              "Principal build-cost driver during the shortage (was ~$200 pre-2025).",
              "LOCK price at purchase: DDR5/GDDR7/NAND shortage forecast +130-400% "
              "through end-2026, persisting into H2 2027. Memory deferred = more $$, not less.",
              []),
]

_BY_KEY: dict[str, Component] = {}


def _load() -> None:
    _BY_KEY.clear()
    for c in _SEED:
        _BY_KEY[c.key] = c
    # merge optional external catalog (research-expanded) over the seed
    path = os.path.join(os.path.dirname(__file__), "..", "data", "catalog.json")
    if os.path.exists(path):
        try:
            for d in json.load(open(path, encoding="utf-8")):
                _BY_KEY[d["key"]] = Component(**{k: v for k, v in d.items()
                                                 if k in Component.__annotations__})
        except Exception:
            pass


_load()


def catalog(kind: Optional[str] = None) -> list[Component]:
    items = list(_BY_KEY.values())
    return [c for c in items if c.kind == kind] if kind else items


def get(key: str) -> Optional[Component]:
    return _BY_KEY.get((key or "").lower())


def add(component: Component) -> None:
    _BY_KEY[component.key] = component
