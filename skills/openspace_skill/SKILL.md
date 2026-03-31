# OpenSpace: Self-Evolving Skill System

Autonomous performance optimization and skill repair engine.

## Overview

OpenSpace allows Catalyst Works agents to learn from their own executions. It monitors task performance, identifies patterns, and automatically updates skill definitions to improve quality and efficiency.

## Capabilities

| Capability | Description |
|---|---|
| **Self-Fixing** | Detects code/logic errors in skills and proposes fixes. |
| **Optimization** | Analyzes execution traces to reduce token usage and latency. |
| **Auto-Evolution** | Proposes new skills based on repeating task patterns. |

## Usage

This skill runs **automatically** in the background after every task. Agents do not need to trigger it manually unless they recognize a specific skill is failing.

### Manual Commands

- `evolve`: Force an evolution analysis on a specific task result.
- `fix_skill`: Attempt to repair a known broken skill.
