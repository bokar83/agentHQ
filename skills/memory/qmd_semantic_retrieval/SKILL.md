---
name: qmd_semantic_retrieval
description: >
  Local semantic memory retrieval for agentsHQ using QMD. Use when Qdrant is
  unavailable, when local-only semantic search is preferred, or when indexing
  agent logs and session notes into a zero-infra on-device backend.
allowed-tools: Read, Write, Bash
---

# QMD Semantic Retrieval

## Prerequisites

- Node.js >= 16
- At least 3 GB free disk space

## Install

QMD's upstream README currently documents the npm package as `@tobilu/qmd`,
while the installed CLI command is still `qmd`.

```bash
npm install -g @tobilu/qmd
```

If package naming changes upstream, verify the current install command in the
QMD repository README before installing.

## Config

Point QMD at `workspace/memory-index/` as the documents root for local memory.

Example:

```bash
cd workspace/memory-index
qmd collection add . --name memory-index
qmd embed
```

Copy or sync memory documents into that directory so QMD can index them.

## Usage Pattern

Run hybrid semantic retrieval with:

```bash
qmd query "search terms"
```

Expected output includes:

- file path
- line number
- matching snippet

The wrapper in `orchestrator/memory_qmd.py` parses lines in the form:

```text
filepath:linenum: snippet text
```

## Gotcha: First Query

The first semantic query can download about 2 GB of local models and may take a
few minutes. Do not interrupt it while models are being pulled.

## Gotcha: Index Refresh

Newly copied content may take up to 5 minutes to appear, depending on QMD's
index refresh cadence.

## Verify

QMD is working correctly when query output includes both:

- a file path
- a line number

Example success shape:

```text
workspace/memory-index/session-2026-04-26.md:42: user approved the deployment plan
```
