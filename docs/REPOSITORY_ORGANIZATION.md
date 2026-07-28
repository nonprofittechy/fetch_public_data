# Repository organization

The repository follows a paper-first layout:

1. `datasets/` contains every publicly distributed dataset named by the paper.
2. Dataset-specific provenance stays beside the dataset.
3. `scripts/` contains shared deterministic and model-backed utilities.
4. `studies/` contains derived experiments that consume those datasets.
5. `prompts/`, `resources/`, and `configs/` contain shared frozen inputs.
6. `docs/` contains cross-study synthesis rather than executable artifacts.

D1 keeps its full labeling audit and review application beside the canonical
355-row paper file. D2 keeps authored sources, candidates, runners, the narrow
FETCH pipeline snapshot, and results together because separating those pieces
would make its provenance harder to follow.

Generated caches, virtual environments, local logs, credentials, private raw
inputs, and temporary repair material are not part of the public audit surface
and remain ignored.
