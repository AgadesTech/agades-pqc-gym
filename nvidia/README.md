# NVIDIA / Accelerator Manifest

This directory contains the public accelerator-facing manifest for Agades PQC Gym.

`accelerator_manifest.json` describes the current public evaluation surface, the
checked-in Hugging Face and Prime artifacts, safety constraints, and the future
GPU acceleration boundary. The current MVP workloads are CPU/verifier plumbing
tasks across the public toy/downscaled family surface, including the
HQC-inspired circulant-erasure fixture decoder; that surface is not an HQC
result, and GPU work is explicitly marked as future reviewed reproduction work.
The manifest also points to
`hf/space_manifest.json`, `hf/collection_manifest.json`, and
`prime_intellect/verifiers_environment/prime_manifest.json`, plus the flat
`public/run_export/manifest.json` run export, so accelerator-facing review sees
the same public contracts used by the HF Space, HF Collection, Prime
environment, and public run-ledger surface.

Regenerate the manifest with:

```bash
uv run agades-pqc nvidia-manifest --out nvidia/accelerator_manifest.json
```
