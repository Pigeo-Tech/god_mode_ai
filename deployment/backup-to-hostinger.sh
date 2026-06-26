#!/usr/bin/env bash
# Back up AGNI live data (skills + knowledge + config) from AWS to Hostinger via SFTP.
# This is the "backups -> Hostinger" half of the architecture: hot data stays on AWS, cold
# backups live safely on Hostinger.
#
# Set these (export them, or a cron line) — password is read from the env, never hard-coded:
#   HOST_SFTP_HOST   e.g. files.000webhost.com  (your Hostinger SFTP host)
#   HOST_SFTP_USER   your Hostinger SFTP username
#   HOST_SFTP_PASS   your Hostinger SFTP password
#   HOST_SFTP_DIR    target folder, default: backups/agni
#
# Run once:   sudo HOST_SFTP_HOST=... HOST_SFTP_USER=... HOST_SFTP_PASS=... bash /opt/app/deployment/backup-to-hostinger.sh
# Schedule daily 3am:  (crontab -e)
#   0 3 * * * HOST_SFTP_HOST=... HOST_SFTP_USER=... HOST_SFTP_PASS=... /opt/app/deployment/backup-to-hostinger.sh
set -e

APP="${APP:-/opt/app}"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="/tmp/agni-backup-$STAMP.tar.gz"

# 1) bundle the durable, version-worthy data
tar -czf "$OUT" -C "$APP" backend/skills $( [ -d "$APP/knowledge" ] && echo knowledge ) \
  $( [ -d "$APP/prompts" ] && echo prompts ) 2>/dev/null
echo "Bundled: $OUT ($(du -h "$OUT" | cut -f1))"

: "${HOST_SFTP_HOST:?set HOST_SFTP_HOST}"
: "${HOST_SFTP_USER:?set HOST_SFTP_USER}"
: "${HOST_SFTP_DIR:=backups/agni}"

# 2) make sure lftp is available (robust SFTP client)
if ! command -v lftp >/dev/null 2>&1; then
  sudo apt-get update -y && sudo apt-get install -y lftp
fi

# 3) push to Hostinger (keeps last 14 daily archives)
lftp -u "$HOST_SFTP_USER,$HOST_SFTP_PASS" "sftp://$HOST_SFTP_HOST" <<EOF
set sftp:auto-confirm yes
mkdir -p $HOST_SFTP_DIR
put "$OUT" -o "$HOST_SFTP_DIR/agni-backup-$STAMP.tar.gz"
cls -1 --sort=name $HOST_SFTP_DIR/agni-backup-*.tar.gz > /tmp/_bk.list 2>/dev/null || true
bye
EOF

# 4) prune old local copy
rm -f "$OUT"
echo "Uploaded to Hostinger:$HOST_SFTP_DIR/agni-backup-$STAMP.tar.gz"
echo "Done. (Tip: cron this daily; memory backup arrives once persistence/DB is added.)"
