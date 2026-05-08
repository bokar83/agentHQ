# RCA: Studio Blotato Publisher — 2026-05-08

**Root cause:** Drive `webViewLink` (`/file/d/{ID}/view`) passed as `mediaUrls` to Blotato. Files were private (no public permission) + wrong URL format. Blotato media fetcher got 403/HTML instead of video bytes → "Failed to read media metadata."

**Fix applied:**
- `orchestrator/studio_blotato_publisher.py` — before `publish()`: extract Drive file ID, call `ensure_public(file_id)`, convert URL to `https://drive.usercontent.google.com/download?id={ID}&export=download&confirm=t`. Commit 7a03dd1.
- `orchestrator/drive_publish.py` — added `audit_studio_pipeline_videos()` + `audit-videos` CLI. 14/15 Pipeline DB Drive assets were private, all fixed. Commit 7a03dd1.
- `orchestrator/studio_render_publisher.py` — added `-r {fps} -vsync cfr` to `_concat_clips` ffmpeg command. TikTok rejects VFR; renders had avg_frame_rate≠r_frame_rate. Commit 31a1fe6.

**Success criterion verified:**
`docker logs orc-crewai | grep 'BLOTATO poll'` →
- X: published in 12.3s `https://x.com/UnderTheBaobab_/status/2052835728480932139`
- Instagram: published in 60.0s `https://www.instagram.com/reel/DYFvgHlkgoS/`
- YouTube: published in 12.9s `https://www.youtube.com/watch?v=AiF0vZh7AgU`
- TikTok: still failing (CFR fix deployed, will validate on next render cycle)

**Backlog requeue:** 8 `publish-failed` records reset to `scheduled`, staggered 2/day across May 8–11 (account warming protocol).

**Never-again rule:** All Drive files used as Blotato `mediaUrls` MUST be made public + converted to usercontent direct-download URL before the API call. Run `audit-videos` after any bulk pipeline DB import.

**Open issue:** Instagram "Sessions for the user are not allowed because the user is not a confirmed user" (May 6 posts, account IDs 45174/45176/45755) — Meta requires account email/phone confirmation after connecting to third-party API. Manual fix: log into each IG account, resolve verification prompt in Meta Business Suite.

**Memory update:** yes — feedback_studio_blotato_drive_url.md
