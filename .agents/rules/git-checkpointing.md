# DIA Git Checkpoint Protocol

Git is the rollback and recovery mechanism for autonomous development.

The agent must use Git continuously.

## Before risky or major changes

Before beginning any substantial modification, create a checkpoint commit
containing the last known-good state.

Example:

git add -A
git commit -m "checkpoint: before <description>"

Never begin a major architectural change without a recoverable checkpoint.

## After successful milestones

After implementing a coherent feature and passing relevant tests:

git add -A
git commit -m "<type>: <description>"

Examples:

feat: implement dataset ingestion
feat: add image quality analyzer
feat: implement duplicate detection
feat: add unified health scoring
feat: add C2 feasibility experiment

## Failed experiments

If an experiment is unsuccessful:

- preserve useful experimental information
- do not overwrite the last known-good implementation
- use Git to revert or branch when appropriate
- document the failure in PROJECT_STATE.md

## Push policy

After every stable milestone commit, push to origin.

Before pushing:
- ensure no secrets are staged
- ensure datasets are ignored
- ensure generated large artifacts are ignored
- inspect git status
- inspect the commit summary

## Large experiments

Do NOT commit:
- datasets
- model weight files
- large embeddings
- generated caches
- local virtual environments
- secrets

Store metadata, configuration, scripts and reproducibility information
instead.

## Rollback

When a substantial change causes persistent regressions:

1. identify the last known-good commit
2. preserve useful debugging information if necessary
3. revert or reset to the known-good state
4. rerun tests
5. continue from the recovered state

Never delete Git history merely to hide a failed experiment.

## Autonomy

Do not ask the human for permission to make ordinary Git commits or pushes.

Git checkpointing is part of the autonomous workflow.
