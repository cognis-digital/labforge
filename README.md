# labforge

> Build and scale a local AI / dev lab on real hardware. `labforge` is a homelab
> hardware toolkit: a catalog of the gear that matters, a model-fit engine, a
> stack-vs-architecture compatibility matrix, a budget-aware procurement planner,
> and an interop map showing how your rig runs the **Cognis 300+ suite** and the
> popular industry tooling.

[![Code License: COCL 1.0](https://img.shields.io/badge/License-COCL%201.0-6b46c1.svg)](LICENSE)
[![tests](https://img.shields.io/badge/tests-10%20passing-2ea44f.svg)](tests/)

<!-- cognis:layman:start -->
## What is this?

Standing up a machine to run modern AI models — or a shared rig for a small dev
team — is suddenly hard: GPUs and memory are expensive and scarce (a real DRAM
shortage in 2026), the specs that matter aren't obvious, and half the "just pip
install it" advice quietly fails on newer chips. `labforge` cuts through that. Tell
it your budget and what you want to run, and it recommends an actual parts list.
Point it at a machine and it tells you which models will fit and roughly how fast.
Ask it whether a tool (vLLM, Ollama, llama.cpp…) will work on a given chip and it
warns you about the traps before you waste a weekend. And it shows how the hardware
you buy runs the whole Cognis software suite and the standard homelab stack. It's
the missing "what do I actually buy, and will my software run on it?" layer for
developers building and scaling a lab.
<!-- cognis:layman:end -->

## Why it exists

Grounded in a real acquisition problem (a $10–12K shared rig for a 3–4-dev team
running 70B–120B-class models + a CUDA/Rust reasoning engine) and **extended web
research** — see [`RESEARCH.md`](RESEARCH.md): 9 categories, 97 hardware/tooling
items, 273 sources. Two physics rules drive everything: **capacity** decides what
loads; **bandwidth** decides speed; **MoE** softens the bandwidth need.

## Five things it does

| Command | What you get |
|---|---|
| `labforge catalog` | The hardware that matters (GPUs, GB10/Spark & Jetson unified boxes, Strix-Halo APUs, SBCs, the memory market) with VRAM, bandwidth, arch, TDP, price band. |
| `labforge detect` | Profiles *this* machine (and defers to **edgemesh**'s probe if installed). |
| `labforge fit --memory 128 --bandwidth 273` | Which models load + a single-stream tok/s estimate (MoE-aware). |
| `labforge compat vllm` | Will a stack run on cuda12-x86 / cuda13-aarch64 / ROCm / Metal / CPU — incl. the GB10 aarch64/CUDA-13 wheel trap. |
| `labforge plan --budget 11000 --workload shared_team --devs 4` | A recommended build (BoM) + what it runs + shortage warnings. |

```sh
labforge plan --budget 11000 --workload shared_team --devs 4
labforge compat vllm --arch cuda13_aarch64      # the trap, spelled out
labforge fit --memory 32 --bandwidth 1792       # what an RTX 5090 runs
labforge interop                                 # how the rig runs the Cognis suite
labforge tools --category inference              # industry tooling for the lab
```

## Interoperates with the Cognis suite + industry tools

`labforge` plans the metal; **[edgemesh](https://github.com/cognis-digital/edgemesh)**
turns it into one cluster + OpenAI endpoint; the Cognis fleet, `cog4`, the
**open-cloud emulators** (opengcp/openaws/openazure/openfirebase), `jtf-meridian`,
and Mission Control run on top. It maps the standard stack too — Ollama, llama.cpp,
vLLM, Proxmox, Docker, k3s, Tailscale, JupyterHub, VS Code Remote, TrueNAS — so the
hardware you buy actually serves the software you run. `labforge interop` and
`labforge tools` document the handoffs.

<!-- cognis:install:start -->
## Install

`labforge` is source-available (not on PyPI) — install straight from GitHub.

```sh
curl -fsSL https://raw.githubusercontent.com/cognis-digital/labforge/HEAD/install.sh | sh   # Linux/macOS
```
```powershell
irm https://raw.githubusercontent.com/cognis-digital/labforge/HEAD/install.ps1 | iex        # Windows
```
```sh
pipx install "git+https://github.com/cognis-digital/labforge.git"   # or uv tool install / pip install
git clone https://github.com/cognis-digital/labforge.git && cd labforge && pip install .    # from source
```
Then: `labforge --help`
<!-- cognis:install:end -->

## Topics / Domains

`homelab` · `hardware` · `local-ai` · `llm` · `gpu` · `procurement` · `devops` ·
`edge-ai` · part of the **Cognis Neural Suite** (cloud & devtools / infrastructure domain).

## Verification

```text
tests   : 10 passing (deterministic; detection degrades gracefully on any host)
data    : RESEARCH.md / data/research_2026-06.json — 97 items, 273 sources (Jun 2026)
runtime : pure Python standard library; no third-party deps
```

## Disclaimer

Hardware prices and availability in 2026 are volatile (active DRAM/GDDR7 shortage) —
the catalog reflects June-2026 research and is a planning aid, **verify current
prices before buying**. tok/s figures are order-of-magnitude estimates, not
benchmarks. Not affiliated with NVIDIA, AMD, Apple, or any vendor named.

## License

Cognis Open Collaboration License (COCL) 1.0 — see [LICENSE](LICENSE).
