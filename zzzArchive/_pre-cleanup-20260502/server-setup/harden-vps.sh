#!/bin/bash
# ============================================================
# BOUBACAR VPS HARDENING SCRIPT v1.0
# Run ONCE after your first SSH login to the VPS
# Ubuntu 22.04 / 24.04 (Hostinger)
# ============================================================
# BEFORE RUNNING: Make sure you have your SSH key copied
# to the VPS already. Run from your LOCAL machine first:
#   ssh-copy-id root@YOUR_VPS_IP
# Then SSH in and run this script.
# ============================================================

set -e
echo "=== BOUBACAR VPS HARDENING — START ==="

# Step 1: Update everything
echo "[1/7] Updating system..."
apt update && apt upgrade -y
apt install -y ufw fail2ban unattended-upgrades curl wget net-tools

# Step 2: Create non-root admin user
echo "[2/7] Creating admin user..."
if ! id "orc-admin" &>/dev/null; then
  adduser --disabled-password --gecos "" orc-admin
  usermod -aG sudo orc-admin
  mkdir -p /home/orc-admin/.ssh
  cp /root/.ssh/authorized_keys /home/orc-admin/.ssh/ 2>/dev/null || true
  chown -R orc-admin:orc-admin /home/orc-admin/.ssh
  chmod 700 /home/orc-admin/.ssh
  chmod 600 /home/orc-admin/.ssh/authorized_keys 2>/dev/null || true
  echo "Created: orc-admin"
else
  echo "orc-admin already exists — skipping"
fi

# Step 3: Harden SSH
echo "[3/7] Hardening SSH..."
cat > /etc/ssh/sshd_config.d/00-hardening.conf << 'EOF'
PasswordAuthentication no
PermitRootLogin no
PermitEmptyPasswords no
MaxAuthTries 3
X11Forwarding no
PubkeyAuthentication yes
EOF
systemctl reload sshd
echo "SSH hardened"

# Step 4: Firewall
echo "[4/7] Configuring UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   comment 'SSH'
ufw allow 80/tcp   comment 'HTTP'
ufw allow 443/tcp  comment 'HTTPS'
ufw allow 5678/tcp comment 'n8n dashboard'
ufw --force enable
echo "UFW active — ports open: 22, 80, 443, 5678"

# Step 5: Fail2ban
echo "[5/7] Configuring Fail2ban..."
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 3

[sshd]
enabled  = true
port     = ssh
logpath  = /var/log/auth.log
maxretry = 3
EOF
systemctl enable fail2ban
systemctl restart fail2ban
echo "Fail2ban active"

# Step 6: Auto security updates
echo "[6/7] Enabling auto security updates..."
cat > /etc/apt/apt.conf.d/20auto-upgrades << 'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF
echo "Auto-updates enabled"

# Step 7: Install Docker if not present
echo "[7/7] Checking Docker..."
if ! command -v docker &> /dev/null; then
  echo "Installing Docker..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  usermod -aG docker $USER
  usermod -aG docker orc-admin
  echo "Docker installed"
else
  echo "Docker already installed: $(docker --version)"
fi

if ! docker compose version &> /dev/null; then
  apt install -y docker-compose-plugin
fi

echo ""
echo "=== HARDENING COMPLETE ==="
echo ""
echo "NEXT STEPS:"
echo "1. Open a NEW terminal and test: ssh orc-admin@YOUR_VPS_IP"
echo "2. If that works, you are good — root login is now disabled"
echo "3. Continue with the README instructions"
echo ""
echo "Firewall status:"
ufw status verbose
echo ""
echo "Fail2ban status:"
fail2ban-client status
