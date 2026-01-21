# Embeddings: Model Options for Local Search

This document reviews candidate **local** embedding models for Reality Check’s semantic search and how they fit the current LanceDB + `sentence-transformers` pipeline.

## Goals (Reality Check-specific)

- **Local-first**: run without external APIs; works offline after the model is present.
- **Good retrieval** on short texts (claims) and medium texts (source titles/notes).
- **Predictable ops**: stable embedding dimensionality, reproducible settings, and clear migration steps.
- **Clear compatibility** with the current database schema and search implementation.

## Current State (in this repo today)

Reality Check currently has a dense-embedding implementation wired into:

- `scripts/db.py` (embedding generation via `sentence-transformers` + semantic search over a vector column)
- `scripts/embed.py` (`rc-embed status|generate|regenerate`)
- `docs/SCHEMA.md` currently documents a fixed `vector[384]` column for embeddings.

### Implication: embedding dimension is “schema-coupled”

Because the schema currently pins `vector[384]`, any candidate model whose output dimensionality ≠ 384 is **not drop-in** without a schema/migration change.

### If you truly haven’t committed to a schema yet

If the intention is to redesign before any “real” indexing/storage lands, you can treat the above as provisional and choose:

- dense single-vector retrieval (simplest)
- chunked dense retrieval (best baseline for long texts)
- late-interaction / ColBERT (best long-doc precision, most architectural work)

## Model Families: “Drop-in” vs “Not Drop-in”

Reality Check’s current search is **dense single-vector retrieval**.

- **Dense embeddings (single vector per text)**: typically drop-in *if* you can match the vector size the DB expects (or migrate schema).
- **Late-interaction / ColBERT-style models (multiple vectors per text)**: **not drop-in** to the current design; they require a different storage/indexing/search approach (token-level embeddings + MaxSim).
- **MoE (mixture-of-experts)**: can still be dense, but may have different latency/caching characteristics; verify on your hardware.

## Keeping `vector[384]` (if we don’t want a schema migration yet)

If we want to try newer models while keeping the current `vector[384]` schema, there are only a few safe options:

1. **Choose a model that natively outputs 384 dims** (true drop-in).
2. **Use “matryoshka”/multi-resolution embeddings** *only if* the model explicitly supports it, where truncating to 384 dims is a recommended usage pattern.
3. **Learn a projection** from N-dim → 384 (e.g., PCA / linear layer) and store projected vectors.

Notes:

- Plain “truncate any embedding to 384” is *not* generally safe unless the model is designed for it.
- Projection adds operational complexity (you now have a model + a projection artifact that must be versioned together).

## Candidate Models (provided list)

Reality Check candidates to evaluate:

- https://huggingface.co/nomic-ai/nomic-embed-text-v2-moe
- https://huggingface.co/LiquidAI/LFM2-ColBERT-350M
- https://huggingface.co/Qwen/Qwen3-Embedding-0.6B
- https://huggingface.co/google/embeddinggemma-300m
- https://huggingface.co/lightonai/modernbert-embed-large
- https://huggingface.co/lightonai/GTE-ModernColBERT-v1

### Additional dense candidates (requested)

- https://huggingface.co/NovaSearch/stella_en_400M_v5
- https://huggingface.co/ibm-granite/granite-embedding-278m-multilingual

### Baseline / reference models (important for comparison)

- https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
- https://huggingface.co/sentence-transformers/all-MiniLM-L12-v2
- https://huggingface.co/sentence-transformers/all-mpnet-base-v2

### Tiny ColBERT reference (edge-sized)

- https://huggingface.co/mixedbread-ai/mxbai-edge-colbert-v0-32m

### Quick Compatibility Table (high-level)

| Model | Family | Likely drop-in for current LanceDB vector search? | Notes |
|------:|--------|----------------------------------------------------|------|
| `nomic-ai/nomic-embed-text-v2-moe` | Dense (MoE) | **Maybe** (dimension must match or migrate) | Verify output dim, recommended pooling, and whether it expects “query:” / “document:” prefixes. |
| `Qwen/Qwen3-Embedding-0.6B` | Dense | **Maybe** (dimension must match or migrate) | Larger model class; likely higher quality but heavier CPU/GPU requirements. Verify dim + normalization. |
| `google/embeddinggemma-300m` | Dense | **Maybe** (dimension must match or migrate) | **Gated** (manual) under Gemma terms; dense `768` dims, `max_seq_length=2048`, supports MRL truncation (`512`/`256`/`128`), query/document prompts (`encode_query`/`encode_document`), float16 activations unsupported. |
| `NovaSearch/stella_en_400M_v5` | Dense | **Maybe** (dimension must match or migrate) | Dense `1024` dims by default, `max_seq_length=512`, query prompts (`s2p_query` / `s2s_query`), MRL dims via per-dimension `2_Dense_*` weights; requires `trust_remote_code=True`. |
| `ibm-granite/granite-embedding-278m-multilingual` | Dense | **Maybe** (dimension must match or migrate) | Dense `768` dims, `max_seq_length=512`, CLS pooling; Apache-2.0; multilingual (12 languages). |
| `lightonai/modernbert-embed-large` | Dense (BERT-derived) | **Maybe** (dimension must match or migrate) | Verify intended use (retrieval vs classification), output dim, and recommended pooling. |
| `LiquidAI/LFM2-ColBERT-350M` | ColBERT / late-interaction | **No (not drop-in)** | Requires token-level embeddings + late-interaction scoring; different indexing than “one vector per record”. |
| `lightonai/GTE-ModernColBERT-v1` | ColBERT / late-interaction | **No (not drop-in)** | Same issue: not compatible with single-vector LanceDB search without redesign. |
| `sentence-transformers/all-MiniLM-L6-v2` | Dense | **Yes** (if schema uses 384) | Very small + extremely popular baseline; short max seq length. |
| `sentence-transformers/all-mpnet-base-v2` | Dense | **Yes** (with schema migration) | Strong “classic” dense baseline; larger dim/params than MiniLM. |
| `mixedbread-ai/mxbai-edge-colbert-v0-32m` | ColBERT / late-interaction | **No (not drop-in)** | Tiny ColBERT; strong long-context retrieval results on its own benchmarks; requires PyLate-style indexing. |

## What You Must Verify From Each Model Card (before adopting)

This repo can’t assume these details without checking the model card:

1. **Output dimensionality** (vector length). If it’s not 384, the current schema can’t store it.
2. **Recommended usage pattern**:
   - query/document prefixes (`"query: ..."`, `"passage: ..."`, etc.)
   - normalization requirement (e.g., L2-normalize embeddings before indexing/search)
   - pooling strategy if using raw `transformers` (CLS vs mean pooling vs special pooling head)
3. **Licensing / use constraints** for your intended use (personal, team, commercial).
4. **Hardware expectations** (CPU viability, GPU requirement, quantization recommendations).
5. **`sentence-transformers` compatibility**:
   - Is it published as a SentenceTransformers model?
   - If not: do you need `transformers` + custom pooling code?
6. **Max input length / truncation behavior** (important for long-ish notes or source summaries).

## Rough Local Hardware Cost (order-of-magnitude)

For models where the name implies parameter count (e.g., `300m`, `350M`, `0.6B`), the *weights alone* are roughly:

| Parameter scale | FP16 weights | INT8 weights | 4-bit weights |
|----------------|--------------|--------------|---------------|
| 300M | ~0.6 GB | ~0.3 GB | ~0.15 GB |
| 350M | ~0.7 GB | ~0.35 GB | ~0.18 GB |
| 600M | ~1.2 GB | ~0.6 GB | ~0.3 GB |

These are back-of-the-envelope numbers (they exclude activation memory, tokenizer/model overhead, and batching effects). Real RAM/VRAM usage is higher, especially at larger batch sizes.

### Popularity (downloads as a proxy)

Download counts are not “quality”, but they’re useful as a proxy for:

- ecosystem maturity (more examples/issues solved)
- likelihood of stable usage patterns

As of 2026-01-21 (HF `downloads` field):

- `sentence-transformers/all-MiniLM-L6-v2`: **142,396,889** downloads
- `sentence-transformers/all-mpnet-base-v2`: **21,662,171** downloads
- `sentence-transformers/all-MiniLM-L12-v2`: **2,724,889** downloads
- `mixedbread-ai/mxbai-edge-colbert-v0-32m`: **43,126** downloads

## Relative Speed & Index Size (Reality Check-relevant)

### What dominates latency?

- **Dense retrieval**: query latency is usually dominated by **query embedding generation** (model forward pass). ANN search in the vector DB is typically fast.
- **ColBERT retrieval**: query latency includes query embedding generation *and* **late-interaction scoring/search** (more expensive than single-vector similarity, mitigated by specialized indexes like PLAID/Voyager).

### What dominates storage?

- **Dense**: one vector per record → roughly `dim * 4 bytes` per record (float32).
- **ColBERT**: many vectors per document (token-level) → much larger raw footprint; practical systems rely on compressed / structured indexes.

### Model “size + shape” snapshot

The intent of this table is **speed intuition**, not exact benchmarking.

| Model | Family | Params (approx) | Representation | Max length (from card/config) | License / gating | Speed intuition |
|------:|--------|-----------------|----------------|-------------------------------|------------------|----------------|
| `all-MiniLM-L6-v2` | Dense | 22.7M | 384-dim vector | 256 tokens | Apache-2.0 | Fast CPU baseline; great default for “claims search”. |
| `all-MiniLM-L12-v2` | Dense | 33.4M | 384-dim vector | 128 tokens | Apache-2.0 | Still small; but shorter max length makes it a worse fit beyond short text. |
| `all-mpnet-base-v2` | Dense | 109M | 768-dim vector | 384 tokens | Apache-2.0 | Slower than MiniLM; quality often better. |
| `nomic-embed-text-v2-moe` | Dense (MoE) | 475M total / 305M active | 768-dim vector (truncate→256 supported) | 512 tokens | Apache-2.0 (needs `trust_remote_code`) | Potentially strong quality; heavier ops footprint (custom code, MoE deps). |
| `modernbert-embed-large` | Dense | 395M | 1024-dim vector (truncate_dim supported) | 8192 tokens | Apache-2.0 | Heavier than MiniLM; attractive if you truly need long-context dense embeddings. |
| `Qwen3-Embedding-0.6B` | Dense | 596M | 1024-dim vector (MRL dims 32–1024) | 32k tokens | Apache-2.0 | Likely slow on CPU; good candidate if GPU + long context matters. |
| `embeddinggemma-300m` | Dense | 303M | 768-dim vector (MRL truncate 512/256/128) | 2048 tokens | Gemma / gated manual | On CPU: much slower than MiniLM; note float16 activations unsupported (use fp32/bf16). |
| `stella_en_400M_v5` | Dense | 435M | 1024-dim vector (MRL dims via `2_Dense_*`) | 512 tokens recommended (trained at 512) | MIT (needs `trust_remote_code`) | Likely GPU-oriented; on CPU it’s noticeably slower than mid-size dense models. |
| `granite-embedding-278m-multilingual` | Dense | 278M | 768-dim vector | 512 tokens | Apache-2.0 | Similar CPU speed class to mpnet/e5-base; multilingual with enterprise-friendly license. |
| `mxbai-edge-colbert-v0-32m` | ColBERT | 31.9M | per-token vectors (proj dim 64) | docs up to 32k tokens (card) | Apache-2.0 | Very fast *encoder*, but late-interaction indexing/search is a bigger system choice. |
| `GTE-ModernColBERT-v1` | ColBERT | 149M | per-token vectors (dim 128) | doc 300 tokens default (configurable) | Apache-2.0 | Heavier than edge ColBERT; likely higher quality. |
| `LFM2-ColBERT-350M` | ColBERT | 353M | per-token vectors (dim 128) | doc 512 / query 32 (card) | LFM Open License v1.0 | Likely high quality; license may be a blocker for some uses. |

### Measured CPU throughput (this machine)

These numbers are for **relative intuition only** (CPU-only; batch sizes: 16 for “short”, 4 for “chunk”; `short_n=64`, `chunk_n=16`, `chunk_sentences=40`). Raw runs are captured in `_dev/perf.txt`.

Reproduce with:

```bash
uv run python _dev/embedding_shootout.py --offline --devices cpu --tablefmt github
```

Important environment note (this machine / Strix Halo):

- Running via system `python` with a **ROCm** Torch build produced **~100× slower CPU embeddings** at default thread settings (e.g., MiniLM short ~`8 q/s` vs `~1300 q/s` under `uv run`).
- Reality Check clamps CPU embedding threads by default (`REALITYCHECK_EMBED_THREADS=4`, which sets `OMP_NUM_THREADS`, etc). If you are in an environment where CPU embeddings are unexpectedly slow, try `REALITYCHECK_EMBED_THREADS=4` or `8` (values like `32` can collapse performance).

CPU summary (from `_dev/perf.txt`, `uv run`, RSS is process peak):

| Model | Dim | Max seq | RSS peak | Short q/s | Chunk q/s |
|------:|----:|--------:|---------:|----------:|----------:|
| `all-MiniLM-L6-v2` | 384 | 256 | 890 MB | 1479.6 | 116.9 |
| `all-mpnet-base-v2` | 768 | 384 | 1307 MB | 250.4 | 13.5 |
| `granite-embedding-278m-multilingual` | 768 | 512 | 2357 MB | 286.7 | 14.2 |
| `embeddinggemma-300m` | 768 | 2048 | 1492 MB | 139.4 | 12.2 |
| `gte-multilingual-base` | 768 | 8192 | 2549 MB | 181.3 | 10.9 |
| `stella_en_400M_v5` | 1024 | 512 | 2572 MB | 52.8 | 3.4 |

Interpretation:
- `all-MiniLM-L6-v2` is in a different speed class on CPU and is the only one listed that is drop-in for the current `vector[384]` schema.
- “Chunk” throughput clusters around ~`10–15 q/s` for the 768-dim models here; if you index lots of long text on CPU, model choice will materially change wall-clock time.
- Max sequence length and truncation dominate perceived speed: MiniLM looks especially fast because it truncates at `256` tokens; long-doc search still needs chunking regardless.
- `stella_en_400M_v5` looks CPU-hostile (slow + high RSS); treat it as “GPU-first” unless proven otherwise.

## How These Models Fit Reality Check’s Use Cases

Reality Check uses embeddings for:

- **Claims**: short, precise propositions (often 1–3 sentences).
- **Sources**: title + (optional) bias notes; later likely abstract/summary snippets.
- **Chains**: name + thesis (and potentially concatenated step claims in the future).
- **Analyses / notes** (likely): long Markdown documents (source analyses, syntheses, dashboards).

This tends to favor **retrieval-optimized** embedding models over generic encoders.

### Primary use cases to design for

1. **Find relevant claims fast** (interactive “/search” while thinking)
2. **Find “near-duplicates” / paraphrases** (merge or link)
3. **Find supporting/contradicting claims** (candidate generation for relationships)
4. **Find relevant sources** by topic (title/abstract/notes)
5. **Search long analyses** (if/when you index full `analysis/` Markdown)

Dense embeddings are typically excellent for (1–4). For (5), you usually need **chunking** (dense) or **late-interaction** (ColBERT).

### Dense embeddings: recommended path for v0.1.x / v0.2

If the goal is “improve search quality soon” without redesigning search:

- Prefer a **dense** embedding model with strong retrieval orientation.
- Ensure we can either:
  - keep `vector[384]` (choose a model that outputs 384), or
  - plan a schema migration path to a new vector size.

### ColBERT: promising, but likely a Phase 3+ architecture change

ColBERT-style models may improve retrieval quality (especially for longer texts and lexical precision), but adopting them cleanly likely means:

- New storage for per-token vectors, and
- A different search routine than LanceDB “one vector column → ANN”.

If we want ColBERT, treat it as a distinct “search backend” rather than just swapping models.

### Reality Check-specific take (given typical data shape)

- **Claims are short** → dense models do very well; ColBERT is usually unnecessary here.
- **Analyses / notes can be long** → don’t store “one vector per full doc”; use **chunking** (dense) or a ColBERT backend.

## Concrete Facts From Model Cards (summary)

These are the Reality Check-relevant “gotchas” surfaced directly from the model cards (as of 2026-01-21).

### Dense candidates

- `sentence-transformers/all-MiniLM-L6-v2`
  - Dense, `384` dims, `max_seq_length=256`, ~`22.7M` params
  - Extremely popular baseline (142M downloads)
- `nomic-ai/nomic-embed-text-v2-moe`
  - Dense, `768` dims (Matryoshka truncation down to `256` supported)
  - Max seq length `512`
  - Requires `trust_remote_code=True`
  - Requires **prefixing**: `search_query:` vs `search_document:` (or ST `prompt_name`)
  - Model card lists **475M total params / 305M active during inference**
- `lightonai/modernbert-embed-large`
  - Dense, `1024` dims (Matryoshka truncation supported via `truncate_dim`)
  - Max seq length `8192` (notably better for long text)
  - Recommends prefixing: `search_query:` / `search_document:`
- `Qwen/Qwen3-Embedding-0.6B`
  - Dense, `1024` dims; **MRL supports user-defined output dims** (32–1024 per model card)
  - Context length `32k`
  - Recommends query prompt usage (`prompt_name="query"`) and cosine similarity with normalization
- `google/embeddinggemma-300m`
  - Dense, `768` dims; max input context length `2048` tokens
  - **MRL truncation** supported (model card: `512`/`256`/`128`; SentenceTransformers `truncate_dim=256` works)
  - Query/document separation is built in (`encode_query()` vs `encode_document()`)
    - Query prompt prefix: `task: search result | query: `
    - Document prompt prefix: `title: none | text: `
  - Model card note: **float16 activations not supported** (use float32 or bfloat16)
  - **Gated** (manual) under Gemma terms
- `NovaSearch/stella_en_400M_v5`
  - Dense, `1024` dims by default; max seq length `512` (model card recommends 512; trained at 512)
  - Prompted queries: `s2p_query` (retrieval) and `s2s_query` (STS); documents do not need prompts
  - MRL dimensions are implemented via per-dimension linear weights directories (`2_Dense_256`, `2_Dense_768`, `2_Dense_1024`, …)
  - Requires `trust_remote_code=True` (pin a revision for safety/reproducibility)
- `ibm-granite/granite-embedding-278m-multilingual`
  - Dense, `768` dims; max seq length `512`; CLS pooling
  - Apache-2.0; multilingual (12 languages listed in model card)

### ColBERT / late-interaction candidates

- `mixedbread-ai/mxbai-edge-colbert-v0-32m`
  - Tiny ColBERT (32M params), projection dim `64`, PyLate-compatible
  - Model card explicitly compares against `all-MiniLM-L6-v2`:
    - BEIR avg reported: `0.521` vs `0.419` (MiniLM)
    - LongEmbed avg reported: `0.849` vs `0.298` (MiniLM)
  - Supports documents “up to 32,000 tokens” per model card
- `lightonai/GTE-ModernColBERT-v1`
  - ColBERT, token vectors `128` dims, PyLate-compatible
  - Default doc length `300` tokens; query length `32`; can set `document_length=8192` (with caveats)
- `LiquidAI/LFM2-ColBERT-350M`
  - ColBERT, token vectors `128` dims, similarity MaxSim
  - Document length `512` tokens; query length `32`
  - License is “LFM Open License v1.0” (not Apache/MIT)

## Decision Framework (what to choose)

Choose based on your constraints:

### If you want “fast and simple now”

- Pick a **dense** model that is:
  - easy to run locally,
  - compatible with `sentence-transformers`, and
  - either outputs 384 dims or you’re willing to migrate the schema.

### If you want “best quality and can spend compute”

- Consider the larger dense model class (e.g., `Qwen/Qwen3-Embedding-0.6B`) if you have GPU (or acceptable CPU latency with quantization).

### If you want “precision retrieval for long docs”

- Put ColBERT candidates on a separate track; do not treat them as a simple `REALITYCHECK_EMBED_MODEL` swap.

### Practical recommendation (no schema/index commitments yet)

- Start with **dense + chunking** as the baseline architecture (it’s simpler than ColBERT and handles long text well).
- If you still need higher precision on long documents, add ColBERT as:
  - a **reranker** (top-k dense → rerank with ColBERT), or
  - a **separate long-doc index** (ColBERT only for `analysis/` content).

## Beyond Embeddings (future quality upgrades)

If dense retrieval quality isn’t sufficient even with a better embedding model:

- **Hybrid search**: combine keyword/BM25 with vectors (helps rare terms, IDs, and proper nouns).
- **Local reranking**: retrieve top-k with vectors, then rerank with a cross-encoder (often a large quality boost for a small latency cost).

These are intentionally out of scope for “swap embedding model” changes, but they’re relevant if the goal is “reliably find the right claim” rather than “rough semantic proximity”.

## Migration & Ops: Switching Embedding Models Safely

## Practical “Probe” Steps (dimension, speed, normalization)

Once a model is available locally (cached/downloaded), the fastest way to answer “is this drop-in?” is:

1) **Can `sentence-transformers` load it?**  
2) **What embedding dimension does it produce?**  
3) **Does it recommend normalization / query prefixes?**

Minimal probe (will download on first run unless already cached):

```bash
uv run python - <<'PY'
from sentence_transformers import SentenceTransformer

model_id = "REPLACE_ME"
model = SentenceTransformer(model_id)  # some models may require trust_remote_code=True

vec = model.encode(["test"], normalize_embeddings=False)
print("shape:", getattr(vec, "shape", None))
print("first-5:", vec[0][:5].tolist() if hasattr(vec[0], "tolist") else vec[0][:5])
PY
```

If the printed shape is `(1, 384)` and the model is retrieval-oriented, it is *closer* to drop-in for the current `vector[384]` schema (still confirm any prefix/normalization requirements).

### Offline mode knobs (Hugging Face)

For “local-only after initial download”, standard knobs include:

- `HF_HUB_OFFLINE=1` (fail fast if a file isn’t cached)
- `HF_HOME=/path/to/cache` (centralize model cache)
- `TRANSFORMERS_CACHE=/path/to/cache` (older pattern; still seen)
- Pin a model revision (commit hash) in documentation/config to avoid silent upgrades.

Reality Check should eventually record the model id + revision in project config to keep embeddings reproducible across machines.

### Recommendation: record an “embedding signature” in the project config

To keep projects reproducible, add an embedding config to `.realitycheck.yaml` (schema TBD), e.g.:

- model name (HF id)
- embedding family (dense vs colbert)
- embedding dim
- normalization (true/false)
- query/document prefix conventions (if any)

This avoids “mystery embeddings” where two projects use different models but share the same DB schema.

### Schema migration options (dense models)

If the new model’s embedding dim differs from 384, you need one of:

1. **New DB (simplest)**: re-init a new LanceDB directory with the new schema; re-import; re-embed.
2. **New column**: add a second vector column per table (e.g., `embedding_v2`) with the new dimension (requires code + schema updates).
3. **New tables**: create parallel tables keyed by `id` just for embeddings per model (clean separation; slightly more code).

Reality Check should pick one approach and document it before standardizing on a new default.

## How to Evaluate Models (Reality Check-oriented)

Reality Check has built-in weak labels you can use for retrieval evaluation:

- claim relationships: `supports`, `contradicts`, `depends_on`, `modified_by`
- chain membership: claims within the same chain
- source linkage: claims that share a `source_id`

Suggested evaluation loop:

1. Embed the DB with a candidate model.
2. Create a query set from existing claims (e.g., claim text → retrieve its related claims).
3. Measure retrieval quality (Recall@k, MRR) using those structural relationships as “should be near”.
4. Measure latency on your target machine (embed throughput, search latency).

Minimum acceptance:

- “Related claim” queries consistently surface true relations in top-k.
- Search doesn’t become so slow that it changes workflow behavior.

## Immediate Engineering Implication (for Phase 2 stability)

Even if we *don’t* change models yet, Phase 2 tests should not require embedding downloads. The CLI defaults to embedding generation, so tests should explicitly disable embeddings (or the CLI should respect `REALITYCHECK_EMBED_SKIP=1`).

## Open Questions / TODO

- Decide the canonical `.realitycheck.yaml` keying for embeddings (and align with `docs/PLAN-separation.md`).
- Decide a migration strategy for changing embedding dimensionality (new DB vs new vector column vs separate embedding tables).
- Decide whether “ColBERT search” is in scope for the near term, or explicitly deferred.
