# agentsHQ Inventory

_Generated: 2026-05-12T04:21:18+00:00_

Read this when you need to know what already exists in agentsHQ before proposing a new skill, tool, or crew. Regenerate via `python scripts/inventory_snapshot.py`.

## Skills (80)

| Slug | Description (truncated) |
|---|---|
| `3d-animation-creator` | Takes a video file (e.g. a product deconstruction/assembly animation, before/after transformation) and builds a production-quality website with scroll-driven an |
| `3d-website-building` | Builds premium 3D animated scroll-driven websites by chaining 4 skills in sequence: website-intelligence (competitive research + HTML report), image-generator ( |
| `active` | Index for the active skill workspace — lists in-progress mirrored skills under skills/active/. Use when the user asks "what's in the active workspace", "show me |
| `agentshq-absorb` | Use when evaluating any GitHub repo, live URL, MCP server, n8n workflow, PDF, raw doc, or local skill for inclusion in agentsHQ. Auto-fires on bare GitHub URLs  |
| `apollo_skill` | Agent-driven Apollo.io lead discovery for Catalyst Works Consulting, including Utah lead search, email reveal workflows, and owner lookup by company name. Trigg |
| `banner-design` | "Design banners for social media, ads, website heroes, creative assets, and print. Multiple art direction options with AI-generated visuals. Actions: design, cr |
| `boub_voice_mastery` | Ensures AI-generated content sounds human, earned, direct, and specifically aligned with Boubacar Barry's voice. Triggers on "voice check", "does this sound lik |
| `boubacar-prompts` | Use when improving, rewriting, or optimizing any AI prompt — agent backstories, task descriptions, system prompts, or one-off queries. Triggers on "improve this |
| `boubacar-skill-creator` | Use when creating a new Claude Code skill, improving an existing skill, or capturing a repeatable workflow as a skill — specifically when working in Boubacar's  |
| `brand` | Brand voice, visual identity, messaging frameworks, asset management, brand consistency. Activate for branded content, tone of voice, marketing assets, brand co |
| `CatalystWorksSkills` | Index for Catalyst Works practice-specific skills — agent-teams, news, sheet-mint, and sheet-mint-workspace. Use when the user asks about CW-internal skill pack |
| `cli_hub` | "Search the community CLI-Hub for pre-built agent-native CLIs (GIMP, Blender, OBS, etc.) and install them. Triggers on \"cli hub\", \"find a CLI\", \"agent CLI\ |
| `client-intake` | First-touch intake for new Catalyst Works clients and for Boubacar's own brand work. Runs a Steven Bartlett style brand-discovery interview, captures voice/audi |
| `clone-builder` | Takes a Clone Targets Notion record by name and executes the full build pipeline: fetch Launch Brief → profile the target site → generate copy in target languag |
| `clone-scout` | Scouts high-traffic websites and web apps that can be cloned and monetized via AdSense. Starts from verified traffic data (SimilarWeb, Semrush, Ahrefs estimates |
| `cold-outreach` | Proven cold email templates for Catalyst Works Consulting. Two variants — sector-specific (when you know the prospect's industry) and size-based (when you're mo |
| `community` | Index for the community skills repo clone — read-only mirror of an external skills marketplace catalog (apps, plugins, skills, tools). Use when looking for comm |
| `content_multiplier` | Takes ONE approved content source (article URL, YouTube video, post, PDF, raw text) and generates 9 atomic content pieces aligned to Boubacar's voice and the 8  |
| `coordination` | Coordination helpers for claiming, completing, and tracking concurrent agent work. |
| `council` | Sankofa Council trigger and workflow documentation for high-stakes strategic review tasks. |
| `ctq-social` | Use when reviewing, rewriting, or quality-checking any social media post or article draft for Boubacar Barry before publishing. Triggers on "review this post",  |
| `cw-automation-engagement` | Operationalizes the Catalyst Works AI automation delivery engagement. Phase 3 scope: find a free case study client, build their automation, document results, ca |
| `deploy-to-vercel` | "BOUBACAR RULE: Vercel = preview and mobile testing ONLY. NOT for production. Use when user says 'get me a preview link', 'share with client for review', or 'te |
| `design` | "Comprehensive design skill: brand identity, design tokens, UI styling, logo generation (55 styles, Gemini AI), corporate identity program (50 deliverables, CIP |
| `design-audit` | Score any visual artifact (local HTML, PDF, slide, banner, social photo, OR live URL, OR multi-page live site) against the 5-dimension Impeccable rubric. Docume |
| `design-system` | Token architecture, component specifications, and slide generation. Three-layer tokens (primitive→semantic→component), CSS variables, spacing/typography scales, |
| `email_enrichment` | Email enrichment tool. Agent-internal only. enrichment_tool.enrich_missing_emails() imported by scheduler.py and tools.py. DO NOT archive. |
| `engagement-ops` | Run client engagements with consistent rigor. Use when starting, prepping, journaling, tracking, or closing any Catalyst Works client engagement (Signal Session |
| `forge_cli` | Core Notion client + Forge KPI/page-builder. Agent-internal only -- not Boubacar-invoked. notion_client.py (NotionClient) imported by atlas_dashboard, crews, gr |
| `frontend-design` | Use when creating, updating, or reviewing any website, landing page, or HTML/CSS artifact. Must run before writing any code. Applies the Volta design standard a |
| `github_skill` | GitHub automation tool. Agent-internal only. github_tool.create_repo/create_issue/create_file imported by tools.py. DO NOT archive. |
| `gsap` | GSAP animation reference for HyperFrames. Covers gsap.to(), from(), fromTo(), easing, stagger, defaults, timelines (gsap.timeline(), position parameter, labels, |
| `hormozi-lead-gen` | Use when the operator asks for lead-gen work, cold outreach, warm reactivation, lead magnets, follow-up sequences, ICP definition, list-building, hooks, or offe |
| `hostinger-deploy` | "THE production deploy path for all websites. Use for every live/production website deployment — always the right choice when a site needs to go live. Vercel is |
| `hunter_skill` | Automates discovery, logging, and reporting of high-intent Utah leads for Catalyst Works Consulting. Triggers on "hunter", "run hunter", "prospect Utah", "daily |
| `hyperframes` | Create video compositions, animations, title cards, overlays, captions, voiceovers, audio-reactive visuals, and scene transitions in HyperFrames HTML. Use when  |
| `hyperframes-cli` | HyperFrames CLI tool — hyperframes init, lint, preview, render, transcribe, tts, doctor, browser, info, upgrade, compositions, docs, benchmark. Use when scaffol |
| `hyperframes-registry` | Install and wire registry blocks and components into HyperFrames compositions. Use when running hyperframes add, installing a block or component, wiring an inst |
| `image-generator` | Generates 3 coordinated AI prompts for scroll-stopping video content: (1) clean product/object shot on pure white background at 16:9, (2) exploded/deconstructed |
| `inbound_lead` | Inbound lead routine for researching, drafting, logging, and notifying on new prospect opportunities. Triggers on "inbound lead", "new lead came in", "research  |
| `karpathy` | Apply the four Karpathy coding principles (from AGENT_SOP.md) as a structured audit of code that was just written, proposed, or reviewed. Use on-demand via /kar |
| `kie_media` | Generates images and videos via the Kai (kie.ai) API. Routes each request to the top-ranked model for the task (text-to-image, image-to-image, text-to-video, im |
| `library` | Index for shared internal skill library assets — lists reusable capability packs (cole-templates, agentshq-dispatch) under skills/library/. Use when looking for |
| `local_crm` | Agent-driven pipeline management for tracking Catalyst Growth Engine leads in a local PostgreSQL CRM. Triggers on "local crm", "update pipeline", "add lead to C |
| `memory` | Memory helpers and references for retrieving and preserving agent operating context. Two layers: (1) flat-file auto-memory in ~/.claude/projects/.../memory/ for |
| `mermaid_diagrammer` | Generates PNG, SVG, or PDF diagrams from Mermaid syntax using local Mermaid-CLI. Triggers on "mermaid", "generate diagram", "mermaid diagram", "draw this as a d |
| `notebooklm` | Query, manage, and automate Google NotebookLM from your AI agent. Add sources, generate slide decks with your brand colors, run research, and keep auth alive au |
| `notion_cli` | Project-specific CLI for direct interaction with Notion databases in agentsHQ. Triggers on "notion cli", "query notion", "notion database", "update notion recor |
| `notion_skill` | Notion API tool. Agent-internal only. notion_tool.query_database/search_databases/create_page/create_idea_page imported by tools.py and handlers_commands.py. DO |
| `notion_stylist` | Applies premium Catalyst Works visual styling to Notion pages and databases. Triggers on "notion stylist", "style this notion page", "notion branding", "format  |
| `nsync` | Use at the start or end of any session to verify and sync GitHub, local, and VPS to the same commit AND leave the VSCode Source Control panel empty. Triggers on |
| `opencli_skill` | \|. Triggers on "opencli", "browse linkedin", "fetch from reddit", "search hackernews", "scrape this site with cli". |
| `openspace_skill` | Autonomous performance optimization and skill repair engine for self-evolving Catalyst Works agents. Triggers on "openspace", "evolve skill", "repair skill", "o |
| `outreach` | Core outreach engine for SW + CW pipelines. Agent-internal only -- not Boubacar-invoked. sequence_engine.py runs 4/5-touch email sequences imported by morning_r |
| `rca` | Use when a production system is broken, behaving unexpectedly, or an incident needs investigation. Triggers on: gate agent failures, studio pipeline errors, SW  |
| `react-best-practices` | React and Next.js performance optimization guidelines from Vercel Engineering. This skill should be used when writing, reviewing, or refactoring React/Next.js c |
| `remoat` | Automates the connection between the Antigravity IDE and Telegram bot through the Remoat bridge. Triggers on "remoat", "antigravity bridge", "connect IDE to Tel |
| `remote-access-auditor` | >. Triggers on "remote access audit", "scan for remote tools", "security scan my PC", "check if someone is accessing my computer". |
| `roadmap` | Manage living roadmaps for multi-session projects in docs/roadmap/. Use when user says "roadmap", "roadmaps", "list roadmaps", "show me the roadmap", "what's ne |
| `sankofa` | Use when the user invokes /sankofa or asks to run the Sankofa Council on content, a decision, a deliverable, or a strategy. Five independent voices stress-test  |
| `scene-segmenter` | Breaks a script into N scene beats at 200 words/minute and emits one paired image-prompt and video-prompt per beat. Front-half of the Studio M3.5 channel cloner |
| `seo-strategy` | Unified SEO skill with two modes: Article/Page Optimization and Full Website Audit. |
| `serper_skill` | Serper-backed prospecting and search tooling for lead discovery workflows. Triggers on "serper", "search leads", "serper search", "prospect search", "find prosp |
| `signal-works-pitch-reel` | Generates a Signal Works pitch reel video from website demo screenshots. Auto-generates niche-specific copywriting, builds a HyperFrames composition, renders th |
| `skool-harvester` | Harvests Skool community lessons , text, attachments (n8n JSONs, agent template zips, PDFs), screenshots, and metadata , into workspace/skool-harvest/<community |
| `slides` | Create strategic HTML presentations with Chart.js, design tokens, responsive layouts, copywriting formulas, and contextual slide strategies. Triggers on 'slides |
| `superpowers` | Superpowers methodology and workflow skill collection used by local coding agents. |
| `tab-shutdown` | Closes a Claude Code session cleanly. Writes all discoveries, decisions, and lessons to memory and skills, updates any affected skills, writes a handoff doc to  |
| `transcribe` | Transcribes audio files, video files, folders, and YouTube URLs using the OpenAI Whisper API with optional Google Drive and NotebookLM routing. Triggers on "tra |
| `transcript-style-dna` | Reverse-engineers a voice fingerprint from N reference texts (transcripts, LinkedIn posts, website copy, About pages) and outputs a JSON style profile plus one  |
| `ui-styling` | Create beautiful, accessible user interfaces with shadcn/ui components (built on Radix UI + Tailwind), Tailwind CSS utility-first styling, and canvas-based visu |
| `ui-ux-pro-max` | "UI/UX design intelligence for web and mobile. Includes 50+ styles, 161 color palettes, 57 font pairings, 161 product types, 99 UX guidelines, and 25 chart type |
| `vercel-cli-with-tokens` | Deploy and manage projects on Vercel using token-based authentication. Use when working with Vercel CLI using access tokens rather than interactive login — e.g. |
| `vercel-launch` | Vercel preview deploy for Boubacar's apps — for mobile testing and sharing preview links with clients ONLY. NOT for production. All live/production deployments  |
| `web-design-guidelines` | Review UI code for Web Interface Guidelines compliance. Use when asked to "review my UI", "check accessibility", "audit design", "review UX", or "check my site  |
| `webapp-testing` | Toolkit for interacting with and testing local web applications using Playwright. Use when verifying frontend functionality, debugging UI behavior, capturing br |
| `website-intelligence` | Research-driven competitive intelligence engine for websites. Scrapes a client's existing site, analyzes their top 5 competitors, produces a professional compet |
| `website-teardown` | Two-mode pipeline that audits a prospect website. COLD mode = lean outbound-email teardown (Phase 0 auto-filter + 3-leak markdown + paste-ready cold email). WAR |
| `website-to-hyperframes` | Capture a website and create a HyperFrames video from it. Use when a user provides a URL and wants a video, wants a social ad or product tour from a website, or |
| `youtube-10k-lens` | Use when given a YouTube URL and you need a transcript, summary, and analysis through Boubacar's $10K/day framework. Triggers when user shares a YouTube link an |

## Orchestrator modules (103)

| File | Purpose | Public funcs | Tool classes | Tool bundles |
|---|---|---|---|---|
| `agent_config.py` | agent_config.py - DB-driven runtime configuration (local Postgres). Provides a t | ensure_table, get_config, set_config, delete_config, list_config |  |  |
| `agents.py` | agents.py — Agent Definitions ============================== All specialist agen | select_by_capability, get_llm, select_llm, build_orchestrator_agent, build_planner_agent, build_researcher_agent |  |  |
| `app.py` | app.py - FastAPI entrypoint for the agentsHQ orchestrator. Startup hooks (in ord | verify_api_key, verify_chat_token, startup_event, get_status, health, telegram_webhook |  |  |
| `approval_queue.py` | approval_queue.py -- Phase 1 autonomy layer. Every autonomous proposal flows thr | normalize_feedback_tag, enqueue, get, find_by_telegram_msg_id, find_latest_pending, list_pending |  |  |
| `async_poll.py` | async_poll.py -- Shared Kie AI async job polling utility. Replaces the flat slee | poll_until_done, submit_and_poll, high_res_params |  |  |
| `atlas_dashboard.py` | atlas_dashboard.py -- Pure data fetchers for the Atlas M8 dashboard. One functio | get_state, get_queue, get_content, get_spend, get_cost_ledger, add_cost_ledger_entry |  |  |
| `auto_publisher.py` | auto_publisher.py - Atlas M7b. Autonomous publish tick. Heartbeat callback that  | auto_publisher_tick |  |  |
| `autonomy_guard.py` | autonomy_guard.py -- Safety rails for autonomous crews. Single source of truth f | get_guard |  |  |
| `beehiiv.py` | beehiiv.py - Newsletter delivery integration. Primary path: Listmonk (self-hoste | send_via_listmonk, create_draft |  |  |
| `blotato_publisher.py` | blotato_publisher.py - Atlas M7b. Verified-against-Blotato-API publisher. Wraps  | get_publisher, list_accounts |  |  |
| `chairman_crew.py` | chairman_crew.py - M5 L5 Learning Loop. Weekly oversight crew (Monday 06:00 MT). | fetch_outcomes, analyse_patterns, propose_mutations, enqueue_proposals, apply_mutation, chairman_weekly_tick |  |  |
| `concierge_crew.py` | concierge_crew.py - M4 LLM-powered error triage. Reads /var/log/error_monitor.lo | fetch_recent_errors, group_by_signature, propose_fix, enqueue_proposals, run_concierge_sweep |  |  |
| `conftest.py` |  |  |  |  |
| `constants.py` | constants.py — System-wide configuration tokens and task classifications. |  |  |  |
| `content_board_reorder.py` | content_board_reorder.py - one-off orchestrator job ============================ | telegram, get_text, get_select, get_multi, fetch_unposted, llm_call |  |  |
| `content_connection_crew.py` | content_connection_crew.py - Atlas M9d-C: Content Connection Finder Reads last 3 | fetch_recent_content, build_connection_prompt, parse_connections, write_connections_to_notion, run |  |  |
| `content_multiplier_crew.py` |  | estimate_tokens, classify_lens, ingest_source, build_piece_plans, ctq_reject_reason, multiply_source |  |  |
| `council.py` | council.py — The Sankofa Council ================================== Named after  | should_invoke_council, load_prompt, strip_style_markers |  |  |
| `crews.py` | crews.py — Dynamic Crew Assembly ================================== Assembles th | build_website_crew, build_3d_website_crew, build_research_crew, build_consulting_crew, build_social_crew, build_content_draft_crew |  |  |
| `db.py` | db.py — Database connection utilities for agentsHQ ============================= | ensure_chat_artifacts_table, save_chat_artifact, get_chat_artifact, ensure_content_approvals_table, ensure_video_jobs_table, get_crm_connection |  |  |
| `design_context.py` | design_context.py — Design Context Loader ====================================== |  |  |  |
| `dream_handler.py` | dream_handler.py - Telegram-integrated memory consolidation (Dreams loop). Flow: | has_pending_proposal, run_dream_async, handle_dream_reply, handle_dream_callback |  |  |
| `drive_publish.py` | drive_publish.py — Publish PDFs (and other files) to Google Drive with public-li | ensure_public, publish_public_file, update_public_file, audit_email_template_pdfs, audit_studio_pipeline_videos |  |  |
| `engine.py` |  | run_orchestrator, run_team_orchestrator |  |  |
| `episodic_memory.py` | episodic_memory.py -- Phase 1 autonomy layer. Writes and reads task_outcomes: on | build_signature, start_task, complete_task, link_approval, record_approval_result, find_similar |  |  |
| `firecrawl_tools.py` | firecrawl_tools.py — Shared Firecrawl Tool Definitions ========================= |  | FirecrawlScrapeTool, FirecrawlCrawlTool, FirecrawlSearchTool |  |
| `gate_agent.py` | gate_agent.py - Echo M2.5: The Gate Sole arbiter of all writes to shared state:  | gate_tick |  |  |
| `griot.py` | griot.py - Phase 3 L0.5 autonomous content pilot. Heartbeat wake callback that r | griot_morning_tick, griot_propose_on_demand, record_content_approval |  |  |
| `griot_scheduler.py` | griot_scheduler.py - Phase 3.75: schedule approved Griot candidates. Runs on a 5 | griot_scheduler_tick |  |  |
| `griot_signal_brief.py` | griot_signal_brief.py -- LéGroit weekly theme detection + Signal Brief. Fires ev | griot_signal_brief_tick |  |  |
| `halo_tracer.py` | halo_tracer.py — CrewAI -> HALO-compatible OTel JSONL trace writer. Subscribes t | get_tracer, maybe_install_halo_tracer |  |  |
| `handlers.py` | handlers.py - Telegram update orchestrator + polling loop. Thin dispatcher. All  | process_telegram_update, telegram_polling_loop |  |  |
| `handlers_approvals.py` | handlers_approvals.py - Phase 1 approval-queue handlers for Telegram. Three publ | handle_callback_query, evict_expired_windows, handle_pending_feedback_tag, handle_approval_reply, handle_naked_approval, handle_publish_reply |  |  |
| `handlers_chat.py` | handlers_chat.py - Rich chat + praise/critique helpers. Owns: - run_chat(message | handle_feedback, run_chat, run_chat_with_buttons, run_atlas_chat |  | _TOOLS |
| `handlers_commands.py` | handlers_commands.py - Slash command dispatch for Telegram. One function per com | parse_task_add, handle_task_add, dispatch_command |  |  |
| `handlers_doc.py` | handlers_doc.py - Telegram emoji command handlers for doc routing. ============= | handle_doc_emoji |  |  |
| `harvest_reviewer.py` | harvest_reviewer.py - Two-agent (Mapper + Decision) reviewer for harvested Skool | review_lesson, run_council_on_batch, review_batch, main |  |  |
| `harvest_triage.py` | harvest_triage.py - Pure-heuristic filter over a community's harvested lessons.  | triage_lesson, build_review_plan, main |  |  |
| `health.py` |  |  |  |  |
| `health_sweep.py` | health_sweep.py - Daily automated API health sweep. Probes every public-facing e | run_health_sweep, read_sweep_state, health_sweep_tick |  |  |
| `heartbeat.py` | heartbeat.py -- Phase 2 autonomy layer. Time-based wake-on-schedule runner with  | register_wake, unregister_wake, list_wakes, dry_run_next, start |  |  |
| `hermes_worker.py` | hermes_worker.py - M24: Autonomous self-healing execution. Triggered when a conc | is_path_safe, checkout_sandbox_branch, commit_and_push_fix, hermes_fix_handler |  |  |
| `hyperframe_boost_agent.py` |  | send_message |  |  |
| `hyperframe_boost_cron.py` |  |  |  |  |
| `hyperframe_brief_generator.py` |  |  |  |  |
| `kie_media.py` | kie_media.py — Kai (kie.ai) Media Generation Core ============================== | generate_image, generate_video, generate_promo_video, list_models, check_credits, sora_watermark_remover |  |  |
| `llm_helpers.py` | llm_helpers.py - Shared LLM client factory and completion helper. All OpenRouter | get_openrouter_client, call_llm |  |  |
| `logger.py` | logger.py — Immutable out-of-band audit trail ================================== | audit, audit_spawn, audit_self_heal, audit_gate, audit_file_edit, audit_task |  |  |
| `memory.py` | memory.py — Agent Memory Interface ===================================== All mem | get_qdrant_client, get_embedding, save_to_memory, query_memory, get_conversation_history, save_conversation_turn |  |  |
| `memory_distillation_crew.py` | memory_distillation_crew.py - Atlas M9d-B: Memory Distillation Engine Reads all  | read_memory_from_db, read_all_memory_files, build_distillation_prompt, save_to_postgres, run |  |  |
| `memory_models.py` | memory_models.py - Write contract for the agentsHQ memory table. Every write pat |  |  |  |
| `memory_qmd.py` | memory_qmd.py -- Local semantic search via QMD (github.com/tobi/qmd). Additive t | qmd_available, qmd_search, index_document, qmd_search_with_fallback |  |  |
| `memory_store.py` | memory_store.py - Read/write interface for the agentsHQ memory table. All write  | write, query_text, query_filter, load_hard_rules |  |  |
| `model_review_agent.py` | model_review_agent.py -- Weekly leGriot model quality review. Fires every Sunday | model_review_tick |  |  |
| `newsletter_anchor_tick.py` | Monday 12:00 MT newsletter drafting tick. | send_message, send_message_with_buttons, build_newsletter_crew, start_task, complete_task, newsletter_anchor_tick |  |  |
| `newsletter_editorial_input.py` | newsletter_editorial_input.py - Postgres CRUD for the weekly editorial reply. Th | upsert_reply, get_reply_for_week |  |  |
| `newsletter_editorial_prompt.py` | newsletter_editorial_prompt.py - Sunday 18:00 MT heartbeat callback. Sends one T | send_message, newsletter_editorial_prompt_tick |  |  |
| `niche_research.py` | niche_research.py - Niche signal scraping via Apify, persisted to Supabase. Scra | ensure_table, write_signals, scrape_reddit, get_tools |  |  |
| `notifier.py` | notifier.py — All Telegram Bot API calls for agentsHQ. No other file sends Teleg | send_message, log_for_remoat, push_commentary, send_briefing, send_progress_ping, send_result |  |  |
| `notion_state_poller.py` | Notion State Poller. Heartbeat-driven 5-minute tick. Queries Notion Tasks DB for | load_cache, save_cache, extract_tracked_props, diff_row, format_changelog_line, append_changelog |  |  |
| `notion_sync_crew.py` | notion_sync_crew.py - Atlas M9d Step 3: Nightly Notion sync Pulls modified pages | sync_ideas, sync_tasks, run |  |  |
| `prompt_loader.py` | prompt_loader.py - Load agent system prompts from disk at runtime. Lookup order  | get_system_md_path, load_system_prompt, reload_prompt |  |  |
| `provider_health.py` | provider_health.py - Circuit breaker state for LLM providers. One row per provid | ensure_table, get_status, record_failure, record_recovery |  |  |
| `provider_probe.py` | provider_probe.py - 5-minute health probe for the active LLM provider. Registere | run_probe |  |  |
| `publish_brief.py` | publish_brief.py - Phase 3.75+: daily morning publish brief. Every weekday at 07 | publish_brief_tick |  |  |
| `research_engine.py` | research_engine.py: CrewAI bypass for research-type prompts. =================== | run_research |  |  |
| `router.py` | router.py — Task Classification Engine ======================================= M | classify_task, get_crew_type, extract_metadata, get_crew_for_task, describe_task, build_task_type_help |  |  |
| `saver.py` | saver.py — Save agent output to GitHub and Google Drive. Env vars required: GITH | get_drive_subfolder, save_to_github, save_to_drive, save_to_notion_content_board |  |  |
| `scheduler.py` | scheduler.py — Catalyst Daily Ignition ====================================== Th | start_scheduler |  |  |
| `schemas.py` |  |  |  |  |
| `scrub_titles.py` | Strip ' -- LinkedIn' / ' -- X' / em dashes from Content Board titles. |  |  |  |
| `session_compressor.py` | session_compressor.py - Cross-session memory compressor (Atlas M9c). Fires every | find_sessions_to_compress, compress_session, compressor_tick |  |  |
| `session_store.py` | session_store.py - Agent session persistence (local Postgres). Provides upsert/t | ensure_table, upsert_session, touch_session, get_session, list_active_sessions |  |  |
| `social_analytics.py` | social_analytics.py — Social Media Engagement Analytics Tracking Pipeline ====== | load_env, ensure_db_schema, send_telegram_summary, parse_count_from_label, scrape_x_metrics, scrape_linkedin_metrics |  |  |
| `spend_snapshot.py` | spend_snapshot.py - Daily provider spend snapshot. Fires once per day at 23:55 M | take_snapshot, get_historical, take_kie_snapshot, get_kie_historical, spend_snapshot_tick |  |  |
| `startup_check.py` | startup_check.py - Hard-fail guard for required env vars. Called once at server  | assert_required_env_vars |  |  |
| `state.py` | state.py - In-memory system state trackers. Shared dicts and locks that span han |  |  |  |
| `story_prompt_tick.py` | story_prompt_tick.py -- LéGroit storytelling prompt engine. Fires on two trigger | story_prompt_scheduled_tick, story_prompt_sparse_tick |  |  |
| `studio_analytics_scraper.py` | studio_analytics_scraper.py - Studio M5-lite. Scrape public view counts from pos | studio_analytics_tick |  |  |
| `studio_blotato_publisher.py` | studio_blotato_publisher.py - Studio M4. Heartbeat tick that publishes Studio Pi | studio_blotato_publisher_tick |  |  |
| `studio_brand_config.py` | studio_brand_config.py — Dynamic brand config loader for Studio M3. Resolution o | load_brand_config, is_brand_ready |  |  |
| `studio_composer.py` | studio_composer.py - Studio M3: Compose video from scenes + audio using ffmpeg.  | compose |  |  |
| `studio_production_crew.py` | studio_production_crew.py — Studio M3: End-to-end production orchestrator. Entry | run_production, studio_production_tick |  |  |
| `studio_qa_crew.py` | studio_qa_crew.py - Studio M1 Engine. Quality Review Crew. 8 checks that run on  | check_spellcheck_grammar, check_banned_phrases, check_length_target, check_hook_present, check_source_citation, check_cta_present |  |  |
| `studio_render_publisher.py` | studio_render_publisher.py - Studio M3: Render + Drive upload + Notion update. R | render_and_publish |  |  |
| `studio_scene_builder.py` | studio_scene_builder.py — Studio M3: Break script into timed scenes. Takes scrip | build_scenes |  |  |
| `studio_script_generator.py` | studio_script_generator.py — Studio M3: Script generation from Pipeline DB candi | generate_script |  |  |
| `studio_story_bridge.py` | studio_story_bridge.py -- Bridge between Content Board Story entries and Studio  | studio_story_bridge_tick |  |  |
| `studio_trend_scout.py` | studio_trend_scout.py - Content Intelligence Scout (Phase 1). Daily heartbeat (M | scout_niche, get_reply_for_week, studio_trend_scout_tick |  |  |
| `studio_visual_generator.py` | studio_visual_generator.py — Studio M3: Visual asset generation per scene. M3.4  | generate_visuals |  |  |
| `studio_voice_generator.py` | studio_voice_generator.py — Studio M3: TTS voice generation. Primary: ElevenLabs | generate_voice |  |  |
| `test_content_connection.py` | Tests for content_connection_crew.py — Atlas M9d-C | test_fetch_recent_content_returns_list, test_fetch_filters_non_published, test_build_connection_prompt_requires_non_obvious, test_parse_connections_returns_list, test_write_connections_to_notion_creates_records |  |  |
| `tools.py` | tools.py — Tool Registry ========================= All tools available to agents | get_mcp_tools | LaunchVercelAppTool, SetNotionStyleTool, AddNotionNavTool, ArchitectNotionPageTool | NOTION_STYLING_TOOLS, FORGE_TOOLS, INBOUND_TOOLS, GWS_TOOLS |
| `unified_queue.py` | unified_queue.py -- Echo M3: single display + routing layer for all pending appr | list_all_pending, list_all_recent, approve_any, reject_any |  |  |
| `upscale.py` | fal.ai video upscale submission helpers. | submit_upscale_job |  |  |
| `usage_logger.py` | usage_logger.py — Per-call LLM ledger ====================================== Log | log_call, log_anthropic_call, merge_context, install_litellm_callback |  |  |
| `utils.py` | utils.py - Small helpers shared across modules. Owns: - sanitize_text: redact se | sanitize_text |  |  |
| `video_analyze.py` | video_analyze.py - Reference video analysis via Gemini Files API. Uploads a loca | analyze, analyze_many, get_tools |  |  |
| `video_crew.py` | Unified video generation dispatcher, all job types: batch, ugc, cameo, narrative | enqueue_video_job, run_video_tick |  |  |
| `video_crew_agents.py` | Dedicated agents for the Unified Video Crew. | build_video_director_agent |  |  |
| `webhooks.py` | Webhook endpoints for asynchronous media callbacks. | fal_upscale_webhook |  |  |
| `weekly_synthesis_crew.py` | weekly_synthesis_crew.py - Atlas M9d-A: Weekly Synthesis Reads last N memory fil | read_memory_from_db, read_memory_files, read_roadmap_logs, build_synthesis_prompt, save_to_postgres, run |  |  |
| `worker.py` | worker.py - Background job execution. _run_background_job is called out-of-band  |  |  |  |

## Environment keys (129)

Names only; values live in `.env`.

```
ALLOWED_USER_IDS
ANTHROPIC_API_KEY
ANTHROPIC_THEPOPEBOT_API_KEY
APIFY_API_TOKEN
APOLLO_API_KEY
BEEHIIV_API_KEY
BEEHIIV_PUBLICATION_ID
BING_SEARCH_API_KEY
BLOTATO_1STGEN_INSTAGRAM_ACCOUNT_ID
BLOTATO_1STGEN_TIKTOK_ACCOUNT_ID
BLOTATO_1STGEN_X_ACCOUNT_ID
BLOTATO_API_KEY
BLOTATO_BAOBAB_INSTAGRAM_ACCOUNT_ID
BLOTATO_BAOBAB_TIKTOK_ACCOUNT_ID
BLOTATO_BAOBAB_X_ACCOUNT_ID
BLOTATO_CATALYST_INSTAGRAM_ACCOUNT_ID
BLOTATO_CATALYST_TIKTOK_ACCOUNT_ID
BLOTATO_LINKEDIN_ACCOUNT_ID
BLOTATO_LINKEDIN_PAGE_ID
BLOTATO_X_ACCOUNT_ID
BLOTATO_YT_BAOBAB_ACCOUNT_ID
BLOTATO_YT_CATALYST_ACCOUNT_ID
CALENDLY_CLIENT_ID
CALENDLY_CLIENT_SECRET
CALENDLY_PERSONAL_ACCESS_TOKEN
CALENDLY_WEBHOOK_SIGNING_KEY
CC_TELEGRAM_BOT_TOKEN
CC_TELEGRAM_CHAT_ID
CHAT_UI_PIN
CONSOLE_VERBOSE
ELEVENLABS_API_KEY
FIRECRAWL_API_KEY
FORGE_CONTENT_DB
FORGE_KPI_BLOCK_IDS
FORGE_PAGE_ID
FORGE_PIPELINE_DB
FORGE_REVENUE_DB
FORGE_TASKS_DB
GENERIC_TIMEZONE
GITHUB_PAT_TOKEN
GITHUB_REPO
GITHUB_TOKEN
GITHUB_USERNAME
GOOGLE_API_KEY
GOOGLE_DRIVE_FOLDER_ID
GOOGLE_OAUTH_CREDENTIALS_JSON
GOOGLE_OAUTH_CREDENTIALS_JSON_CW
GUMROAD_DEFAULT_PRODUCT_LINK
HCK_SUPABASE_ANON
HCK_SUPABASE_DB
HCK_SUPABASE_DIRECT_CONNECTION_STRING
HCK_SUPABASE_HOST
HCK_SUPABASE_PASSWORD_B64
HCK_SUPABASE_PORT
HCK_SUPABASE_PROJECT_ID
HCK_SUPABASE_SERVICE_KEY
HCK_SUPABASE_USER
HEALTH_REPORT_TOKEN
HELLOSIGN_API_KEY
HOTELCLUBDEKIPE_PROJECT_URL
HUNTER_API_KEY
IDEAS_DB_ID
KIE_AI_API_KEY
LISTMONK_PW
LISTMONK_USERNAME
N8N_ENCRYPTION_KEY
NEXT_PUBLIC_ADSENSE_PUBLISHER_ID
NOTION_CRM_LEADS_DB_ID
NOTION_DATABASE_ID
NOTION_FORGE_PIPELINE_DB_ID
NOTION_HARVESTED_RECS_DATA_SOURCE_ID
NOTION_HARVESTED_RECS_DB_ID
NOTION_MEDIA_INDEX_DB_ID
NOTION_OUTPUTS_DB_ID
NOTION_SECRET
NOTION_STUDIO_BRAND_CONFIG_DB_ID
NOTION_STUDIO_PIPELINE_DB_ID
OPENAI_API_KEY
OPENROUTER_API_KEY
ORCHESTRATOR_API_KEY
ORCHESTRATOR_TELEGRAM_BOT_TOKEN
PERPLEXITY_API_KEY
PERSONAL_WHATSAPP
POSTGRES_PASSWORD
PRACTICE_SESSIONS_DB_ID
PROSPEO_KEY
REMOAT_ALLOWED_USER_IDS
REMOAT_TELEGRAM_BOT_TOKEN
REMOAT_TELEGRAM_CHAT_ID
REPORT_EMAIL
SERPAPI_KEY
SERPER_API_KEY
SIGNAL_WORKS_CALENDLY
SIGNAL_WORKS_CALENDLY_AUDIT
SIGNAL_WORKS_DEMO_DENTAL
SIGNAL_WORKS_DEMO_ROOFING
SIGNAL_WORKS_LOOM_DENTAL
SIGNAL_WORKS_LOOM_ROOFING
SIGNAL_WORKS_SENDER
SKRAPP_API_KEY
SMTP_PASS
SMTP_USER
STRIPE_LINK_MONTHLY_497
STRIPE_LINK_MONTHLY_797
STRIPE_LINK_MONTHLY_997
STRIPE_PUBLISHABLE_KEY
STRIPE_SECRET_KEY
STRIPE_SETUP_1000
STRIPE_SETUP_2500
STRIPE_SETUP_500
STRIPE_WEBHOOK_SECRET
SUPABASE_DB
SUPABASE_HOST
SUPABASE_KEY
SUPABASE_KEY_SECRET
SUPABASE_PASSWORD_B64
SUPABASE_PORT
SUPABASE_SERVICE_KEY
SUPABASE_URL
SUPABASE_USER
TELEGRAM_CHAT_ID
USE_METACLAW
VERCEL_TOKEN
VIDEO_CREW_ENABLED
VPS_IP
WAVESPEED_API_KEY
WORKSPACE_BASE_DIR
YOUTUBE_API_KEY
YOUTUBE_API_KEY_2
```

## Python requirements (29)

```
crewai[tools]==1.14.4
crewai-tools==1.14.4
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
httpx>=0.27.0
pydantic[email]>=2.8.0
openai==2.34.0
litellm==1.83.0
anthropic==0.98.1
notion-client>=2.2.1
qdrant-client==1.17.1
psycopg2-binary>=2.9.9
mcp>=1.0.0
firecrawl-py>=4.21.0
curl_cffi>=0.7.0
playwright>=1.49.0
patchright>=1.49.0
beautifulsoup4>=4.12.0
youtube-transcript-api>=0.6.2
python-dotenv>=1.0.1
tenacity>=8.3.0
pytz>=2024.1
requests>=2.31.0
PyGithub>=2.3.0
google-api-python-client>=2.130.0
google-auth>=2.29.0
pypdf>=4.0.0
notebooklm-mcp-cli>=0.5.0
pytest>=8.0.0
```
