"""
Model-fit engine: given a machine's memory + bandwidth, what models can it run and
roughly how fast?

Two physics-grounded rules of thumb (the same ones the DARQ-IR-001 analysis turns
on): memory CAPACITY decides whether a model loads at all; memory BANDWIDTH decides
single-stream token-generation speed. Mixture-of-experts (MoE) models read only
their *active* parameters per token, which is why 128GB/273GB/s boxes serve
120B-class MoE models at usable speeds despite modest bandwidth.
"""
from __future__ import annotations
from dataclasses import dataclass

# bytes per parameter by quantization
QUANT_BYTES = {"fp16": 2.0, "int8": 1.0, "q5": 0.65, "q4": 0.5, "mxfp4": 0.5, "int4": 0.5}

# representative models: (name, total_params_B, active_params_B [=total if dense])
MODELS = [
    ("Llama 3.1 8B", 8, 8),
    ("Qwen3 14B", 14, 14),
    ("Gemma 3 27B", 27, 27),
    ("Llama 3.3 70B", 70, 70),
    ("Qwen3 235B-A22B (MoE)", 235, 22),
    ("gpt-oss-120B (MoE)", 120, 5.1),
    ("Llama 4 Maverick 400B (MoE)", 400, 17),
    ("DeepSeek-V3 671B (MoE)", 671, 37),
]


@dataclass
class FitResult:
    model: str
    quant: str
    weights_gb: float
    fits: bool
    est_tok_s: float | None     # single-stream, bandwidth-bound estimate
    note: str = ""

    def to_dict(self): return vars(self)


def weights_gb(total_params_b: float, quant: str) -> float:
    return round(total_params_b * QUANT_BYTES.get(quant, 0.5), 1)


def active_gb(active_params_b: float, quant: str) -> float:
    return active_params_b * QUANT_BYTES.get(quant, 0.5)


def est_tok_s(bandwidth_gbs: float | None, active_params_b: float, quant: str) -> float | None:
    """Single-stream generation is ~ memory-bound: tok/s ~= bandwidth / active-weight-bytes.
    A 0.7 efficiency factor approximates real-world overhead. Rough, order-of-magnitude."""
    if not bandwidth_gbs:
        return None
    ag = active_gb(active_params_b, quant)
    if ag <= 0:
        return None
    return round(0.7 * bandwidth_gbs / ag, 1)


def fits(memory_gb: float | None, bandwidth_gbs: float | None = None,
         quant: str = "q4", overhead: float = 1.2) -> list[FitResult]:
    """For each representative model, does it load on `memory_gb` (with a KV-cache/
    runtime overhead factor) and roughly how fast at `quant`?"""
    out = []
    for name, total, active in MODELS:
        w = weights_gb(total, quant)
        need = w * overhead
        ok = memory_gb is not None and need <= memory_gb
        spd = est_tok_s(bandwidth_gbs, active, quant) if ok else None
        note = ""
        if total != active:
            note = f"MoE: {active}B active of {total}B"
        out.append(FitResult(name, quant, w, ok, spd, note))
    return out


def fit_component(component, quant: str = "q4") -> list[FitResult]:
    return fits(getattr(component, "memory_gb", None),
                getattr(component, "bandwidth_gbs", None), quant)


def largest_fit(memory_gb: float | None, quant: str = "q4") -> str:
    runnable = [r for r in fits(memory_gb, quant=quant) if r.fits]
    return runnable[-1].model if runnable else "none"
