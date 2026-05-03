# configs/

Brand configuration files for agentsHQ clients and projects.

**What goes here:** `brand_config.<slug>.json` files consumed by `orchestrator/studio_brand_config.py` and related Studio pipeline scripts.

**What does NOT go here:** credentials, .env values, deployment configs, or any file not directly consumed by the Studio brand pipeline.

**Move out condition:** A brand config moves to `zzzArchive/` when the associated client project is closed or superseded.
