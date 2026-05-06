---
name: mermaid_diagrammer
description: Generates PNG, SVG, or PDF diagrams from Mermaid syntax using local Mermaid-CLI.
when_to_use: When an agent needs to draw a flowchart, org chart, architecture diagram, or thought process map and output it to a file.
---

# Mermaid Diagrammer Skill

This skill allows any agent to convert Mermaid JS code blocks into physical image files (`.png`, `.svg` or `.pdf`) using the locally installed `@mermaid-js/mermaid-cli`.

This fulfills the requirement to "automatically map out thought processes and decisions" dynamically.

## Spec-Before-Render Rule

Before generating any Mermaid syntax, emit a compact spec block. Only render after the spec is confirmed (or auto-proceed if running autonomously).

```
Diagram spec:
  Title: <one-line diagram title>
  Type: flowchart | sequenceDiagram | classDiagram | erDiagram | gantt
  Nodes: <comma-separated list of main nodes/entities>
  Connections: <key relationships in plain language>
  Layout: TD (top-down) | LR (left-right) | BT | RL
  Output: <file path, e.g. research/arch-diagram.png>
```

Why: generates diagrams that match what was asked instead of what the LLM defaulted to. Catches scope mismatch before the render CLI call.

## Usage
Agents can import `generate_mermaid_diagram` from `skills.mermaid_diagrammer.skill`.
