# BUILD TODAY — agentsHQ True Agent Orchestrator
# ============================================================
# What you're building:
# One WhatsApp message → 5 autonomous agents plan, research,
# write, build, and QA a complete website → delivered to you.
# That is a TRUE agent. Not a chatbot. Not automation.
# ============================================================

---

## STATUS CHECKPOINT — What's Already Done

✅ SSH access from PowerShell (key-based, no password)
✅ agentsHQ folder structure created at ~/agentsHQ/
✅ .env uploaded and verified at ~/agentsHQ/.env
✅ Docker running: Traefik + n8n (both healthy)
✅ n8n accessible at https://n8n.srv1040886.hstgr.cloud (2FA protected)
✅ Serper API key in .env
✅ OpenRouter API key in .env
✅ GitHub repo created (agentHQ)

---

## LOCAL FOLDER STRUCTURE (D:\Ai_Sandbox\agentsHQ)

```
agentsHQ/
├── BUILD-TODAY.md               ← this file
├── agent-brain/
│   ├── Dockerfile
│   ├── orchestrator.py
│   └── requirements.txt
├── infrasctructure/
│   ├── .env                     ← source of truth for secrets
│   ├── docker-compose.yml       ← renamed from docker-compose-v3.yml
│   └── env-template-FINAL.txt
├── n8n-workflows/
│   ├── workflow-SUB-always-save.json   ← Phase 5 only
│   └── workflow-whatsapp-v6.json       ← main workflow
└── server-setup/
    ├── harden-vps.sh
    └── setup-database.sql
```

## TARGET VPS STRUCTURE (~/agentsHQ on root@72.60.209.109)

```
~/agentsHQ/
├── .env                         ← already uploaded
├── docker-compose.yml
├── setup-database.sql
├── agent_outputs/               ← where agents save built websites
└── orchestrator/
    ├── Dockerfile
    ├── orchestrator.py
    └── requirements.txt
```

---

## STEP 1 — Upload Build Files (5 min)

From PowerShell on your LOCAL machine:

```powershell
# docker-compose
scp -i C:\Users\HUAWEI\.ssh\id_ed25519 D:\Ai_Sandbox\agentsHQ\infrasctructure\docker-compose.yml root@72.60.209.109:~/agentsHQ/docker-compose.yml

# database setup script
scp -i C:\Users\HUAWEI\.ssh\id_ed25519 D:\Ai_Sandbox\agentsHQ\server-setup\setup-database.sql root@72.60.209.109:~/agentsHQ/setup-database.sql

# orchestrator files
scp -i C:\Users\HUAWEI\.ssh\id_ed25519 D:\Ai_Sandbox\agentsHQ\agent-brain\orchestrator.py root@72.60.209.109:~/agentsHQ/orchestrator/orchestrator.py
scp -i C:\Users\HUAWEI\.ssh\id_ed25519 D:\Ai_Sandbox\agentsHQ\agent-brain\requirements.txt root@72.60.209.109:~/agentsHQ/orchestrator/requirements.txt
scp -i C:\Users\HUAWEI\.ssh\id_ed25519 D:\Ai_Sandbox\agentsHQ\agent-brain\Dockerfile root@72.60.209.109:~/agentsHQ/orchestrator/Dockerfile
```

Verify structure on VPS:

```bash
ssh root@72.60.209.109 "find ~/agentsHQ -type f"
```

---

## STEP 2 — Create Required Folders on VPS (1 min)

```bash
ssh root@72.60.209.109 "mkdir -p ~/agentsHQ/agent_outputs"
```

---

## STEP 3 — Run Database Setup (2 min)

```bash
ssh root@72.60.209.109
cd ~/agentsHQ
docker compose up -d postgres
```

Wait 10 seconds for PostgreSQL to initialize, then:

```bash
docker compose exec postgres psql -U postgres -f /docker-entrypoint-initdb.d/setup-database.sql
```

If that fails, try:

```bash
cat setup-database.sql | docker compose exec -T postgres psql -U postgres
```

Verify tables were created:

```bash
docker compose exec postgres psql -U postgres -c "\dt"
```

Expected: 5 tables — n8n_chat_histories, conversation_archive, task_queue, sop_changelog, security_events

---

## STEP 4 — Build and Start the Full Stack (10-15 min)

```bash
cd ~/agentsHQ
docker compose up -d
```

Watch the orchestrator build (first time takes 5-10 min — installing Python packages):

```bash
docker compose logs orchestrator -f
```

Wait for this line:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Press Ctrl+C when you see it.

Verify all containers are healthy:

```bash
docker compose ps
```

Expected containers running:
- root-traefik-1 (existing)
- root-n8n-1 (existing)
- agentshq-postgres-1
- agentshq-qdrant-1
- agentshq-waha-1
- agentshq-orchestrator-1 (orc-crewai)

Verify orchestrator health:

```bash
curl http://localhost:8000/health
# Expected: {"status":"ok"}

curl http://localhost:8000/
# Expected: {"status":"running","service":"Boubacar Orchestrator",...}
```

---

## STEP 5 — Import Workflow in n8n (5 min)

1. Open https://n8n.srv1040886.hstgr.cloud
2. Log in with your credentials (2FA via Authy)
3. Deactivate any existing main workflow (toggle off)
4. Click + New Workflow → top menu → Import from JSON
5. Paste contents of `D:\Ai_Sandbox\agentsHQ\n8n-workflows\workflow-whatsapp-v6.json`
6. Set the PostgreSQL credential (host: postgres, db: postgres, user: postgres, password: from .env)
7. ACTIVATE the workflow (toggle on)
8. Save

---

## STEP 6 — Connect WhatsApp via WAHA

1. Open http://72.60.209.109:3000 (WAHA dashboard)
2. Start a new session named `default`
3. Scan the QR code with WhatsApp on your phone
   (Use the Google Voice number on your agent Google account)
4. Wait for status: CONNECTED
5. Test: send a message to your agent's WhatsApp number from your personal phone

---

## STEP 7 — THE TEST (Moment of Truth)

Send this EXACT message to your agent's WhatsApp number:

```
Create a website for Saveurs d'Afrique — an African fusion
restaurant in Atlanta serving West African and Southern
American cuisine
```

WHAT HAPPENS NEXT:
1. Within 5 seconds: acknowledgment on WhatsApp
   "⏳ Got it. My agents are working on this now..."
2. Agents start working — watch in n8n Executions tab
3. After 2-5 minutes: full result delivered on WhatsApp
4. HTML file saved to ~/agentsHQ/agent_outputs/

Watch the agents think in real time:

```bash
docker logs orc-crewai -f
```

---

## STEP 8 — View the Built Website

```bash
ssh root@72.60.209.109 "ls ~/agentsHQ/agent_outputs/"
```

Copy to your local machine:

```powershell
scp -i C:\Users\HUAWEI\.ssh\id_ed25519 root@72.60.209.109:~/agentsHQ/agent_outputs/website_TIMESTAMP.html D:\Desktop\
```

Open in browser. That is a website built by your agents from a single WhatsApp message.

---

## TROUBLESHOOTING

### Orchestrator won't start:
```bash
docker compose logs orchestrator --tail 50
```

### Build fails (package install error):
```bash
docker compose build orchestrator --no-cache
```

### n8n can't reach the orchestrator:
```bash
docker exec -it root-n8n-1 wget -O- http://orc-crewai:8000/health
```

### Agent times out:
The workflow timeout is 5 minutes. For first run, try a simpler test:
```
Create a simple one-page website for a pizza restaurant
```

### Research agent can't search:
```bash
# Verify SERPER_API_KEY in .env then:
docker compose restart orchestrator
```

---

## WHAT'S DEFERRED TO PHASE 5

These are NOT needed to get the agent working. Add them later:

- WhatsApp number setup (Google Voice via agent Google account)
- workflow-SUB-always-save.json (saves to GitHub + Drive + Notion)
- GOOGLE_DRIVE_FOLDER_ID
- NOTION_SECRET
- NOTION_DATABASE_ID (agent creates the database, you get the ID after)

---

## ADDING NEW AGENTS IN THE FUTURE

1. Add a new Agent definition in orchestrator.py
2. Add a new Task in build_tasks()
3. Add it to the agents dict and task list
4. Restart: `docker compose restart orchestrator`
5. Done — no rebuild needed

---

## HOW OTHER TOOLS ACCESS YOUR AGENTS

From Cursor, Claude Code, or any HTTP client:

```bash
curl -X POST http://72.60.209.109:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task": "your task here", "from_number": "cursor"}'
```

One endpoint. All agents. From anywhere.
