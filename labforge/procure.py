"""
Procurement planner: budget + workload + team size -> a recommended build (BoM),
shortage-aware, in the spirit of the DARQ-IR-001 acquisition analysis.

Key principles encoded here:
- Shared central rigs beat per-seat rigs on capital efficiency when the workload is
  large-model inference (3-4 devs hit one rig over SSH/JupyterHub/VS Code Remote).
- Capacity decides what loads; bandwidth decides speed; MoE softens bandwidth.
- During the DRAM/GDDR7 shortage, lock memory-bearing purchases at approval time.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from . import hardware, fit

WORKLOADS = {
    "starter": "Learn / run small models (≤8-14B) locally.",
    "inference_small": "Serve up to ~32B dense / small MoE for a person or two.",
    "inference_large": "Serve 70B-120B-class (incl. MoE) open-weight models.",
    "cuda_dev": "Heavy CUDA/Rust dev loop (compile-test-profile) needing mature x86 CUDA + bandwidth.",
    "shared_team": "Central shared rig for 3-4 devs doing large-model inference + dev.",
}


@dataclass
class Build:
    workload: str
    budget_usd: int
    devs: int
    bom: list = field(default_factory=list)     # [{component, qty, est_cost}]
    total_low: int = 0
    total_high: int = 0
    rationale: str = ""
    runs: str = ""
    notes: list = field(default_factory=list)

    def to_dict(self):
        d = vars(self).copy()
        d["bom"] = [{"component": b["component"].name, "key": b["component"].key,
                     "qty": b["qty"], "price_band": b["component"].price_band}
                    for b in self.bom]
        return d


def _line(key, qty=1):
    c = hardware.get(key)
    return {"component": c, "qty": qty} if c else None


def recommend(budget_usd: int, workload: str = "shared_team", devs: int = 1) -> Build:
    b = Build(workload=workload, budget_usd=budget_usd, devs=max(1, devs))
    bom = []

    if workload == "starter" or budget_usd < 2500:
        bom = [_line("rtx_4090")] if budget_usd >= 1800 else [_line("strix_halo_395")]
        b.rationale = ("Single value GPU or a unified-memory mini-PC. A used RTX 4090 "
                       "(24GB, mature CUDA) is the best learning/dev GPU per dollar; a "
                       "Strix Halo 395 mini-PC trades speed for 128GB unified at low power.")
    elif workload in ("inference_large", "shared_team") and budget_usd >= 9000:
        # DARQ-IR-001 Config B: a unified-memory box for capacity + a discrete GPU for
        # bandwidth/mature toolchain — complementary, not overlapping.
        bom = [_line("dgx_spark"), _line("rtx_5090"), _line("ddr5_64gb_kit", 1)]
        b.rationale = ("Config-B pairing (DARQ-IR-001): a GB10 unified-memory box "
                       "(128GB) loads 120B-class MoE models; a discrete RTX 5090 "
                       "(1,792 GB/s, mature x86 CUDA) carries the dev loop and fast "
                       "single-stream inference. Shared by the team over the network — "
                       f"~${(budget_usd // max(1, devs)):,}/seat-equivalent.")
        b.notes.append("aarch64/CUDA13 wheel traps apply to the GB10 box — see `labforge compat`.")
    elif workload == "cuda_dev" or (budget_usd >= 3000 and workload == "inference_small"):
        bom = [_line("rtx_5090")]
        b.rationale = ("A single RTX 5090: maximum bandwidth + the most mature x86 CUDA "
                       "toolchain for a compile-test-profile dev loop.")
    elif budget_usd >= 4000:
        bom = [_line("dgx_spark")]
        b.rationale = ("A GB10 unified-memory box: 128GB loads 120B-class MoE on one "
                       "unit; best capacity-per-dollar for large-model inference.")
    else:
        bom = [_line("rtx_5090")] if budget_usd >= 3000 else [_line("rtx_4090")]
        b.rationale = "Best single-GPU fit within budget."

    b.bom = [x for x in bom if x]
    b.total_low = sum((x["component"].price_low or 0) * x["qty"] for x in b.bom)
    b.total_high = sum((x["component"].price_high or x["component"].price_low or 0) * x["qty"]
                       for x in b.bom)
    # what it runs: use the largest-memory component
    mem = max([(x["component"].memory_gb or 0) for x in b.bom], default=0)
    bw = max([(x["component"].bandwidth_gbs or 0) for x in b.bom], default=0)
    runnable = [r for r in fit.fits(mem, bw, quant="q4") if r.fits]
    b.runs = runnable[-1].model if runnable else "small models"
    b.notes.append("DRAM/GDDR7 shortage: lock memory-bearing line items at approval — "
                   "prices forecast +130-400% through end-2026.")
    if b.total_low > budget_usd:
        b.notes.append(f"WARNING: low estimate ${b.total_low:,} exceeds budget ${budget_usd:,}.")
    return b
