#!/usr/bin/env python3
"""
embedding_shootout.py

Benchmarks embedding models for:
- load time
- encode throughput (queries + documents, short + chunk cases)
- CPU RSS (current + peak, Linux /proc-based)
- GPU memory (CUDA/XPU peak allocated/reserved when available)

Designed for local, reproducible comparisons in Reality Check.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


DEFAULT_MODELS = [
    "sentence-transformers/all-MiniLM-L6-v2",
    "google/embeddinggemma-300m",
    # "ibm-granite/granite-embedding-278m-multilingual",
    # "sentence-transformers/all-mpnet-base-v2",
    # "NovaSearch/stella_en_400M_v5",
    "Alibaba-NLP/gte-multilingual-base",
]


def _parse_key_value_overrides(text: str) -> dict[str, str]:
    overrides: dict[str, str] = {}
    if not text:
        return overrides
    for part in text.split(","):
        if not part.strip():
            continue
        if "=" not in part:
            raise ValueError(f"Invalid override '{part}'; expected key=value")
        k, v = part.split("=", 1)
        overrides[k.strip()] = v.strip()
    return overrides


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    name: str
    trust_remote_code: bool = False
    truncate_dim: Optional[int] = None
    query_prompt_name: Optional[str] = None
    doc_prompt_name: Optional[str] = None
    extra_st_kwargs: dict[str, Any] = None

    def to_json(self) -> str:
        payload = {
            "model_id": self.model_id,
            "name": self.name,
            "trust_remote_code": self.trust_remote_code,
            "truncate_dim": self.truncate_dim,
            "query_prompt_name": self.query_prompt_name,
            "doc_prompt_name": self.doc_prompt_name,
            "extra_st_kwargs": self.extra_st_kwargs or {},
        }
        return json.dumps(payload, separators=(",", ":"))


def _default_spec_for_model_id(model_id: str, *, truncate_dim: Optional[int] = None) -> ModelSpec:
    name = model_id.split("/")[-1]

    # Model-specific “known good defaults” from model cards / observed behavior.
    if model_id == "nomic-ai/nomic-embed-text-v2-moe":
        return ModelSpec(
            model_id=model_id,
            name=name,
            trust_remote_code=True,
            truncate_dim=truncate_dim,
            query_prompt_name="query",
            doc_prompt_name="passage",
            extra_st_kwargs={},
        )

    if model_id == "Qwen/Qwen3-Embedding-0.6B":
        return ModelSpec(
            model_id=model_id,
            name=name,
            trust_remote_code=False,
            truncate_dim=truncate_dim,
            query_prompt_name="query",
            doc_prompt_name="document",
            extra_st_kwargs={},
        )

    if model_id == "NovaSearch/stella_en_400M_v5":
        return ModelSpec(
            model_id=model_id,
            name=name,
            trust_remote_code=True,
            truncate_dim=truncate_dim,
            query_prompt_name="s2p_query",
            doc_prompt_name=None,  # docs do not need a prompt per model card
            extra_st_kwargs={
                # Model card suggests disabling these for CPU usage.
                "config_kwargs": {"use_memory_efficient_attention": False, "unpad_inputs": False},
            },
        )

    if model_id == "google/embeddinggemma-300m":
        # Uses encode_query/encode_document when available (worker handles this),
        # but keep prompt names for fallback.
        return ModelSpec(
            model_id=model_id,
            name=name,
            trust_remote_code=False,
            truncate_dim=truncate_dim,
            query_prompt_name="query",
            doc_prompt_name="document",
            extra_st_kwargs={},
        )

    if model_id == "Alibaba-NLP/gte-multilingual-base":
        return ModelSpec(
            model_id=model_id,
            name=name,
            trust_remote_code=True,
            truncate_dim=truncate_dim,
            query_prompt_name=None,
            doc_prompt_name=None,
            extra_st_kwargs={},
        )

    return ModelSpec(
        model_id=model_id,
        name=name,
        trust_remote_code=False,
        truncate_dim=truncate_dim,
        query_prompt_name=None,
        doc_prompt_name=None,
        extra_st_kwargs={},
    )


def _proc_status_kb() -> dict[str, int]:
    path = Path("/proc/self/status")
    if not path.exists():
        return {}
    data: dict[str, int] = {}
    for line in path.read_text().splitlines():
        if ":" not in line:
            continue
        key, rest = line.split(":", 1)
        key = key.strip()
        if key in {"VmRSS", "VmHWM"}:
            parts = rest.strip().split()
            if not parts:
                continue
            try:
                data[key] = int(parts[0])
            except ValueError:
                continue
    return data


def _sync_device(device: str) -> None:
    try:
        import torch
    except Exception:
        return

    if device.startswith("cuda") and torch.cuda.is_available():
        index = 0
        if ":" in device:
            try:
                index = int(device.split(":", 1)[1])
            except ValueError:
                index = 0
        torch.cuda.synchronize(index)
        return

    if device.startswith("xpu") and hasattr(torch, "xpu") and torch.xpu.is_available():
        try:
            torch.xpu.synchronize()
        except Exception:
            pass


def _gpu_mem_stats(device: str) -> dict[str, Any]:
    try:
        import torch
    except Exception:
        return {}

    if device.startswith("cuda") and torch.cuda.is_available():
        index = 0
        if ":" in device:
            try:
                index = int(device.split(":", 1)[1])
            except ValueError:
                index = 0
        return {
            "backend": "cuda",
            "device": device,
            "device_name": torch.cuda.get_device_name(index),
            "max_memory_allocated_bytes": int(torch.cuda.max_memory_allocated(index)),
            "max_memory_reserved_bytes": int(torch.cuda.max_memory_reserved(index)),
        }

    if device.startswith("xpu") and hasattr(torch, "xpu") and torch.xpu.is_available():
        stats: dict[str, Any] = {"backend": "xpu", "device": device}
        for fn_name in ["max_memory_allocated", "max_memory_reserved"]:
            fn = getattr(torch.xpu, fn_name, None)
            if callable(fn):
                try:
                    stats[f"{fn_name}_bytes"] = int(fn())
                except Exception:
                    pass
        return stats

    return {}


def _reset_gpu_peak_stats(device: str) -> None:
    try:
        import torch
    except Exception:
        return

    if device.startswith("cuda") and torch.cuda.is_available():
        index = 0
        if ":" in device:
            try:
                index = int(device.split(":", 1)[1])
            except ValueError:
                index = 0
        try:
            torch.cuda.reset_peak_memory_stats(index)
        except Exception:
            pass
        return

    if device.startswith("xpu") and hasattr(torch, "xpu") and torch.xpu.is_available():
        try:
            torch.xpu.reset_peak_memory_stats()
        except Exception:
            pass


def _make_texts_short(n: int) -> list[str]:
    return [
        f"Claim {i}: AI will change labor markets through automation and augmentation."
        for i in range(1, n + 1)
    ]


def _make_texts_chunk(n: int, *, sentence_repeats: int) -> list[str]:
    chunk = " ".join(["This is a sentence about automation and economics."] * sentence_repeats)
    return [chunk for _ in range(n)]


def _worker(spec: ModelSpec, *, device: str, args: argparse.Namespace) -> dict[str, Any]:
    # Imports inside worker to keep orchestrator fast and keep subprocess output clean.
    import torch  # noqa: F401
    import sentence_transformers
    import transformers
    from sentence_transformers import SentenceTransformer

    if args.offline:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

    rss0 = _proc_status_kb().get("VmRSS")

    st_kwargs: dict[str, Any] = {}
    if spec.trust_remote_code:
        st_kwargs["trust_remote_code"] = True
    if spec.truncate_dim is not None:
        st_kwargs["truncate_dim"] = spec.truncate_dim
    if spec.extra_st_kwargs:
        st_kwargs.update(spec.extra_st_kwargs)

    t0 = time.perf_counter()
    model = SentenceTransformer(spec.model_id, device=device, **st_kwargs)
    load_s = time.perf_counter() - t0

    # Reset GPU peaks after load so encode peaks are more meaningful.
    _reset_gpu_peak_stats(device)

    rss_after_load = _proc_status_kb().get("VmRSS")

    embed_dim = int(model.get_sentence_embedding_dimension())
    max_seq_length = getattr(model, "max_seq_length", None)
    prompts = getattr(model, "prompts", {}) or {}
    prompt_names = sorted(list(prompts.keys()))

    short_texts = _make_texts_short(args.short_n)
    chunk_texts = _make_texts_chunk(args.chunk_n, sentence_repeats=args.chunk_sentences)

    def encode_texts(texts: list[str], *, kind: str, batch_size: int) -> Any:
        if kind == "query":
            if hasattr(model, "encode_query"):
                return model.encode_query(texts, batch_size=batch_size, show_progress_bar=False)
            if spec.query_prompt_name:
                return model.encode(texts, prompt_name=spec.query_prompt_name, batch_size=batch_size, show_progress_bar=False)
            return model.encode(texts, batch_size=batch_size, show_progress_bar=False)
        if hasattr(model, "encode_document"):
            return model.encode_document(texts, batch_size=batch_size, show_progress_bar=False)
        if spec.doc_prompt_name:
            return model.encode(texts, prompt_name=spec.doc_prompt_name, batch_size=batch_size, show_progress_bar=False)
        return model.encode(texts, batch_size=batch_size, show_progress_bar=False)

    # Warmup (reduces one-time overhead in timed sections)
    encode_texts([short_texts[0]], kind="document", batch_size=1)
    _sync_device(device)

    rss_after_warmup = _proc_status_kb().get("VmRSS")

    benches: list[dict[str, Any]] = []
    for case_name, texts, bs in [
        ("short", short_texts, args.batch_short),
        ("chunk", chunk_texts, args.batch_chunk),
    ]:
        for kind in ["query", "document"]:
            rss_before = _proc_status_kb().get("VmRSS")
            _sync_device(device)
            t1 = time.perf_counter()
            emb = encode_texts(texts, kind=kind, batch_size=bs)
            _sync_device(device)
            dt = time.perf_counter() - t1
            rss_after = _proc_status_kb().get("VmRSS")
            dim = getattr(emb, "shape", (None, None))[-1]
            benches.append(
                {
                    "case": case_name,
                    "kind": kind,
                    "n": len(texts),
                    "batch_size": bs,
                    "seconds": dt,
                    "items_per_sec": (len(texts) / dt) if dt > 0 else None,
                    "embedding_dim": int(dim) if dim is not None else None,
                    "rss_before_kb": rss_before,
                    "rss_after_kb": rss_after,
                }
            )

    rss_end = _proc_status_kb().get("VmRSS")
    rss_peak = _proc_status_kb().get("VmHWM")

    out: dict[str, Any] = {
        "ok": True,
        "model": {
            "name": spec.name,
            "model_id": spec.model_id,
            "trust_remote_code": spec.trust_remote_code,
            "truncate_dim": spec.truncate_dim,
            "query_prompt_name": spec.query_prompt_name,
            "doc_prompt_name": spec.doc_prompt_name,
            "extra_st_kwargs": spec.extra_st_kwargs or {},
        },
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "torch": getattr(__import__("torch"), "__version__", None),
            "sentence_transformers": sentence_transformers.__version__,
            "transformers": transformers.__version__,
        },
        "device": device,
        "model_info": {
            "embedding_dim": embed_dim,
            "max_seq_length": max_seq_length,
            "prompt_names": prompt_names,
        },
        "timing": {"load_seconds": load_s},
        "memory": {
            "rss_start_kb": rss0,
            "rss_after_load_kb": rss_after_load,
            "rss_after_warmup_kb": rss_after_warmup,
            "rss_end_kb": rss_end,
            "rss_peak_kb": rss_peak,
        },
        "gpu_memory": _gpu_mem_stats(device),
        "benchmarks": benches,
    }
    return out


def _detect_devices() -> list[str]:
    devices = ["cpu"]
    try:
        import torch
    except Exception:
        return devices

    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            devices.append(f"cuda:{i}")
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        try:
            count = torch.xpu.device_count()
        except Exception:
            count = 1
        for i in range(count):
            devices.append(f"xpu:{i}")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        devices.append("mps")
    return devices


def _device_probe(device: str, *, iters: int = 1) -> dict[str, Any]:
    """
    Runs a minimal torch allocation/compute probe in a subprocess.

    This catches hard crashes (segfaults) that won't raise Python exceptions.
    """
    code = r"""
import os, time

device = os.environ.get("RC_DEVICE", "cpu")
iters = int(os.environ.get("RC_ITERS", "1"))

print(f"probe_start device={device} iters={iters}", flush=True)

import torch

def sync():
    if device.startswith("cuda") and torch.cuda.is_available():
        idx = 0
        if ":" in device:
            try:
                idx = int(device.split(":", 1)[1])
            except ValueError:
                idx = 0
        try:
            torch.cuda.synchronize(idx)
        except Exception:
            pass
    if device.startswith("xpu") and hasattr(torch, "xpu") and torch.xpu.is_available():
        try:
            torch.xpu.synchronize()
        except Exception:
            pass

t0 = time.perf_counter()
for _ in range(iters):
    x = torch.empty((1,), device=device)
    y = x + 1
    _ = y.sum()
    sync()

dt = time.perf_counter() - t0
print(f"probe_ok device={device} seconds={dt:.6f}", flush=True)
"""

    env = os.environ.copy()
    env["RC_DEVICE"] = device
    env["RC_ITERS"] = str(max(1, int(iters)))
    t0 = time.perf_counter()
    proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
    dt = time.perf_counter() - t0
    return {
        "device": device,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "seconds": dt,
        "stdout": proc.stdout.strip()[-4000:],
        "stderr": proc.stderr.strip()[-4000:],
    }


def _torch_info() -> dict[str, Any]:
    try:
        import torch
    except Exception as e:
        return {"ok": False, "error": str(e)}

    info: dict[str, Any] = {
        "ok": True,
        "torch_version": getattr(torch, "__version__", None),
        "cuda_build": getattr(getattr(torch, "version", None), "cuda", None),
        "hip_build": getattr(getattr(torch, "version", None), "hip", None),
        "mps_available": bool(getattr(getattr(torch, "backends", None), "mps", None) and torch.backends.mps.is_available()),
    }

    cuda: dict[str, Any] = {"available": bool(torch.cuda.is_available())}
    if cuda["available"]:
        try:
            count = int(torch.cuda.device_count())
        except Exception:
            count = 0
        cuda["device_count"] = count
        try:
            cuda["current_device"] = int(torch.cuda.current_device()) if count > 0 else None
        except Exception:
            cuda["current_device"] = None
        devices: list[dict[str, Any]] = []
        for i in range(count):
            try:
                name = torch.cuda.get_device_name(i)
            except Exception:
                name = None
            devices.append({"index": i, "name": name})
        cuda["devices"] = devices
    info["cuda"] = cuda

    xpu: dict[str, Any] = {"available": False}
    if hasattr(torch, "xpu"):
        try:
            xpu["available"] = bool(torch.xpu.is_available())
        except Exception:
            xpu["available"] = False
        if xpu["available"]:
            try:
                xpu["device_count"] = int(torch.xpu.device_count())
            except Exception:
                xpu["device_count"] = None
    info["xpu"] = xpu

    return info


def _device_available(device: str) -> tuple[bool, str]:
    if device == "cpu":
        return True, ""

    try:
        import torch
    except Exception as e:
        return False, f"torch import failed: {e}"

    if device.startswith("cuda"):
        if not torch.cuda.is_available():
            return False, "torch.cuda.is_available()==False"
        idx = 0
        if ":" in device:
            try:
                idx = int(device.split(":", 1)[1])
            except ValueError:
                idx = 0
        try:
            count = int(torch.cuda.device_count())
        except Exception:
            count = 0
        if idx < 0 or idx >= count:
            return False, f"cuda device index out of range (idx={idx}, count={count})"
        return True, ""

    if device.startswith("xpu"):
        if not hasattr(torch, "xpu"):
            return False, "torch.xpu is not available in this build"
        try:
            ok = bool(torch.xpu.is_available())
        except Exception:
            ok = False
        if not ok:
            return False, "torch.xpu.is_available()==False"
        return True, ""

    if device == "mps":
        if not hasattr(torch.backends, "mps") or not torch.backends.mps.is_available():
            return False, "torch.backends.mps.is_available()==False"
        return True, ""

    return False, f"unknown device '{device}'"


def _format_mb(kb: Optional[int]) -> str:
    if kb is None:
        return "n/a"
    return f"{kb/1024:.1f} MB"


def _format_mb_from_bytes(num_bytes: Optional[int]) -> str:
    if num_bytes is None:
        return "-"
    return f"{num_bytes/1024/1024:.0f} MB"


def _parse_worker_json(stdout: str) -> Optional[dict[str, Any]]:
    text = (stdout or "").strip()
    if not text:
        return None

    # Best case: stdout is exactly the JSON object.
    try:
        obj = json.loads(text)
        return obj if isinstance(obj, dict) else None
    except Exception:
        pass

    # Common failure mode on some systems: native libraries print diagnostics to stdout.
    # The worker prints JSON on the last line; salvage by parsing the last JSON-looking line.
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in reversed(lines):
        if ln.startswith("{") and ln.endswith("}"):
            try:
                obj = json.loads(ln)
                return obj if isinstance(obj, dict) else None
            except Exception:
                continue

    # Last resort: try parsing from the last '{' onward.
    start = text.rfind("{")
    if start != -1:
        try:
            obj = json.loads(text[start:])
            return obj if isinstance(obj, dict) else None
        except Exception:
            pass

    return None


def _get_bench(result: dict[str, Any], *, case: str, kind: str) -> Optional[dict[str, Any]]:
    for b in result.get("benchmarks", []) or []:
        if b.get("case") == case and b.get("kind") == kind:
            return b
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark embedding models (CPU/GPU) for speed + memory.")
    parser.add_argument(
        "--models",
        nargs="*",
        default=None,
        help="Model ids to benchmark (default: a Reality Check starter set).",
    )
    parser.add_argument(
        "--limit-models",
        type=int,
        default=None,
        help="Only run the first N models from the model list (useful for debugging).",
    )
    parser.add_argument(
        "--truncate-dim",
        type=int,
        default=None,
        help="Optional: apply SentenceTransformers truncate_dim to all models (only works for models that support it).",
    )
    parser.add_argument(
        "--devices",
        default="auto",
        help="Comma-separated devices (e.g. 'cpu,cuda:0,xpu:0') or 'auto' (default: cpu + any available accelerators).",
    )
    parser.add_argument("--offline", action="store_true", help="Set HF_HUB_OFFLINE=1 in workers (fail if not cached).")
    parser.add_argument("--short-n", type=int, default=64, help="Number of short texts to encode per run.")
    parser.add_argument("--chunk-n", type=int, default=16, help="Number of chunk texts to encode per run.")
    parser.add_argument("--chunk-sentences", type=int, default=40, help="Number of sentences per chunk text.")
    parser.add_argument("--batch-short", type=int, default=16, help="Batch size for short texts.")
    parser.add_argument("--batch-chunk", type=int, default=4, help="Batch size for chunk texts.")
    parser.add_argument("--json-out", type=Path, default=None, help="Write full results to this JSON file.")
    parser.add_argument(
        "--tablefmt",
        default="github",
        help="Summary table format. Use 'tsv' for tab-separated output; otherwise uses tabulate table formats (e.g. github, simple, grid).",
    )
    parser.add_argument("--debug", action="store_true", help="Print torch/device diagnostics and per-run timing to stderr.")
    parser.add_argument(
        "--probe-devices",
        action="store_true",
        help="Run a minimal torch GPU/accelerator probe per device (in a subprocess) before benchmarking.",
    )
    parser.add_argument(
        "--probe-iters",
        type=int,
        default=1,
        help="Iterations for the device probe (use >1 to detect flakiness).",
    )
    parser.add_argument(
        "--probe-only",
        action="store_true",
        help="Only run the device probe(s) and exit (no model benchmarking).",
    )
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--spec-json", default=None, help=argparse.SUPPRESS)
    parser.add_argument("--device", default=None, help=argparse.SUPPRESS)

    args = parser.parse_args()

    if args.worker:
        if not args.spec_json or not args.device:
            print(json.dumps({"ok": False, "error": "worker requires --spec-json and --device"}))
            return 2
        spec_payload = json.loads(args.spec_json)
        spec = ModelSpec(
            model_id=spec_payload["model_id"],
            name=spec_payload["name"],
            trust_remote_code=bool(spec_payload.get("trust_remote_code", False)),
            truncate_dim=spec_payload.get("truncate_dim"),
            query_prompt_name=spec_payload.get("query_prompt_name"),
            doc_prompt_name=spec_payload.get("doc_prompt_name"),
            extra_st_kwargs=spec_payload.get("extra_st_kwargs") or {},
        )
        try:
            out = _worker(spec, device=args.device, args=args)
        except Exception as e:
            out = {"ok": False, "error": str(e), "model": spec_payload, "device": args.device}
        print(json.dumps(out))
        return 0

    model_ids = args.models if args.models else DEFAULT_MODELS
    if args.limit_models is not None:
        n = max(0, int(args.limit_models))
        model_ids = model_ids[:n]
    device_arg = args.devices.strip()
    if device_arg == "auto":
        devices = _detect_devices()
    else:
        devices = [d.strip() for d in device_arg.split(",") if d.strip()]
        if not devices:
            devices = ["cpu"]

    # Torch/device sanity check (helpful when running on CUDA/ROCm/XPU).
    info = _torch_info()
    if args.debug:
        print("[debug] torch info:", file=sys.stderr)
        print(json.dumps(info, indent=2, sort_keys=True), file=sys.stderr)
        print(f"[debug] requested devices: {devices}", file=sys.stderr)
    else:
        for d in devices:
            ok, reason = _device_available(d)
            if not ok:
                torch_ver = info.get("torch_version") if isinstance(info, dict) else None
                print(
                    f"[warn] device '{d}' may be unavailable ({reason}). torch={torch_ver}. "
                    "Re-run with --debug for full torch/device info.",
                    file=sys.stderr,
                )

    if args.probe_devices or args.probe_only:
        probe_rows: list[dict[str, Any]] = []
        for device in devices:
            if args.debug:
                print(f"[debug] probe device={device} iters={args.probe_iters}", file=sys.stderr)
            probe = _device_probe(device, iters=args.probe_iters)
            probe_rows.append(probe)
            if args.debug:
                print(
                    f"[debug] probe done device={device} ok={probe.get('ok')} returncode={probe.get('returncode')} seconds={probe.get('seconds'):.2f}",
                    file=sys.stderr,
                )
                if not probe.get("ok"):
                    if probe.get("stdout"):
                        print(f"[debug] probe stdout tail: {probe.get('stdout').splitlines()[-1]}", file=sys.stderr)
                    if probe.get("stderr"):
                        print(f"[debug] probe stderr tail: {probe.get('stderr').splitlines()[-1]}", file=sys.stderr)

        # If probe-only, print and exit.
        if args.probe_only:
            headers = ["device", "ok", "returncode", "seconds"]
            rows = [
                [str(p.get("device")), str(bool(p.get("ok"))), str(p.get("returncode")), f"{p.get('seconds', 0):.2f}"]
                for p in probe_rows
            ]
            if args.tablefmt.strip().lower() == "tsv":
                print("\t".join(headers))
                for row in rows:
                    print("\t".join(row))
            else:
                try:
                    from tabulate import tabulate  # type: ignore[import-not-found]
                except Exception:
                    print("\t".join(headers))
                    for row in rows:
                        print("\t".join(row))
                else:
                    print(tabulate(rows, headers=headers, tablefmt=args.tablefmt, stralign="left", numalign="right"))
            return 0 if all(bool(p.get("ok")) for p in probe_rows) else 1

        if args.probe_devices:
            ok_devices = [p["device"] for p in probe_rows if p.get("ok")]
            bad_devices = [p["device"] for p in probe_rows if not p.get("ok")]
            if bad_devices:
                print(
                    f"[warn] skipping devices that failed the torch probe: {', '.join(bad_devices)}",
                    file=sys.stderr,
                )
            devices = ok_devices
            if not devices:
                print("[warn] no usable devices remain after probe; exiting.", file=sys.stderr)
                return 1

    specs = [_default_spec_for_model_id(mid, truncate_dim=args.truncate_dim) for mid in model_ids]

    results: list[dict[str, Any]] = []
    for spec in specs:
        for device in devices:
            ok, reason = _device_available(device)
            if not ok:
                results.append(
                    {
                        "ok": False,
                        "error": f"device unavailable: {reason}",
                        "model": {"model_id": spec.model_id, "name": spec.name},
                        "device": device,
                    }
                )
                if args.debug:
                    print(f"[debug] skip model={spec.model_id} device={device}: {reason}", file=sys.stderr)
                continue

            cmd = [
                sys.executable,
                str(Path(__file__).resolve()),
                "--worker",
                "--spec-json",
                spec.to_json(),
                "--device",
                device,
                "--short-n",
                str(args.short_n),
                "--chunk-n",
                str(args.chunk_n),
                "--chunk-sentences",
                str(args.chunk_sentences),
                "--batch-short",
                str(args.batch_short),
                "--batch-chunk",
                str(args.batch_chunk),
            ]
            if args.offline:
                cmd.append("--offline")

            if args.debug:
                print(f"[debug] run model={spec.model_id} device={device}", file=sys.stderr)
            t_start = time.perf_counter()
            proc = subprocess.run(cmd, capture_output=True, text=True)
            t_elapsed = time.perf_counter() - t_start
            out = _parse_worker_json(proc.stdout)
            if out is not None:
                results.append(out)
                if args.debug:
                    print(
                        f"[debug] done model={spec.model_id} device={device} ok={bool(out.get('ok'))} elapsed_s={t_elapsed:.2f} returncode={proc.returncode}",
                        file=sys.stderr,
                    )
                    if not out.get("ok") and out.get("error"):
                        print(f"[debug] error: {out.get('error')}", file=sys.stderr)
                continue
            results.append(
                {
                    "ok": False,
                    "error": "worker failed",
                    "returncode": proc.returncode,
                    "stdout": proc.stdout[-4000:],
                    "stderr": proc.stderr[-4000:],
                    "model": {"model_id": spec.model_id, "name": spec.name},
                    "device": device,
                    "elapsed_seconds": t_elapsed,
                }
            )
            if args.debug:
                print(
                    f"[debug] done model={spec.model_id} device={device} ok=False elapsed_s={t_elapsed:.2f} returncode={proc.returncode} (worker failed)",
                    file=sys.stderr,
                )
                if proc.stdout.strip():
                    tail = proc.stdout.strip().splitlines()[-1]
                    print(f"[debug] stdout tail: {tail}", file=sys.stderr)
                if proc.stderr.strip():
                    tail = proc.stderr.strip().splitlines()[-1]
                    print(f"[debug] stderr tail: {tail}", file=sys.stderr)

    if args.json_out:
        args.json_out.write_text(json.dumps(results, indent=2))

    # Print compact summary
    headers = [
        "model",
        "device",
        "dim",
        "max_seq",
        "load_s",
        "rss_peak",
        "gpu_peak_alloc",
        "gpu_peak_resv",
        "short_q/s",
        "short_d/s",
        "chunk_q/s",
        "chunk_d/s",
    ]
    rows: list[list[str]] = []

    def fmt_ips(b: Optional[dict[str, Any]]) -> str:
        v = (b or {}).get("items_per_sec")
        if v is None:
            return "-"
        return f"{v:.1f}"

    for r in results:
        model = (r.get("model") or {}).get("name") or (r.get("model") or {}).get("model_id") or "?"
        device = r.get("device") or "?"
        if not r.get("ok"):
            rows.append([model, device, "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"])
            continue

        mi = r.get("model_info") or {}
        dim = mi.get("embedding_dim")
        max_seq = mi.get("max_seq_length")
        load_s = (r.get("timing") or {}).get("load_seconds")
        rss_peak = _format_mb((r.get("memory") or {}).get("rss_peak_kb"))
        gpu_mem = r.get("gpu_memory") or {}
        gpu_peak_alloc = _format_mb_from_bytes(gpu_mem.get("max_memory_allocated_bytes"))
        gpu_peak_resv = _format_mb_from_bytes(gpu_mem.get("max_memory_reserved_bytes"))

        short_q = _get_bench(r, case="short", kind="query")
        short_d = _get_bench(r, case="short", kind="document")
        chunk_q = _get_bench(r, case="chunk", kind="query")
        chunk_d = _get_bench(r, case="chunk", kind="document")

        rows.append(
            [
                str(model),
                str(device),
                str(dim),
                str(max_seq),
                f"{load_s:.3f}" if isinstance(load_s, (int, float)) else "-",
                rss_peak,
                gpu_peak_alloc,
                gpu_peak_resv,
                fmt_ips(short_q),
                fmt_ips(short_d),
                fmt_ips(chunk_q),
                fmt_ips(chunk_d),
            ]
        )

    if args.tablefmt.strip().lower() == "tsv":
        print("\t".join(headers))
        for row in rows:
            print("\t".join(row))
    else:
        try:
            from tabulate import tabulate  # type: ignore[import-not-found]
        except Exception:
            print("\t".join(headers))
            for row in rows:
                print("\t".join(row))
        else:
            print(tabulate(rows, headers=headers, tablefmt=args.tablefmt, stralign="left", numalign="right"))

    if args.json_out:
        print(f"\nWrote JSON results to: {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
