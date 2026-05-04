# IG & TikTok Launch Kit : Execution Prompt

**Target Batch:** M1 Channels (Under the Baobab, AI Catalyst, First Generation Money)  
**Goal:** Initialize social presence and perform warm-up research to avoid shadow-banning.

---

## 1. Context & Assets
- **Channel 1: Under the Baobab** (African Folktales/Culture)
  - Assets: `05_Asset_Library/under_the_baobab/M2_Brand_Identity/`
- **Channel 2: AI Catalyst** (AI Strategy/HR)
  - Assets: `05_Asset_Library/ai_catalyst/M2_Brand_Identity/`
- **Channel 3: First Generation Money** (Autonomous Test Channel)
  - Assets: `05_Asset_Library/first_generation_money/M2_Brand_Identity/`

## 2. Agent Task: Account Initialization
For each channel, execute the following:
1. **Bio Engineering:** Draft 3 variations of a bio (IG and TikTok formats) that align with the brand voice defined in `configs/brand_config.<channel_id>.json`.
2. **Handle Verification:** Confirm availability of `@<Handle>` (or fallback) across IG and TikTok.
3. **Profile Setup Prep:** Organize the avatar, banner, and voice samples from the M2 asset library for manual or automated upload.

## 3. Agent Task: Warm-up Research
1. **Niche Velocity Check:** Analyze top 5 creators in each niche on IG Reels and TikTok.
   - What is their posting frequency?
   - What hashtags are they currently trending for?
2. **Warm-up Protocol:** Define a 14-day "Account Warm-up" schedule.
   - **Days 1-3:** Engagement only (no posting).
   - **Days 4-7:** One post every 48 hours.
   - **Days 8-14:** Daily posting (one per platform).

## 4. Delivery
- Save the bio drafts to `docs/roadmap/studio/m4/launch_kit_<channel_id>.md`.
- Update the `operating-snapshot.md` table with the new handles and status.
- **UPDATES:** Update the Studio Roadmap (`docs/roadmap/studio.md`) with M4 progress as well as the Notion Task DB as the progress occurs (vs all at the end).
