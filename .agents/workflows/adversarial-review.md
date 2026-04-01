---
description: Two-Tier Code Quality System (Pulse Scan vs. Deep Audit)
---
# Antigravity Review Tiers (AAR System)

This document defines the two levels of code quality assurance for **agentsHQ**.

## 🔴 Level 1: Pulse Scan (Daily)
**Goal:** Quick, high-level sanity check for operational continuity.
- **Frequency:** Daily (or every PR).
- **Checks:**
    - **Broken Logic:** Syntax errors, circular imports, or obvious null-pointer risks.
    - **Integration Check:** Do the updated endpoints still talk to the expected VPS ports?
    - **n8n Alignment:** Does the orchestrator still accept the trigger from the Telegram bot?
- **Quota:** Zero forced findings. If it's clean, mark as **PASS**.

## 🛑 Level 2: Deep Audit (Adversarial) 
**Goal:** High-rigor stress-test for security and architectural debt.
- **Frequency:** Every 2-3 Days.
- **Persona:** Skeptical Hostile Auditor.
- **Critical Safety Rule:** **NO HALLUCINATION.** If no vulnerabilities are found, the auditor must provide a **Proof of Resilience** (listing 5 distinct 'attack attempts' and why they failed) instead of making up issues.
- **Checks:**
    - **Security:** Path traversal, API credential leakage, unauthorized command injection.
    - **Performance:** Async race conditions, redundant database calls, memory leaks.
    - **Logic:** "Edge of the Map" scenarios (unhandled error codes, malformed JSON, network timeouts).
- **Quota:** 3 Critical + 2 Architectural findings (unless Proof of Resilience is provided).

---

### Phase-by-Phase Adversarial Protocol (Deep Audit)

1.  **Skeptical Reading:** Assume the code is broken. Use `view_file` on all related logic.
2.  **Assumption Mapping:** Document every "trusted" input or service call.
3.  **Active Stress-Test:** Create a scratch script in `/tmp/` to mock bad data.
4.  **Revenue Engine Audit:** Verify the "Catalyst Works" voice and lead-gen metrics remain intact.
5.  **Findings/Verdict:** Deliver the `adversarial_report.md` artifact.
