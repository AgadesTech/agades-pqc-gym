---
title: Agades PQC Gym Agent Environment
sdk: gradio
app_file: app.py
python_version: "3.11"
license: apache-2.0
colorFrom: gray
colorTo: blue
pinned: false
tags:
  - agent-environment
  - reinforcement-learning
  - post-quantum-cryptography
  - cryptanalysis
short_description: Public-safe AttackPlan Agent Environment for Agades PQC Gym.
---

# Agades PQC Gym Agent Environment

This Space exposes a public-safe Agent Environment for Agades PQC Gym. It lets
users inspect task observations, score candidate AttackPlan JSON, and view
public rollout traces.

The environment trains or evaluates agents to produce and validate conforming
AttackPlans. It does not claim real-world PQC breaks, does not execute
arbitrary code, does not accept live targets, and does not publish private RL traces,
reviewer annotations, prompts, model weights, or serious-research rollouts.

## Public Surfaces

- `app.py` launches the Gradio UI.
- `requirements.txt` installs the public package and stays compatible with the
  Gradio version injected by Hugging Face Spaces.
- `dataset/attack_plans.jsonl` contains public toy/schema-only AttackPlan rows.
- `dataset/task_metadata.jsonl` contains task constraints for scoring.
- `dataset/rl_rollouts.jsonl` contains public example rollout traces.
- `docs/` and `formal/lean/` contain the public formal runtime bundle required
  by the Agent Environment reward and formal artifact binding.
- `space_manifest.json` records the audited Agent Environment contract.
- `collection_manifest.json` records the related public Hugging Face surfaces.

## Guardrails

- Outputs are toy/demo verifier and reward signals, not security claims.
- Unsupported schema-only families remain explicit zero-reward safety checks.
- Private training data, RL traces, reviewer notes, prompts, adapters, and model
  weights must stay outside this Space.
- Public publication requires release review after the local manifest and smoke
  gates pass.
