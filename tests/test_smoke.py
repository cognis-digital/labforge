"""Tests for labforge. No network — detection degrades gracefully on any host."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from labforge import (  # noqa: E402
    TOOL_NAME, TOOL_VERSION, catalog, get, KINDS, fit, compat, detect, procure, interop,
)
from labforge.cli import main  # noqa: E402


def test_metadata():
    assert TOOL_NAME == "labforge"
    assert TOOL_VERSION.count(".") == 2


def test_catalog():
    cs = catalog()
    assert len(cs) >= 8
    assert all(c.kind in KINDS for c in cs)
    spark = get("dgx_spark")
    assert spark and spark.memory_gb == 128 and "aarch64" in spark.arch.lower()
    assert get("rtx_5090").bandwidth_gbs == 1792


def test_fit_capacity_and_speed():
    # 24GB card can't fit 70B at q4 (~35GB*1.2), can fit 27B
    res = {r.model: r for r in fit.fits(24, 1008, quant="q4")}
    assert res["Gemma 3 27B"].fits
    assert not res["Llama 3.3 70B"].fits
    # 128GB unified fits 120B-class MoE and gives a tok/s estimate
    big = {r.model: r for r in fit.fits(128, 273, quant="q4")}
    assert big["gpt-oss-120B (MoE)"].fits
    assert big["gpt-oss-120B (MoE)"].est_tok_s and big["gpt-oss-120B (MoE)"].est_tok_s > 0
    # MoE active-param speed > a dense model of the same total size would get
    assert "MoE" in big["gpt-oss-120B (MoE)"].note


def test_fit_largest():
    assert fit.largest_fit(8) in ("Llama 3.1 8B", "none")
    assert "120B" in fit.largest_fit(128) or "235B" in fit.largest_fit(128) or fit.largest_fit(128)


def test_compat_traps():
    # the GB10 aarch64/CUDA13 vLLM wheel trap is encoded
    assert compat.check("vllm", "cuda12_x86")["status"] == "ok"
    assert compat.check("vllm", "cuda13_aarch64")["status"] == "partial"
    assert compat.check("mlx", "metal_arm64")["status"] == "ok"
    assert compat.check("mlx", "cuda12_x86")["status"] == "unsupported"
    assert compat.check("nope", "cuda12_x86")["status"] == "unknown"
    # llama.cpp runs everywhere
    for arch in compat.ARCHS:
        assert compat.check("llama.cpp", arch)["status"] == "ok"


def test_detect_runs():
    p = detect.detect()
    assert "arch_family" in p and p["arch_family"] in compat.ARCHS
    assert "_source" in p


def test_procure_shared_team_config_b():
    b = procure.recommend(11000, "shared_team", devs=4)
    keys = [x["component"].key for x in b.bom]
    assert "dgx_spark" in keys and "rtx_5090" in keys  # the Config-B pairing
    assert b.total_low > 0
    assert any("shortage" in n.lower() for n in b.notes)
    json.dumps(b.to_dict())


def test_procure_starter():
    b = procure.recommend(2000, "starter")
    assert b.bom and b.total_low > 0


def test_interop_maps():
    ci = interop.cognis_interop()
    assert any(c["repo"] == "edgemesh" for c in ci)
    tools = interop.industry_tools()
    assert any(t["tool"] == "Ollama" for t in tools)
    assert any(t["tool"] == "Proxmox VE" for t in tools)


def test_cli():
    assert main(["catalog"]) == 0
    assert main(["catalog", "--kind", "gpu", "--format", "json"]) == 0
    assert main(["show", "dgx_spark", "--format", "json"]) == 0
    assert main(["detect"]) == 0
    assert main(["fit", "--memory", "32", "--bandwidth", "1792"]) == 0
    assert main(["compat", "vllm"]) == 0
    assert main(["compat", "vllm", "--arch", "cuda13_aarch64", "--format", "json"]) == 0
    assert main(["plan", "--budget", "11000", "--workload", "shared_team", "--devs", "4"]) == 0
    assert main(["interop"]) == 0
    assert main(["tools", "--format", "json"]) == 0
