---
name: mermaid_diagrammer
description: Generates PNG, SVG, or PDF diagrams from Mermaid syntax using local Mermaid-CLI.
when_to_use: When an agent needs to draw a flowchart, org chart, architecture diagram, or thought process map and output it to a file.
---

# Mermaid Diagrammer Skill

This skill allows any agent to convert Mermaid JS code blocks into physical image files (`.png`, `.svg` or `.pdf`) using the locally installed `@mermaid-js/mermaid-cli`.

This fulfills the requirement to "automatically map out thought processes and decisions" dynamically.

## Usage
Agents can import `generate_mermaid_diagram` from `skills.mermaid_diagrammer.skill`.
