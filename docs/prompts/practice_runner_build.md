# Build Prompt: Practice Runner AI
**Status**: Ready to Run
**Protocol**: `app_build`

### The Prompt
```text
/app_build
Build the "Practice Runner AI" application.

Execution Directives:
1. CONTEXT: Search for the 'Practice Runner' entry in our Notion Ideas database (using the IDEAS_DB_ID from .env).
2. INFRASTRUCTURE: Use the 'create_github_repo' tool to initialize a new repository named 'practice-runner-app' under user 'bokar83'. 
3. DEVELOPMENT: Scaffold a Next.js (TypeScript) application inside the 'practice-runner-app' directory.
4. FEATURE SET:
   - Implement the AI Roleplay Simulator as described in the Notion spec.
   - Implement the Performance Feedback loop using Claude-3.5-Sonnet logic.
   - Design a premium, high-stakes dashboard UI (Catalyst Works aesthetic).
5. DEPLOYMENT: Push the code to the 'main' branch of 'practice-runner-app' and prepare the project for Vercel deployment.

Deliverable: A functional repository at 'practice-runner-app' with all core features implemented and ready for review.
```

---
### Technical Notes for Boubacar
- **Fixed Agents**: `Strategic Planner` and `App Builder` have been upgraded with `ORCHESTRATION_TOOLS`.
- **Environment**: `IDEAS_DB_ID` is set to `33bbcf1a-3029-817e-966f-fb1b8fab0ff5` in your `.env`.
- **Repo Name**: Target is `practice-runner-app` (public by default).
