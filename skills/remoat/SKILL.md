---
name: remoat
description: Automates the connection between the Antigravity IDE and Telegram bot through the Remoat bridge. Triggers on "remoat", "antigravity bridge", "connect IDE to Telegram", "remoat ignite", "wire Antigravity".
---

# Remoat Ignite — Automated Launch

## Description
This skill automates the connection between the AntiGravity IDE and your Telegram bot via the Remoat bridge.

## Setup & Use
Run the following command in any terminal to launch the system:
`powershell d:\Ai_Sandbox\agentsHQ\skills\remoat\ignite.ps1`

## Implementation Details
- Launches `remoat open` to start the IDE.
- Waits for the CDP port (9222 or 7800) to become available.
- Launches `remoat start` in the background to connect the Telegram bot.
