#!/bin/bash
################################################################################
# Quick Date Verification Script
# Usage: ./quick_verify_date.sh [YYYY-MM-DD]
# Example: ./quick_verify_date.sh 2024-11-09
################################################################################

set -e

DATE=${1:-$(date -d "yesterday" +%Y-%m-%d)}

echo "============================================================"
echo "🔍 QUICK VERIFICATION FOR: $DATE"
echo "============================================================"
echo ""
echo "Current time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Function to run SQL query
run_query() {
    local db=$1
    local query=$2

    python3 - <<EOF
import sys
import os
sys.path.insert(0, '/home/user/nba-mcp-synthesis')

from mcp_server.unified_secrets_manager import load_secrets_hierarchical, get_database_config
import psycopg2

# Load credentials
load_secrets_hierarchical('nba-mcp-synthesis', 'NBA', 'production')
config = get_database_config()

# Override database
config['database'] = '$db'

try:
    conn = psycopg2.connect(**config)
    cur = conn.cursor()
    cur.execute("""$query""")

    results = cur.fetchall()
    for row in results:
        print('\t'.join(map(str, row)))

    cur.close()
    conn.close()
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)
EOF
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 DATABASE: nba_simulator"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check espn_games
echo ""
echo "📋 espn.espn_games:"
run_query "nba_simulator" "
SELECT COUNT(*) as games
FROM espn.espn_games
WHERE game_date = '$DATE';
" || echo "  ❌ Query failed"

# Check espn_plays
echo ""
echo "🎮 espn.espn_plays:"
run_query "nba_simulator" "
SELECT COUNT(*) as plays
FROM espn.espn_plays
WHERE game_id IN (SELECT game_id FROM espn.espn_games WHERE game_date = '$DATE');
" || echo "  ❌ Query failed"

# Check espn_team_stats
echo ""
echo "📈 espn.espn_team_stats:"
run_query "nba_simulator" "
SELECT COUNT(*) as team_stats
FROM espn.espn_team_stats
WHERE game_id IN (SELECT game_id FROM espn.espn_games WHERE game_date = '$DATE');
" || echo "  ❌ Query failed"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 DATABASE: nba_mcp_synthesis"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check schedule_espn_nba
echo ""
echo "📅 espn_raw.schedule_espn_nba:"
run_query "nba_mcp_synthesis" "
SELECT COUNT(*) as schedule_games
FROM espn_raw.schedule_espn_nba
WHERE game_date = '$DATE';
" || echo "  ❌ Query failed"

# Check play_by_play_espn_nba
echo ""
echo "🎯 espn_raw.play_by_play_espn_nba:"
run_query "nba_mcp_synthesis" "
SELECT COUNT(*) as pbp_plays
FROM espn_raw.play_by_play_espn_nba
WHERE game_id IN (SELECT game_id FROM espn_raw.schedule_espn_nba WHERE game_date = '$DATE');
" || echo "  ❌ Query failed"

# Check team_box_espn_nba
echo ""
echo "📊 espn_raw.team_box_espn_nba:"
run_query "nba_mcp_synthesis" "
SELECT COUNT(*) as team_box_stats
FROM espn_raw.team_box_espn_nba
WHERE game_id IN (SELECT game_id FROM espn_raw.schedule_espn_nba WHERE game_date = '$DATE');
" || echo "  ❌ Query failed"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 SUMMARY FOR $DATE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Expected for NBA regular season day:"
echo "  • Games:      ~8-15 games"
echo "  • Plays:      ~30,000-60,000 total"
echo "  • Team Stats: 2x games (20-30 records)"
echo ""
echo "✅ If all counts are > 0, data collection succeeded!"
echo "⚠️  If any count is 0, check logs and run manual collection."
echo ""
echo "============================================================"
