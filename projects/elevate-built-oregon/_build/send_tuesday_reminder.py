"""
Standalone Telegram-reminder fallback for Rod outreach.

If the in-session cron job dies (Claude session restarts before Tuesday May 6),
schedule THIS script via Windows Task Scheduler instead. It has zero
dependencies beyond stdlib Python.

To schedule via Task Scheduler:
  schtasks /Create /SC ONCE /SD 05/06/2026 /ST 09:03 /TN "RodReminder" \
    /TR "python d:\\Ai_Sandbox\\agentsHQ\\projects\\elevate-built-oregon\\_build\\send_tuesday_reminder.py"

Or just run it manually if you remember on Tuesday morning.
"""
import urllib.request, urllib.parse, json, sys

TOKEN = '8777275362:AAE6XBLzEnwufW6m074H2A-8fNZO29rbRTg'
CHAT_ID = '7792432594'

TEXT = """🔔 *Tuesday - reach out to Rod today.*

*Project:* Elevate Roofing & Construction (Medford OR)
*Folder:* `d:/Ai_Sandbox/agentsHQ/projects/elevate-built-oregon/`

*Steps:*
1. Deploy demo: `cd site && vercel --prod`
2. Open `MESSAGE_TO_ROD.md` - pick Version A (text) or B (email)
3. Replace `[LINK]` with Vercel URL
4. (Email only) Print `audit-one-pager.html` to PDF, attach
5. Send

*Hard rules:*
- ❌ NO price mention in first touch
- ❌ NO "free" or "discount"
- ✅ Demo IS the pitch
- ✅ Wait 7 days before any follow-up

*If Rod asks price:* "$1,500 + a referral or two if you've got contractors in your network. Or trade - I need a roof inspection on a property anyway."

Full plan: `MESSAGE_TO_ROD.md` + `REMINDER_TUESDAY_MAY_6.md`"""


def send():
    data = urllib.parse.urlencode({
        'chat_id': CHAT_ID,
        'text': TEXT,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': 'true',
    }).encode()
    req = urllib.request.Request(
        f'https://api.telegram.org/bot{TOKEN}/sendMessage',
        data=data,
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        body = json.loads(r.read())
        if body.get('ok'):
            print(f"Sent. msg_id={body.get('result', {}).get('message_id')}")
            return 0
        print(f"FAILED: {body}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(send())
