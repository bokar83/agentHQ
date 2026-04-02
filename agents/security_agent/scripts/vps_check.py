"""
vps_check.py — VPS health and port scanner
Part of SecureWatch (agentsHQ security_agent)

Runs lightweight checks against the VPS to detect exposed dangerous
ports or services that should not be publicly accessible.
"""

import socket
from typing import Optional


# Ports that should be closed/firewalled from the public internet
# (Only accessible via internal Docker network or VPN)
DANGEROUS_PORTS = {
    5432: "PostgreSQL (should NOT be internet-accessible)",
    6333: "Qdrant vector DB (should NOT be internet-accessible)",
    6334: "Qdrant gRPC (should NOT be internet-accessible)",
    27017: "MongoDB (should NOT be internet-accessible)",
    6379: "Redis (should NOT be internet-accessible)",
    8080: "HTTP alt (acceptable but monitor)",
}

# Ports that should be open (expected services)
EXPECTED_OPEN_PORTS = {
    80: "HTTP (Nginx/Caddy)",
    443: "HTTPS (Nginx/Caddy)",
    22: "SSH (should use key auth only)",
    5678: "n8n dashboard (acceptable if firewalled by auth)",
}

TIMEOUT_SECONDS = 3


def check_port(host: str, port: int) -> bool:
    """Return True if the port is reachable (open)."""
    try:
        with socket.create_connection((host, port), timeout=TIMEOUT_SECONDS):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False


def check_vps_health(vps_ip: str) -> list[dict]:
    """
    Run port checks against the VPS.
    Returns list of findings.
    """
    findings = []

    # Check dangerous ports that should NOT be open
    for port, description in DANGEROUS_PORTS.items():
        if check_port(vps_ip, port):
            findings.append({
                "type": "DANGEROUS_PORT_OPEN",
                "severity": "CRITICAL",
                "port": port,
                "message": f"Port {port} is publicly accessible — {description}",
                "action": f"Run on VPS: ufw deny {port} (or restrict to Docker internal network)",
            })

    # Note: we don't flag expected ports, just include a summary
    open_expected = []
    for port, description in EXPECTED_OPEN_PORTS.items():
        if check_port(vps_ip, port):
            open_expected.append(f"{port} ({description})")

    # SSH check — warn if found, not critical (it's expected, but worth knowing)
    if check_port(vps_ip, 22):
        findings.append({
            "type": "SSH_OPEN",
            "severity": "INFO",
            "port": 22,
            "message": "SSH (port 22) is accessible — verify key-only auth is enforced",
            "action": "Ensure PasswordAuthentication no in /etc/ssh/sshd_config",
        })

    return findings


if __name__ == "__main__":
    import sys
    import json

    vps_ip = sys.argv[1] if len(sys.argv) > 1 else None
    if not vps_ip:
        print("Usage: python vps_check.py <VPS_IP>")
        sys.exit(1)

    results = check_vps_health(vps_ip)
    critical = [r for r in results if r["severity"] == "CRITICAL"]
    if critical:
        print(f"🚨 Found {len(critical)} critical VPS issue(s):")
        print(json.dumps(results, indent=2))
        sys.exit(2)
    elif results:
        print(f"⚠️  Found {len(results)} VPS notice(s):")
        print(json.dumps(results, indent=2))
        sys.exit(1)
    else:
        print("✅ VPS health looks good.")
        sys.exit(0)
