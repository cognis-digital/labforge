"""
Interop map — how a labforge-planned rig runs the Cognis suite (300+ repos) and the
popular industry tooling, so the hardware you buy actually serves the software you run.

labforge plans the metal; edgemesh turns the metal into one cluster + OpenAI endpoint;
the Cognis fleet, cog4, the open-cloud emulators, and Mission Control run on top; and
the standard homelab/industry stack (Ollama, vLLM, Proxmox, Docker, k8s, Tailscale,
JupyterHub) provides the substrate. This module is the documented handoff.
"""
from __future__ import annotations

# Cognis repos that consume the lab, with the handoff
COGNIS = [
    {"repo": "edgemesh", "role": "Cluster + scheduler",
     "interop": "labforge's detector mirrors edgemesh's hardware probe; once your rigs "
                "are built, edgemesh discovers them, fits models to each node's VRAM, "
                "and exposes one OpenAI-compatible /v1 endpoint + a swarm scheduler.",
     "handoff": "labforge plan -> build -> `edgemesh join` each node -> one cluster."},
    {"repo": "cognis fleet (cog4)", "role": "Local multi-model fleet",
     "interop": "The reasoning/coding/vision/uncensored slots run on the GPUs/boxes "
                "labforge recommends; bandwidth + VRAM from `labforge fit` set which "
                "models each slot can host.",
     "handoff": "size slots from `labforge fit`; serve via llama.cpp/Ollama."},
    {"repo": "opengcp / openaws / openazure / openfirebase", "role": "Local cloud emulators",
     "interop": "Pure-stdlib, run on any node in the lab (even a mini-PC/SBC control "
                "node) to give the team local cloud primitives with no external spend.",
     "handoff": "deploy on a homelab node; point dev apps at the local endpoints."},
    {"repo": "jtf-meridian", "role": "Decision-support",
     "interop": "Uses the uncensored fleet slot that the lab hosts.",
     "handoff": "fleet up -> `jtf brief` runs live."},
    {"repo": "mission-control", "role": "Cockpit",
     "interop": "Monitors the fleet/Docker/bot running on the lab.", "handoff": "open :7777."},
]

# popular industry tools and their place in a homelab / shared dev lab
INDUSTRY = [
    {"tool": "Ollama", "category": "inference", "role": "Easiest local model serving; "
     "cross-arch (CUDA/ROCm/Metal). Good default for each node."},
    {"tool": "llama.cpp", "category": "inference", "role": "Most portable engine "
     "(CUDA/ROCm/Metal/Vulkan/CPU); the reliable path on GB10 aarch64 + Strix Halo."},
    {"tool": "vLLM", "category": "inference", "role": "High-throughput serving on mature "
     "CUDA x86; mind the aarch64/CUDA13 wheel trap (see `labforge compat`)."},
    {"tool": "Proxmox VE", "category": "virtualization", "role": "Hypervisor to carve a "
     "big rig into VMs/LXC per dev or service; GPU passthrough."},
    {"tool": "Docker", "category": "containers", "role": "Package + run services "
     "(the open-cloud emulators, JupyterHub) consistently across nodes."},
    {"tool": "Kubernetes / k3s", "category": "orchestration", "role": "k3s is the "
     "homelab-friendly way to schedule containers across multiple nodes."},
    {"tool": "Tailscale", "category": "networking", "role": "Zero-config mesh VPN so "
     "devs reach the shared rigs securely from their laptops anywhere."},
    {"tool": "JupyterHub", "category": "multi-user", "role": "Multi-user notebooks on the "
     "shared rig — the DARQ multi-dev access pattern."},
    {"tool": "VS Code Remote (SSH/Tunnels)", "category": "remote-dev", "role": "Devs edit "
     "+ run on the central rig from a laptop frontend."},
    {"tool": "TrueNAS", "category": "storage", "role": "Shared model/dataset storage over "
     "10GbE for the lab."},
]


def cognis_interop() -> list:
    return list(COGNIS)


def industry_tools(category: str | None = None) -> list:
    return [t for t in INDUSTRY if not category or t["category"] == category]


def stack_for_arch_note(arch: str) -> str:
    from . import compat
    rec = [s["stack"] for s in compat.stacks_for(arch) if s["status"] == "ok"]
    return f"On {arch}, prefer: {', '.join(rec) or 'CPU fallbacks'}."
