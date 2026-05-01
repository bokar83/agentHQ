"""DRAFT extension to orchestrator/app.py.

Pre-staged 2026-04-30. NOT a new file. The route below gets APPENDED to
orchestrator/app.py near the existing /inbound-lead route (line 657).

The route is auth-gated by the existing verify_api_key dependency, so the
n8n workflow uses the same X-API-Key Header Auth credential as the Calendly
inbound flow.

Sync execution: the route blocks 30-60s while the scorer runs. n8n is
configured with a long timeout on the HTTP Request node, and the webhook
response mode is "respond when last node finishes" so the browser holds
its connection open through the whole chain.
"""

# === BEGIN PASTE-IN APPEND TO orchestrator/app.py =======================


@app.post("/score-request", dependencies=[Depends(verify_api_key)])
async def score_request_endpoint(request: Request):
    """Inbound AI Visibility Score request from geolisted.co (via n8n).

    Sync. Blocks ~30-60s while the scorer runs OpenRouter + SerpAPI calls.
    On success, returns ScoreResult JSON to the caller (n8n responds back
    to the browser with this same payload through the open webhook).

    On scoring failure, returns 500 with a brief error. The n8n workflow's
    error branch (TODO Friday) handles fallback messaging to the visitor.

    Side effects (best-effort, do not raise):
      - Insert lead row in Supabase with source='geolisted.co - Score Request'
      - Render and send/draft the full report email to the visitor's address
      - Telegram notification (reusing the inbound-lead notify pattern)
    """
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON body: {e}")

    logger.info(
        f"Score request received: {body.get('email', '(no email)')} "
        f"business={body.get('business', '?')} city={body.get('city', '?')}"
    )

    try:
        from skills.score_request.runner import run_score_request
        result = run_score_request(body)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=f"Payload validation failed: {exc.errors()[:1]}")
    except Exception as exc:
        logger.error(f"Score request runner raised: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Scoring failed: {type(exc).__name__}")

    # Best-effort Telegram notification (mirrors inbound_lead pattern)
    try:
        from notifier import send_message
        telegram_chat = os.environ.get("TELEGRAM_CHAT_ID", "")
        if telegram_chat:
            msg = (
                f"New geolisted.co score request:\n"
                f"  {body.get('business', '?')} ({body.get('city', '?')})\n"
                f"  {body.get('email', '?')}\n"
                f"  Score: {result.get('score', '?')}/100\n"
                f"  Email status: {result.get('email_status', '?')}"
            )
            send_message(telegram_chat, msg)
    except Exception as notify_exc:
        logger.warning(f"Score request Telegram notify failed: {notify_exc}")

    return result


# === END PASTE-IN APPEND ===============================================
