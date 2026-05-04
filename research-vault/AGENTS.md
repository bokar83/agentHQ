# research-vault/

**Purpose:** Per-channel intelligence dossiers injected into Studio script crews at production time. Scripts read niche signal, competitor gaps, and proven hooks before writing.

**What goes here:** Channel dossiers (`dossiers/<channel>.md`) containing trend signal, competitor analysis, hook patterns, and YMYL compliance notes per niche.

**What does NOT go here:** Final scripts, rendered assets, Pipeline DB exports, or general research not tied to a specific Studio channel.

**Graduation/archive trigger:** If a channel is killed (M8 channel-kill protocol), its dossier moves to `zzzArchive/research-vault/`.

**Live-mount:** `dossiers/` is read by `studio_script_generator.py` at production time via `_load_dossier()`. Do not rename or restructure without updating the channel dossier map in that module.

**Reference:** `docs/GOVERNANCE.md` + `docs/AGENT_SOP.md` Folder Governance.
