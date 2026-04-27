"""One-shot script to write pending Harvested Recs rows to Notion."""
import os, requests
from dotenv import load_dotenv
load_dotenv("D:/Ai_Sandbox/agentsHQ/.env")

TOKEN = os.environ["NOTION_SECRET"]
HRECS_DB = os.environ["NOTION_HARVESTED_RECS_DB_ID"]
IDEAS_DB = os.environ["IDEAS_DB_ID"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
TOOLS_VALID = {"n8n","apify","blotato","kie","airtable","google_sheets","modal","gemini","notion","supabase","firecrawl","crewai","antigravity","claude_code"}

ROWS = [
    {"title":"R45 | Auto Music Creator with Suno v5","lesson_id":"969784c667a04ffaa270c514e02ceb65","batch":"2026-04-26T23-26-56Z","verdict":"Take with translation","status":"Approved","lift":16.0,"target":"skills/suno-music-creator/ + orchestrator/music_creator_crew.py","reasoning":"Automated music ideation to final Suno v5 track. n8n template downloaded. Splittable: concept-agent + suno-skill + assembly-crew. Feeds faceless channel content pipeline.","council_notes":"No Council run yet. Run Council before building.","fit":"enhances kie_media + new skill (skills/suno-music-creator/)","fit_detail":"kie_media has suno-api stub. R45 adds full ideation->generation->assembly pipeline on top. New crew orchestrates kie_media suno calls with batch scheduling and Content Board upload.","tools":["n8n","kie"],"source_url":"https://www.skool.com/robonuggets/classroom/e3a5624c?md=969784c667a04ffaa270c514e02ceb65"},
    {"title":"R44 - The AI Influencer Toolkit","lesson_id":"002c0a0ad8d5463fb1900f33458a264e","batch":"2026-04-26T23-26-56Z","verdict":"Take with translation","status":"Approved","lift":8.5,"target":"skills/ai-influencer/ + orchestrator/influencer_crew.py","reasoning":"End-to-end faceless influencer: character design -> content calendar -> video gen. n8n template 18K chars downloaded. Core use case for faceless channels.","council_notes":"No Council run. Check character consistency approach vs existing kie_media routing before build.","fit":"new standalone crew (orchestrator/influencer_crew.py)","fit_detail":"Nothing in agentsHQ covers consistent character persona management for faceless channels. New crew: character-profile + content-calendar + video-gen agents via kie_media. Sits alongside studio roadmap.","tools":["n8n","kie","gemini"],"source_url":"https://www.skool.com/robonuggets/classroom/35e6fa9d?md=002c0a0ad8d5463fb1900f33458a264e"},
    {"title":"R43 - Sora2 on Autopilot","lesson_id":"aba5dfdcc2e249048ac0f2525dab8330","batch":"2026-04-26T23-26-56Z","verdict":"Take with translation","status":"Approved","lift":8.5,"target":"skills/kie_media/ (extend with Sora2) + n8n workflow (keep)","reasoning":"Batch video generation for faceless content. Two ZIPs downloaded: image-to-video + text-to-video templates. Extends kie_media with Sora2 alongside Kling.","council_notes":"No Council run. Verify Sora2 API access via OpenRouter/kie before build.","fit":"enhances skills/kie_media/SKILL.md","fit_detail":"kie_media already routes image/video gen. R43 adds Sora2 as new model option in the router + batch scheduling via n8n. Surgical: extend MODEL_REGISTRY with Sora2 slug.","tools":["n8n","kie"],"source_url":"https://www.skool.com/robonuggets/classroom/e7cff690?md=aba5dfdcc2e249048ac0f2525dab8330"},
    {"title":"n48 - Claude + GPT-Image-2","lesson_id":"14301f0faebd4295af5ffc70cb9f44dd","batch":"2026-04-26T23-28-48Z","verdict":"Take with translation","status":"Approved","lift":4.5,"target":"skills/gpt-image-composer/ + extend skills/kie_media/","reasoning":"Brand context -> GPT-Image-2 API -> branded asset. Council anchor pick. 8.8MB resources ZIP downloaded. 4.5h skill build.","council_notes":"Council anchor pick for n45-n49 batch. Promote immediately. Extend kie_media router with GPT-Image-2 branded-asset route.","fit":"enhances skills/kie_media/ + new skill (skills/gpt-image-composer/)","fit_detail":"kie_media routes to nano-banana-pro and Kling. n48 adds GPT-Image-2 as branded-asset-specific route when brand context is provided. Extends the router, not replaces it.","tools":["gemini","claude_code"],"source_url":"https://www.skool.com/robonuggets/classroom/64ef71ee?md=14301f0faebd4295af5ffc70cb9f44dd"},
    {"title":"n49 - Claude HTML Slides","lesson_id":"1925ea6c9f6c4dc29bf1668cc4cafd49","batch":"2026-04-26T23-28-48Z","verdict":"Reference only","status":"Deferred","lift":6.0,"target":"skills/slides/ (component templates only, on request)","reasoning":"Master Slides component library useful but routing through IDE is architectural regression. Council: port templates to slides skill only if explicitly requested.","council_notes":"Council downgrade to Reference only. Component templates salvageable into slides skill on demand.","fit":"enhances skills/slides/ (partial, on demand only)","fit_detail":"slides skill already generates HTML presentations. n49 component library can be imported as templates manually. Not a crew build.","tools":["claude_code"],"source_url":"https://www.skool.com/robonuggets/classroom/827a3bd5?md=1925ea6c9f6c4dc29bf1668cc4cafd49"},
    {"title":"n47 - Claude + Awesome Designs MD","lesson_id":"d93926d6cf3b4818a54b5a95e52e95f1","batch":"2026-04-26T23-28-48Z","verdict":"Reference only","status":"Deferred","lift":3.5,"target":"none","reasoning":"Awesome Designs MD is proprietary, undocumented, no public API. Cannot translate.","council_notes":"Confirmed Reference only. Proprietary closed framework blocks translation.","fit":"not applicable","fit_detail":"No translation path. Awesome Designs MD has no public spec. Monitor for open-source equivalent.","tools":["claude_code"],"source_url":"https://www.skool.com/robonuggets/classroom/c2f95fca?md=d93926d6cf3b4818a54b5a95e52e95f1"},
    {"title":"n46 - Claude + Seedance 2.0","lesson_id":"c8982134d8894aeca6b526e35434ac4d","batch":"2026-04-26T23-28-48Z","verdict":"Reference only","status":"Deferred","lift":0.5,"target":"none","reasoning":"Seedance 2.0 already covered by kie_media multi-model video routing. No new system taught.","council_notes":"Confirmed Reference only. kie_media covers this.","fit":"not applicable -- already covered by skills/kie_media/","fit_detail":"kie_media routes to multiple video models. Seedance 2.0 adds no new workflow or pattern.","tools":["claude_code"],"source_url":"https://www.skool.com/robonuggets/classroom/4bbb08b0?md=c8982134d8894aeca6b526e35434ac4d"},
    {"title":"n45 - Claude + NotebookLM = 24/7 Research Team","lesson_id":"ef846599e2a34f6394fd493cf4f7e2a7","batch":"2026-04-26T23-28-48Z","verdict":"Skip","status":"Rejected","lift":0.0,"target":"none","reasoning":"Council reversed to Skip. Building on scraped Google UI = scheduled breakage. Firecrawl + LLM summarization already achieves the research outcome.","council_notes":"Council: Skip. NotebookLM UI scraping is fragile. research_engine.py + Firecrawl already covers autonomous document research.","fit":"not applicable -- outcome covered by orchestrator/research_engine.py","fit_detail":"research_engine.py with Firecrawl provides autonomous document research. NotebookLM adds no capability that justifies UI-scraping brittleness.","tools":["claude_code"],"source_url":"https://www.skool.com/robonuggets/classroom/0d3c944a?md=ef846599e2a34f6394fd493cf4f7e2a7"},
]

def make_props(row):
    tools = [t for t in row.get("tools", []) if t in TOOLS_VALID]
    return {
        "Title": {"title": [{"text": {"content": row["title"]}}]},
        "Lesson ID": {"rich_text": [{"text": {"content": row["lesson_id"]}}]},
        "Community": {"select": {"name": "robonuggets"}},
        "Verdict": {"select": {"name": row["verdict"]}},
        "Target Path": {"rich_text": [{"text": {"content": row["target"]}}]},
        "Lift Hours": {"number": row["lift"]},
        "Reasoning": {"rich_text": [{"text": {"content": row["reasoning"]}}]},
        "Council Notes": {"rich_text": [{"text": {"content": row["council_notes"]}}]},
        "Status": {"select": {"name": row["status"]}},
        "Source URL": {"url": row["source_url"]},
        "Batch": {"rich_text": [{"text": {"content": row["batch"]}}]},
        "Tools Mentioned": {"multi_select": [{"name": t} for t in tools]},
        "agentsHQ Fit": {"rich_text": [{"text": {"content": row.get("fit", "")}}]},
        "agentsHQ Fit Detail": {"rich_text": [{"text": {"content": row.get("fit_detail", "")}}]},
    }

print("Writing rows to Harvested Recs...")
for row in ROWS:
    r = requests.post("https://api.notion.com/v1/pages", headers=HEADERS,
        json={"parent": {"database_id": HRECS_DB}, "properties": make_props(row)})
    print(f"  {row['title'][:45]:45} -> {r.status_code}")

print("\nWriting n48 to Ideas DB...")
r2 = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json={
    "parent": {"database_id": IDEAS_DB},
    "properties": {
        "Name": {"title": [{"text": {"content": "n48: GPT-Image-2 Branded Asset Composer"}}]},
        "Status": {"select": {"name": "Queued"}},
        "Effort": {"select": {"name": "Low"}},
        "Impact": {"select": {"name": "High"}},
        "Category": {"select": {"name": "Agent"}},
        "Content": {"rich_text": [{"text": {"content": "Source: n48 RoboNuggets bonus. Council anchor pick. Build skills/gpt-image-composer/ + extend kie_media router with GPT-Image-2 branded-asset route. 4.5h. Resources at workspace/skool-harvest/robonuggets/14301f0faebd4295af5ffc70cb9f44dd/downloads/"}}]},
    }
})
print(f"  Ideas DB n48 -> {r2.status_code} | {r2.json().get('id', '')[:36]}")
