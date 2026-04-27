"""Write R40-R36 batch + stray n-series batch to Notion, add R39 to Ideas DB."""
import json, os, requests
from pathlib import Path
from dotenv import load_dotenv
load_dotenv("D:/Ai_Sandbox/agentsHQ/.env")

TOKEN = os.environ["NOTION_SECRET"]
HRECS_DB = os.environ["NOTION_HARVESTED_RECS_DB_ID"]
IDEAS_DB = os.environ["IDEAS_DB_ID"]
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
TOOLS_V = {"n8n","apify","blotato","kie","airtable","google_sheets","modal","gemini","notion","supabase","firecrawl","crewai","antigravity","claude_code"}
REVIEWS_DIR = Path("workspace/skool-harvest/robonuggets/_reviews")

R40_OVERRIDES = {
    "9e1cfe601a5c45338199675bca42dba5": {"verdict":"Skip","status":"Rejected","council":"Council: reverse to Skip. Frontend demo, not infrastructure. Already covered by kie_media + R57 Blotato workflow.","fit":"not applicable -- frontend demo","fit_detail":"Ad creation UI demo. Infrastructure already exists in kie_media + R57 Blotato marketing agent."},
    "b5046034f3c346f3bf2bcb098d5f2e39": {"council":"Council: conditional. Pause pending Veo3 API validation spike (access + price 10-job async batch + validate 240s polling without memory leak).","fit":"enhances skills/kie_media/ -- logo animation route","fit_detail":"LogoRobo adds logo animation via Veo3. Extends kie_media routing. Pause until Veo3 API access confirmed."},
    "007a01434fa44829b5df102c1a8ac4e6": {"council":"Council: conditional. Pause pending Veo3 API validation spike. UGC advert factory is genuinely valuable but Veo3 dependency must be validated first.","fit":"new standalone crew (orchestrator/ugc_adverts_crew.py)","fit_detail":"Automated UGC video generation at scale. New crew wraps kie_media + Veo3. Real faceless channel value. Wait for Veo3 validation."},
    "f3dcf731391d47d6bb2c2cc1b77811e7": {"council":"Council anchor for R40-R36 batch. Take now. Batched cost-routed image gen is a composable primitive the entire media stack benefits from.","fit":"new skill (skills/split-ad-system/) + extends kie_media routing","fit_detail":"Batch-splits a single ad concept into N cost-optimized image variants in parallel. Composable primitive: other crews call this skill. Extends kie_media with batch routing logic."},
    "b5f9938bd9d44c3d8c87d92183b8ab97": {"council":"Take with translation. Character-consistent storymaking. Merge character-consistency constraints into R51 SEALCaM scope.","fit":"enhances orchestrator/sealcam_crew.py (R51 scope)","fit_detail":"Hyperconsistent character generation. Folds into R51 SEALCaM translation: adds character-consistency layer to scene analysis + variant generation pipeline."},
}

N_FIT = {
    "n13": ("enhances skills/kie_media/ + leGriot crew", "Video quality enhancement pipeline. Extends kie_media with upscaling route. leGriot calls this before publishing to Content Board."),
    "n7":  ("enhances skills/kie_media/ -- Seedance 1.0 cost-optimization route", "Seedance 1.0 is 25x cheaper than Veo3. Adds cost-optimized video route to kie_media MODEL_REGISTRY."),
    "n6":  ("enhances skills/kie_media/ -- Veo3 high-quality route", "Veo3 in n8n. Extends kie_media with Veo3 as premium video route alongside Kling."),
    "n4":  ("enhances orchestrator/griot.py + niche_research.py", "IG automation: source -> curate -> schedule. Extends Griot content sourcing with Instagram-specific scheduling logic."),
    "n3":  ("enhances Griot + kie_media via new skill doc", "TTS + subtitle generation. New skill wraps Fish Audio TTS + auto-subtitle burn. Griot calls this before video posting."),
    "n0":  ("not applicable -- credentials reference", "Pure reference documentation. Skip."),
}

def make_props(v, ov, batch):
    d = v.get("decision", {})
    verdict = ov.get("verdict", d.get("verdict", "Reference only"))
    status = ov.get("status", "Approved" if "Take" in verdict else "Rejected" if verdict == "Skip" else "Deferred")
    tools = [t for t in v.get("mapper", {}).get("tools_used_by_lesson", []) if t in TOOLS_V]
    fit_from_d = d.get("agentshq_fit", "")
    fit_d_from_d = d.get("agentshq_fit_detail", "")
    return {
        "Title": {"title": [{"text": {"content": v["title"][:100].encode("ascii", "replace").decode("ascii")}}]},
        "Lesson ID": {"rich_text": [{"text": {"content": v["lesson_id"]}}]},
        "Community": {"select": {"name": "robonuggets"}},
        "Verdict": {"select": {"name": verdict}},
        "Target Path": {"rich_text": [{"text": {"content": d.get("target_path", "none")[:200]}}]},
        "Lift Hours": {"number": d.get("lift_hours", 0)},
        "Reasoning": {"rich_text": [{"text": {"content": d.get("reasoning", "")[:1500]}}]},
        "Council Notes": {"rich_text": [{"text": {"content": ov.get("council", "")[:1500]}}]},
        "Status": {"select": {"name": status}},
        "Source URL": {"url": v.get("lesson_url", "https://www.skool.com")},
        "Batch": {"rich_text": [{"text": {"content": batch}}]},
        "Tools Mentioned": {"multi_select": [{"name": t} for t in tools[:10]]},
        "agentsHQ Fit": {"rich_text": [{"text": {"content": ov.get("fit", fit_from_d)[:500]}}]},
        "agentsHQ Fit Detail": {"rich_text": [{"text": {"content": ov.get("fit_detail", fit_d_from_d)[:1000]}}]},
    }

# R40-R36
B1 = "2026-04-27T00-42-48Z"
data1 = json.load(open(f"{REVIEWS_DIR}/{B1}.json", encoding="utf-8"))
print("R40-R36:")
for v in data1["verdicts"]:
    ov = R40_OVERRIDES.get(v["lesson_id"], {})
    r = requests.post("https://api.notion.com/v1/pages", headers=HEADERS,
        json={"parent": {"database_id": HRECS_DB}, "properties": make_props(v, ov, B1)})
    verdict = ov.get("verdict", v.get("decision", {}).get("verdict", "?"))
    print(f"  {v['title'].encode('ascii','replace').decode('ascii')[:36]:36} | {verdict[:18]:18} -> {r.status_code}")

# Stray n-series
B2 = "2026-04-27T00-38-50Z"
data2 = json.load(open(f"{REVIEWS_DIR}/{B2}.json", encoding="utf-8"))
print("n-series stray:")
for v in data2["verdicts"]:
    if not v.get("decision", {}).get("verdict"):
        continue
    title_key = v["title"][:3]
    fit, fit_d = N_FIT.get(title_key, ("", ""))
    ov = {"fit": fit, "fit_detail": fit_d}
    r = requests.post("https://api.notion.com/v1/pages", headers=HEADERS,
        json={"parent": {"database_id": HRECS_DB}, "properties": make_props(v, ov, B2)})
    verdict = v.get("decision", {}).get("verdict", "?")
    print(f"  {v['title'].encode('ascii','replace').decode('ascii')[:36]:36} | {verdict[:18]:18} -> {r.status_code}")

# R39 to Ideas DB
r2 = requests.post("https://api.notion.com/v1/pages", headers=HEADERS, json={
    "parent": {"database_id": IDEAS_DB},
    "properties": {
        "Name": {"title": [{"text": {"content": "R39: Split Ad System -- Batched Cost-Routed Image Gen"}}]},
        "Status": {"select": {"name": "Queued"}},
        "Effort": {"select": {"name": "Low"}},
        "Impact": {"select": {"name": "High"}},
        "Category": {"select": {"name": "Agent"}},
        "Content": {"rich_text": [{"text": {"content": "Source: R39 RoboNuggets. Council anchor (R40-R36 batch). Composable primitive: batch-splits ad concept into N cost-optimized image variants in parallel. Extends kie_media with batch routing. Other crews call this skill. 6.5h. n8n JSON at workspace/skool-harvest/robonuggets/f3dcf731391d47d6bb2c2cc1b77811e7/downloads/"}}]},
    }
})
print(f"Ideas DB R39 -> {r2.status_code} | {r2.json().get('id','')[:36]}")
