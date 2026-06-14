"""labforge — plan, fit, and check compatibility for a homelab / dev-AI rig, and
see how it runs the Cognis suite + popular industry tools.

  catalog [--kind gpu|unified_box|apu_mini_pc|sbc_edge|memory]   browse hardware
  show <key>                              one component in detail
  detect                                  profile THIS machine (edgemesh-aware)
  fit [--memory GB] [--bandwidth GBs] [--quant q4|q5|int8|fp16]  what models run
  compat <stack> [--arch ARCH]            will a stack run on an architecture?
  plan --budget N [--workload W] [--devs N]   recommend a build (BoM)
  interop                                 how the rig runs the Cognis suite
  tools [--category C]                    popular industry tools for a homelab

--format table|json
"""
from __future__ import annotations
import argparse
import json

from . import hardware, fit as fitmod, compat as compatmod, detect as detectmod
from . import procure, interop
from .hardware import TOOL_NAME, TOOL_VERSION


def _j(o): print(json.dumps(o, indent=2, default=lambda x: getattr(x, "to_dict", lambda: str(x))()))


def cmd_catalog(a):
    cs = hardware.catalog(a.kind)
    if a.format == "json":
        _j([c.to_dict() for c in cs]); return 0
    for c in cs:
        mem = f"{c.memory_gb:g}GB" if c.memory_gb else "-"
        bw = f"{c.bandwidth_gbs:g}GB/s" if c.bandwidth_gbs else "-"
        print(f"{c.key:24} {c.kind:13} {mem:>7} {bw:>10}  {c.price_band:>15}  {c.name}")
    return 0


def cmd_show(a):
    c = hardware.get(a.key)
    if not c:
        print(f"unknown '{a.key}'"); return 1
    _j(c.to_dict()); return 0


def cmd_detect(a):
    p = detectmod.detect()
    if a.format == "json":
        _j(p); return 0
    print(f"source: {p.get('_source')}  os: {p.get('os')}  arch: {p.get('arch_family')}")
    print(f"cpu: {p.get('cpu')}  ram: {p.get('ram_gb')}GB")
    print(f"gpus: {p.get('gpus')}")
    print(f"inference memory: {p.get('inference_memory_gb')}GB")
    print(f"-> largest model (q4): {fitmod.largest_fit(p.get('inference_memory_gb'))}")
    return 0


def cmd_fit(a):
    mem = a.memory
    bw = a.bandwidth
    if mem is None:
        p = detectmod.detect(); mem = p.get("inference_memory_gb")
        print(f"(using detected memory: {mem}GB)") if a.format != "json" else None
    res = fitmod.fits(mem, bw, quant=a.quant)
    if a.format == "json":
        _j([r.to_dict() for r in res]); return 0
    for r in res:
        mark = "OK " if r.fits else "  -"
        spd = f"~{r.est_tok_s} tok/s" if r.est_tok_s else ""
        print(f"{mark} {r.model:32} {r.weights_gb:>6}GB @ {r.quant:5} {spd:>14}  {r.note}")
    return 0


def cmd_compat(a):
    if a.arch:
        _j(compatmod.check(a.stack, a.arch)); return 0
    # show across all archs
    res = {arch: compatmod.check(a.stack, arch) for arch in compatmod.ARCHS}
    if a.format == "json":
        _j(res); return 0
    for arch, r in res.items():
        print(f"{arch:18} {r['status']:12} {r['note']}")
    return 0


def cmd_plan(a):
    b = procure.recommend(a.budget, a.workload, a.devs)
    if a.format == "json":
        _j(b.to_dict()); return 0
    print(f"# Build for: {a.workload} (budget ${a.budget:,}, {a.devs} dev(s))")
    print(f"\n{b.rationale}\n")
    print("Bill of materials:")
    for x in b.bom:
        print(f"  {x['qty']}x {x['component'].name}  ({x['component'].price_band})")
    print(f"\nEstimated total: ${b.total_low:,} - ${b.total_high:,}")
    print(f"Runs (q4): up to {b.runs}")
    for n in b.notes:
        print(f"  ! {n}")
    return 0


def cmd_interop(a):
    if a.format == "json":
        _j(interop.cognis_interop()); return 0
    for c in interop.cognis_interop():
        print(f"[{c['repo']}] {c['role']}\n    {c['interop']}\n    handoff: {c['handoff']}")
    return 0


def cmd_tools(a):
    ts = interop.industry_tools(a.category)
    if a.format == "json":
        _j(ts); return 0
    for t in ts:
        print(f"{t['tool']:28} [{t['category']:14}] {t['role']}")
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog=TOOL_NAME, description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--version", action="version", version=f"{TOOL_NAME} {TOOL_VERSION}")
    sub = p.add_subparsers(dest="command")

    def add(n, fn):
        sp = sub.add_parser(n); sp.add_argument("--format", choices=["table", "json"],
                                                default="table"); sp.set_defaults(func=fn)
        return sp

    sp = add("catalog", cmd_catalog); sp.add_argument("--kind")
    sp = add("show", cmd_show); sp.add_argument("key")
    add("detect", cmd_detect)
    sp = add("fit", cmd_fit); sp.add_argument("--memory", type=float)
    sp.add_argument("--bandwidth", type=float); sp.add_argument("--quant", default="q4")
    sp = add("compat", cmd_compat); sp.add_argument("stack"); sp.add_argument("--arch")
    sp = add("plan", cmd_plan); sp.add_argument("--budget", type=int, required=True)
    sp.add_argument("--workload", default="shared_team"); sp.add_argument("--devs", type=int, default=1)
    add("interop", cmd_interop)
    sp = add("tools", cmd_tools); sp.add_argument("--category")
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not getattr(args, "command", None):
        build_parser().print_help(); return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
