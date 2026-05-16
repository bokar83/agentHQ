#!/usr/bin/env python3
"""
ritual_cron_dispatch.py - cron entrypoint for Saturday ritual dispatch.

Invoked from /etc/cron.d/lighthouse-rituals on the VPS:

    0 16 * * 6 root docker exec orc-crewai \\
        python /app/scripts/ritual_cron_dispatch.py lr4_triad_lock \\
        >> /var/log/lighthouse-rituals.log 2>&1

Reads OWNER_TELEGRAM_CHAT_ID from env and posts the intro message with
[Start now][Hold] inline-keyboard. The orchestrator's existing
telegram_polling_loop handles the button taps from there.
"""
import os
import sys

# Allow running from the scripts/ dir or from /app inside the container.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.abspath(os.path.join(_HERE, ".."))
if _ORCH not in sys.path:
    sys.path.insert(0, _ORCH)


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: ritual_cron_dispatch.py <ritual_key> [chat_id]", file=sys.stderr)
        return 2
    ritual_key = argv[1]
    chat_id = argv[2] if len(argv) > 2 else os.environ.get("OWNER_TELEGRAM_CHAT_ID")
    if not chat_id:
        print("OWNER_TELEGRAM_CHAT_ID not set; aborting", file=sys.stderr)
        return 3
    from ritual_engine import cron_dispatch
    result = cron_dispatch(ritual_key, chat_id)
    print(f"dispatched ritual={ritual_key} chat={chat_id} message_id={result.get('message_id')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
