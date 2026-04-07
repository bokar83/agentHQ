import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from dotenv import load_dotenv

load_dotenv("d:/Ai_Sandbox/agentsHQ/.env")

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")

if not SMTP_USER or not SMTP_PASS:
    print("Error: SMTP_USER or SMTP_PASS not found in .env")
    exit(1)

to_addresses = ["bokar83@gmail.com", "catalystworks.ai@gmail.com"]
subject = "Sankofa Council - Generated Architecture Diagram & MMD Source"

body = """
Hello,

Please find attached the Mermaid diagram visualizing the Sankofa Council internal logic mapping.

Included attachments: 
1. The rendered PNG utilizing the custom Catalyst Works Dark Mode template.
2. The raw .mmd text source file.

Best regards,
agentsHQ
"""

msg = MIMEMultipart()
msg['From'] = SMTP_USER
msg['To'] = ", ".join(to_addresses)
msg['Subject'] = subject

msg.attach(MIMEText(body, 'plain'))

# Find the latest diagram (PNG)
import glob
diagrams = glob.glob("d:/Ai_Sandbox/agentsHQ/outputs/diagrams/diagram_*.png")
if not diagrams:
    print("Error: No diagram found")
    exit(1)

latest_diagram = max(diagrams, key=os.path.getmtime)

with open(latest_diagram, 'rb') as f:
    img_data = f.read()

image = MIMEImage(img_data, name="sankofa_council_map.png")
msg.attach(image)

# Attach MMD source
mmd_path = "d:/Ai_Sandbox/agentsHQ/outputs/diagrams/sankofa_council.mmd"
if os.path.exists(mmd_path):
    with open(mmd_path, 'r', encoding='utf-8') as f:
        mmd_src = MIMEApplication(f.read(), _subtype="txt")
        mmd_src.add_header('Content-Disposition', 'attachment', filename="sankofa_council.mmd")
        msg.attach(mmd_src)

try:
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.send_message(msg)
    print(f"Email sent successfully to {', '.join(to_addresses)}")
except Exception as e:
    print(f"Failed to send email: {e}")
