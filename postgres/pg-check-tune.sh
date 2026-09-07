#!/usr/bin/env bash
# pg-check-tune.sh — Diagnose and tune PostgreSQL in Docker on EC2
# Run from your Mac:  EC2_IP=<ip> ./pg-check-tune.sh
# Or directly on EC2: bash pg-check-tune.sh --local
#
# Flags:
#   --local      skip SSH, run directly on the EC2 host
#   --apply      apply the recommended settings and reload Postgres (default: dry-run)
#   --target N   target concurrent users (default: 50)

set -e

# ── Config ──────────────────────────────────────────────────────────────────
EC2_IP="${EC2_IP:-ec2-18-205-38-130.compute-1.amazonaws.com}"
EC2_USER="${EC2_USER:-ubuntu}"
TARGET_USERS="${TARGET_USERS:-50}"
APPLY=false
LOCAL=false
PG_USER="${PG_USER:-postgres}"
PG_DB="${PG_DB:-postgres}"

for arg in "$@"; do
  case $arg in
    --apply)  APPLY=true  ;;
    --local)  LOCAL=true  ;;
    --target) TARGET_USERS="$2"; shift ;;
  esac
done

# ── Remote execution wrapper ─────────────────────────────────────────────────
run_remote() {
  if [ "$LOCAL" = "true" ]; then
    bash -s <<'LOCALEOF'
LOCALEOF
  else
    ssh -o ConnectTimeout=10 "${EC2_USER}@${EC2_IP}" bash -s
  fi
}

# ── Main payload (runs on EC2) ───────────────────────────────────────────────
APPLY_FLAG="$APPLY"
TARGET="$TARGET_USERS"
PGUSER="$PG_USER"
PGDB="$PG_DB"
PGPASSWORD_VAL="${PGPASSWORD:-}"

if [ "$LOCAL" = "true" ]; then
  REMOTE_CMD="bash"
else
  REMOTE_CMD="ssh -o ConnectTimeout=10 ${EC2_USER}@${EC2_IP} bash -s"
fi

$REMOTE_CMD <<SSHEOF
set -e
APPLY=${APPLY_FLAG}
TARGET=${TARGET}
PGUSER=${PGUSER}
PGDB=${PGDB}
PGPASSWORD=${PGPASSWORD_VAL}
SEP="──────────────────────────────────────────────────────────────"

echo ""
echo "\$SEP"
echo "  PostgreSQL Connection & Tuning Diagnostic"
echo "  Target: \${TARGET} concurrent users"
echo "\$SEP"

# ── 1. Find postgres container ──────────────────────────────────────────────
echo ""
echo "[ 1/6 ] Detecting PostgreSQL container..."
PG_CONTAINER=\$(docker ps --format '{{.Names}}' | grep -iE 'postgres|pg' | head -1 || true)

if [ -z "\$PG_CONTAINER" ]; then
  echo "ERROR: No running container matching 'postgres' or 'pg'."
  echo "       Running containers:"
  docker ps --format '  {{.Names}}\t{{.Image}}\t{{.Status}}'
  exit 1
fi
echo "  Container : \$PG_CONTAINER"
echo "  Image     : \$(docker inspect --format '{{.Config.Image}}' "\$PG_CONTAINER")"
echo "  Status    : \$(docker inspect --format '{{.State.Status}}' "\$PG_CONTAINER")"

# Helper: run psql inside the container (PGPASSWORD avoids interactive password prompt)
psql_exec() { docker exec -e "PGPASSWORD=\${PGPASSWORD}" "\$PG_CONTAINER" psql -U "\$PGUSER" -d "\$PGDB" -t -c "\$1" 2>/dev/null | sed 's/^[ \t]*//;s/[ \t]*$//'; }

# ── 2. EC2 host RAM ─────────────────────────────────────────────────────────
echo ""
echo "[ 2/6 ] Host memory..."
TOTAL_KB=\$(grep MemTotal /proc/meminfo | awk '{print \$2}')
TOTAL_MB=\$((TOTAL_KB / 1024))
TOTAL_GB_RAW=\$(echo "scale=1; \$TOTAL_MB / 1024" | bc)
AVAIL_KB=\$(grep MemAvailable /proc/meminfo | awk '{print \$2}')
AVAIL_MB=\$((AVAIL_KB / 1024))
echo "  Total RAM   : \${TOTAL_MB} MB  (\${TOTAL_GB_RAW} GB)"
echo "  Available   : \${AVAIL_MB} MB"

# ── 3. Current PostgreSQL settings ─────────────────────────────────────────
echo ""
echo "[ 3/6 ] Current PostgreSQL settings..."

MAX_CONN=\$(psql_exec "SHOW max_connections;" | grep -v '^$' | head -1)
SHARED_BUF=\$(psql_exec "SHOW shared_buffers;" | grep -v '^$' | head -1)
WORK_MEM=\$(psql_exec "SHOW work_mem;" | grep -v '^$' | head -1)
MAINT_WORK=\$(psql_exec "SHOW maintenance_work_mem;" | grep -v '^$' | head -1)
EFF_CACHE=\$(psql_exec "SHOW effective_cache_size;" | grep -v '^$' | head -1)
WAL_BUFS=\$(psql_exec "SHOW wal_buffers;" | grep -v '^$' | head -1)
CP_COMPL_TGT=\$(psql_exec "SHOW checkpoint_completion_target;" | grep -v '^$' | head -1)
LOG_CHECKPOINTS=\$(psql_exec "SHOW log_checkpoints;" | grep -v '^$' | head -1)

printf "  %-35s %s\n" "max_connections"              "\$MAX_CONN"
printf "  %-35s %s\n" "shared_buffers"               "\$SHARED_BUF"
printf "  %-35s %s\n" "work_mem"                     "\$WORK_MEM"
printf "  %-35s %s\n" "maintenance_work_mem"         "\$MAINT_WORK"
printf "  %-35s %s\n" "effective_cache_size"         "\$EFF_CACHE"
printf "  %-35s %s\n" "wal_buffers"                  "\$WAL_BUFS"
printf "  %-35s %s\n" "checkpoint_completion_target" "\$CP_COMPL_TGT"
printf "  %-35s %s\n" "log_checkpoints"              "\$LOG_CHECKPOINTS"

# PostgreSQL version
PG_VER=\$(psql_exec "SELECT version();" | grep -o 'PostgreSQL [0-9.]*' | head -1)
echo "  Version     : \$PG_VER"

# ── 4. Current connection usage ─────────────────────────────────────────────
echo ""
echo "[ 4/6 ] Current connection usage..."

psql_exec "
SELECT
  state,
  count(*) AS count
FROM pg_stat_activity
GROUP BY state
ORDER BY count DESC;" | grep -v '^$' | awk '{printf "  %-20s %s\n", \$1, \$3}'

echo ""
echo "  Per-database connection counts:"
psql_exec "
SELECT
  datname AS database,
  count(*) AS connections,
  round(count(*) * 100.0 / current_setting('max_connections')::int, 1) AS pct_of_max
FROM pg_stat_activity
WHERE datname IS NOT NULL
GROUP BY datname
ORDER BY connections DESC;" | grep -v '^$' | awk '{printf "  %-25s connections=%-5s (%.1f%% of max)\n", \$1, \$3, \$5}'

echo ""
MAX_CONN_INT=\${MAX_CONN//[!0-9]/}
ACTIVE_TOTAL=\$(psql_exec "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';" | grep -v '^$' | tr -d ' ')
IDLE_TOTAL=\$(psql_exec "SELECT count(*) FROM pg_stat_activity WHERE state = 'idle';" | grep -v '^$' | tr -d ' ')
ALL_TOTAL=\$(psql_exec "SELECT count(*) FROM pg_stat_activity;" | grep -v '^$' | tr -d ' ')

echo "  Active : \${ACTIVE_TOTAL:-0}"
echo "  Idle   : \${IDLE_TOTAL:-0}"
echo "  Total  : \${ALL_TOTAL:-0} / \$MAX_CONN_INT"
PCT_USED=\$(echo "scale=1; \${ALL_TOTAL:-0} * 100 / \$MAX_CONN_INT" | bc)
echo "  Usage  : \${PCT_USED}%"

# ── 5. Calculate recommended settings ───────────────────────────────────────
echo ""
echo "[ 5/6 ] Recommended settings for \${TARGET} concurrent users..."

# max_connections: target users + 20% headroom + 3 reserved for superuser
REC_MAX_CONN=\$(echo "\$TARGET + (\$TARGET / 5) + 3" | bc)
# Ensure minimum of 100
[ "\$REC_MAX_CONN" -lt 100 ] && REC_MAX_CONN=100

# shared_buffers: 25% of total RAM (in MB, expressed as xMB)
SB_MB=\$(echo "\$TOTAL_MB / 4" | bc)
[ "\$SB_MB" -lt 128 ] && SB_MB=128
REC_SHARED_BUF="\${SB_MB}MB"

# work_mem: (RAM * 0.25) / (max_connections * 2) — conservative for parallel queries
WM_MB=\$(echo "scale=0; (\$TOTAL_MB / 4) / (\$REC_MAX_CONN * 2)" | bc)
[ "\$WM_MB" -lt 4 ]  && WM_MB=4
[ "\$WM_MB" -gt 64 ] && WM_MB=64
REC_WORK_MEM="\${WM_MB}MB"

# maintenance_work_mem: min(RAM/8, 256MB)
MM_MB=\$(echo "\$TOTAL_MB / 8" | bc)
[ "\$MM_MB" -gt 256 ] && MM_MB=256
[ "\$MM_MB" -lt 64 ]  && MM_MB=64
REC_MAINT_MEM="\${MM_MB}MB"

# effective_cache_size: 75% of total RAM
EC_MB=\$(echo "(\$TOTAL_MB * 3) / 4" | bc)
REC_EFF_CACHE="\${EC_MB}MB"

# wal_buffers: 16MB is good for most workloads
REC_WAL_BUFS="16MB"

printf "  %-35s current=%-12s  recommended=%s\n" "max_connections"      "\$MAX_CONN"     "\$REC_MAX_CONN"
printf "  %-35s current=%-12s  recommended=%s\n" "shared_buffers"       "\$SHARED_BUF"   "\$REC_SHARED_BUF"
printf "  %-35s current=%-12s  recommended=%s\n" "work_mem"             "\$WORK_MEM"     "\$REC_WORK_MEM"
printf "  %-35s current=%-12s  recommended=%s\n" "maintenance_work_mem" "\$MAINT_WORK"   "\$REC_MAINT_MEM"
printf "  %-35s current=%-12s  recommended=%s\n" "effective_cache_size" "\$EFF_CACHE"    "\$REC_EFF_CACHE"
printf "  %-35s current=%-12s  recommended=%s\n" "wal_buffers"          "\$WAL_BUFS"     "\$REC_WAL_BUFS"
printf "  %-35s current=%-12s  recommended=%s\n" "checkpoint_completion_target" "\$CP_COMPL_TGT" "0.9"

# Warn if max_connections is already over recommendation
if [ "\$MAX_CONN_INT" -ge "\$REC_MAX_CONN" ]; then
  echo ""
  echo "  NOTE: max_connections (\$MAX_CONN_INT) already meets the target."
fi

# ── 6. Apply changes (if --apply was passed) ────────────────────────────────
echo ""
if [ "\$APPLY" = "true" ]; then
  echo "[ 6/6 ] Applying recommended settings to postgresql.conf..."

  # Locate postgresql.conf inside the container
  PG_CONF=\$(docker exec "\$PG_CONTAINER" psql -U "\$PGUSER" -d "\$PGDB" -t -c "SHOW config_file;" 2>/dev/null | tr -d ' \n')
  echo "  Config file: \$PG_CONF"

  apply_setting() {
    local KEY="\$1" VAL="\$2"
    # Comment out existing entries for this key, then append the new value
    docker exec "\$PG_CONTAINER" bash -c "
      sed -i \"s|^\s*\${KEY}\s*=.*|# & # tuned by pg-check-tune.sh|\" \"\$PG_CONF\"
      echo \"\${KEY} = '\${VAL}'  # tuned by pg-check-tune.sh\" >> \"\$PG_CONF\"
    "
    echo "  SET \${KEY} = \${VAL}"
  }

  apply_setting "max_connections"              "\$REC_MAX_CONN"
  apply_setting "shared_buffers"              "\$REC_SHARED_BUF"
  apply_setting "work_mem"                    "\$REC_WORK_MEM"
  apply_setting "maintenance_work_mem"        "\$REC_MAINT_MEM"
  apply_setting "effective_cache_size"        "\$REC_EFF_CACHE"
  apply_setting "wal_buffers"                 "\$REC_WAL_BUFS"
  apply_setting "checkpoint_completion_target" "0.9"

  echo ""
  echo "  Reloading PostgreSQL config (no restart needed for most settings)..."
  docker exec "\$PG_CONTAINER" psql -U "\$PGUSER" -d "\$PGDB" -c "SELECT pg_reload_conf();" 2>/dev/null | tr -d ' '

  # max_connections requires a restart — check if it changed
  NEW_MAX=\$(docker exec "\$PG_CONTAINER" psql -U "\$PGUSER" -d "\$PGDB" -t -c "SHOW max_connections;" 2>/dev/null | tr -d ' \n')
  if [ "\$NEW_MAX" != "\$MAX_CONN" ]; then
    echo ""
    echo "  NOTICE: max_connections changed \$MAX_CONN → \$NEW_MAX"
    echo "          This requires a PostgreSQL RESTART (not just reload)."
    echo "          Run: docker restart \$PG_CONTAINER"
    echo "          (plan a brief downtime window)"
  else
    echo "  max_connections unchanged — no restart needed."
  fi

  echo ""
  echo "  Verifying applied settings:"
  for KEY in max_connections shared_buffers work_mem effective_cache_size wal_buffers; do
    VAL=\$(docker exec "\$PG_CONTAINER" psql -U "\$PGUSER" -d "\$PGDB" -t -c "SHOW \$KEY;" 2>/dev/null | tr -d ' \n')
    printf "    %-35s %s\n" "\$KEY" "\$VAL"
  done

else
  echo "[ 6/6 ] Dry-run — no changes made."
  echo "        To apply: re-run with --apply flag"
  echo "        From Mac:   EC2_IP=${EC2_IP} bash pg-check-tune.sh --apply"
  echo "        On EC2:     bash pg-check-tune.sh --local --apply"
fi

echo ""
echo "\$SEP"
echo "  Connection pool advice for the application layer"
echo "\$SEP"
echo ""
echo "  If your agents use direct psycopg2 connections (no pooler):"
echo "    - Set pool_size = 5-10 per agent process"
echo "    - Set max_overflow = 5 (SQLAlchemy) or pool_maxconn = 15"
echo "    - Total = agents * (pool_size + max_overflow) must be < max_connections"
echo ""
echo "  For \${TARGET} concurrent users across N agents:"
echo "    Example with 4 agents: each agent pool_size = \$(echo "\$TARGET / 4" | bc)"
echo "    Total connections held = ~\$(echo "\$TARGET" | bc) (leaving headroom in max_connections=\$REC_MAX_CONN)"
echo ""
echo "  Consider PgBouncer (transaction pooling) if you exceed 100 connections:"
echo "    - Multiplexes many app connections onto a small number of server connections"
echo "    - Especially valuable when most connections are 'idle in transaction'"
echo ""
SSHEOF
