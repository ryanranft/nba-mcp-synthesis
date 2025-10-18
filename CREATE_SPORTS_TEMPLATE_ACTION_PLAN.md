# Action Plan: Create Sports MCP Template

**Goal:** Create universal Sports MCP Template with NCAA Men's Basketball as first instance
**Timeline:** 2-3 days
**Outcome:** Template + NCAA MBB + NCAA WBB ready to deploy

---

## 📋 Overview

We'll create a **NEW repository** called `sports-mcp-template` that's separate from `nba-mcp-synthesis`. The NBA MCP becomes the first "production" instance, and the template enables rapid creation of new sports.

### Strategy

```
Day 1: Extract & Generalize
├── Create template repository
├── Copy universal components from NBA MCP
├── Build configuration system
└── Create basketball module

Day 2: NCAA Implementation
├── Configure NCAA Men's Basketball
├── Configure NCAA Women's Basketball
├── Test both instances
└── Document setup process

Day 3: Polish & Deploy
├── Write comprehensive docs
├── Create setup scripts
├── Deploy both NCAA instances
└── Validate everything works
```

---

## 🎯 Day 1: Create Template Foundation

### Task 1.1: Create New Repository (15 min)

```bash
# In parent directory of nba-mcp-synthesis
cd ~/repos  # or wherever you keep repos

# Create new repository
mkdir sports-mcp-template
cd sports-mcp-template

# Initialize
git init
python3 -m venv venv
source venv/bin/activate

# Create directory structure
mkdir -p config/sports config/analytics
mkdir -p mcp_server/{core,sports/{basketball,football,baseball,hockey},tools,ml}
mkdir -p scripts tests docs/examples
touch README.md TEMPLATE_USAGE_GUIDE.md SPORT_SETUP_GUIDE.md
```

### Task 1.2: Copy Universal Components (30 min)

```bash
# Copy reusable tools from NBA MCP (adjust paths as needed)
NBA_MCP=../nba-mcp-synthesis

# Core utilities (universal across sports)
cp $NBA_MCP/mcp_server/tools/math_helper.py mcp_server/core/
cp $NBA_MCP/mcp_server/tools/stats_helper.py mcp_server/core/
cp $NBA_MCP/mcp_server/tools/correlation_helper.py mcp_server/core/

# Machine learning tools (universal)
cp $NBA_MCP/mcp_server/tools/ml_*.py mcp_server/ml/
cp $NBA_MCP/mcp_server/tools/clustering_helper.py mcp_server/ml/
cp $NBA_MCP/mcp_server/tools/classification_helper.py mcp_server/ml/
cp $NBA_MCP/mcp_server/tools/anomaly_helper.py mcp_server/ml/
cp $NBA_MCP/mcp_server/tools/evaluation_helper.py mcp_server/ml/

# Database connectivity (universal)
cp $NBA_MCP/mcp_server/connectors/rds_connector.py mcp_server/core/db_connector.py
cp $NBA_MCP/mcp_server/connectors/s3_connector.py mcp_server/core/s3_connector.py

# Parameter models (we'll adapt these)
cp $NBA_MCP/mcp_server/tools/params.py mcp_server/params_template.py

# Response models
cp $NBA_MCP/mcp_server/responses.py mcp_server/
```

### Task 1.3: Create Base Sport Class (45 min)

Create the foundational abstraction:

```bash
# Create base sport class
cat > mcp_server/sports/base_sport.py << 'PYTHON'
# See SPORTS_TEMPLATE_QUICKSTART.md for full code
# (Copy the BaseSport class from that document)
PYTHON

# Create sport module __init__.py
cat > mcp_server/sports/__init__.py << 'PYTHON'
from .base_sport import BaseSport
from .basketball import Basketball

__all__ = ['BaseSport', 'Basketball']
PYTHON
```

### Task 1.4: Extract Basketball Module from NBA MCP (60 min)

```bash
# Create basketball module directory
mkdir -p mcp_server/sports/basketball

# Extract NBA-specific code into basketball module
cat > mcp_server/sports/basketball/__init__.py << 'PYTHON'
from ..base_sport import BaseSport
# Copy basketball metrics from nba_metrics_helper.py
# (All PER, TS%, eFG%, Four Factors, etc.)
PYTHON

# Copy NBA metrics to basketball module
cp $NBA_MCP/mcp_server/tools/nba_metrics_helper.py \
   mcp_server/sports/basketball/metrics.py

# Refactor to work with base class
# (This requires some manual editing)
```

### Task 1.5: Create Configuration System (45 min)

```bash
# Create config loader
cat > mcp_server/config_loader.py << 'PYTHON'
# See SPORTS_TEMPLATE_QUICKSTART.md for SportConfigLoader code
PYTHON

# Create template config
cat > config/sports/template.yaml << 'YAML'
sport:
  name: "SPORT_NAME"
  short_name: "sport_abbr"
  category: "CATEGORY"  # basketball, football, baseball, hockey, soccer
  league: "LEAGUE_NAME"

data_sources:
  database:
    type: "postgresql"
    host: "${DB_HOST}"
    port: 5432
    database: "${DB_NAME}"
    username: "${DB_USER}"
    password: "${DB_PASSWORD}"

positions: []
statistics: []
metrics: []
YAML
```

### Task 1.6: Create Main Server (30 min)

```bash
# Create FastMCP server
cat > mcp_server/server.py << 'PYTHON'
# See SPORTS_TEMPLATE_QUICKSTART.md for server code
PYTHON

# Create requirements.txt
cat > requirements.txt << 'TXT'
fastmcp>=1.0.0
pydantic>=2.0.0
pyyaml>=6.0
psycopg2-binary>=2.9.0
boto3>=1.26.0
pandas>=2.0.0
numpy>=1.24.0
sympy>=1.12
TXT

# Install dependencies
pip install -r requirements.txt
```

---

## 🎯 Day 2: NCAA Implementations

### Task 2.1: Create NCAA Men's Basketball Config (30 min)

```bash
# Create NCAA MBB configuration
cat > config/sports/ncaa_mens_basketball.yaml << 'YAML'
sport:
  name: "NCAA Men's Basketball"
  short_name: "ncaa_mbb"
  category: "basketball"
  league: "NCAA"
  division: "I"
  gender: "male"
  season_type: "college"

data_sources:
  database:
    type: "postgresql"
    host: "${NCAA_MBB_DB_HOST}"
    port: 5432
    database: "ncaa_basketball"
    username: "${NCAA_MBB_DB_USER}"
    password: "${NCAA_MBB_DB_PASSWORD}"
    tables:
      games: "games"
      players: "players"
      teams: "teams"
      player_stats: "player_game_stats"
      team_stats: "team_game_stats"
      conferences: "conferences"
      tournaments: "tournaments"

  s3:
    bucket: "${NCAA_MBB_S3_BUCKET}"
    region: "us-east-1"
    prefix: "ncaa-mbb/"

rules:
  game_length: 40  # minutes
  periods: 2
  overtime_length: 5
  roster_size: 15
  starting_lineup: 5
  fouls_to_disqualify: 5
  shot_clock: 30
  three_point_line: 22.15  # feet

positions:
  - name: "Point Guard"
    abbreviation: "PG"
    number: 1
    description: "Primary ball handler and playmaker"
  - name: "Shooting Guard"
    abbreviation: "SG"
    number: 2
    description: "Perimeter scorer"
  - name: "Small Forward"
    abbreviation: "SF"
    number: 3
    description: "Versatile wing player"
  - name: "Power Forward"
    abbreviation: "PF"
    number: 4
    description: "Inside-outside big"
  - name: "Center"
    abbreviation: "C"
    number: 5
    description: "Primary interior presence"

statistics:
  basic:
    - points
    - rebounds
    - assists
    - steals
    - blocks
    - turnovers
    - fouls
    - minutes

  shooting:
    - field_goals_made
    - field_goals_attempted
    - three_pointers_made
    - three_pointers_attempted
    - free_throws_made
    - free_throws_attempted

  advanced:
    - offensive_rebounds
    - defensive_rebounds
    - plus_minus
    - usage_rate
    - true_shooting_percentage

metrics:
  player:
    - player_efficiency_rating
    - true_shooting_percentage
    - effective_field_goal_percentage
    - usage_rate
    - offensive_rating
    - defensive_rating
    - win_shares
    - box_plus_minus
    - assist_percentage
    - steal_percentage
    - block_percentage
    - turnover_percentage
    - rebound_percentage

  team:
    - offensive_efficiency
    - defensive_efficiency
    - pace
    - effective_field_goal_percentage
    - turnover_percentage
    - offensive_rebound_percentage
    - free_throw_rate
    - four_factors

analytics:
  clustering:
    enabled: true
    features:
      - points_per_game
      - rebounds_per_game
      - assists_per_game
      - shooting_percentage
      - three_point_percentage
    methods: ["kmeans", "hierarchical"]
    default_clusters: 5

  classification:
    enabled: true
    models:
      all_american:
        target: "all_american_status"
        features: ["points", "rebounds", "assists", "shooting_pct"]
      tournament_team:
        target: "tournament_selection"
        features: ["wins", "losses", "rpi", "sos"]

  prediction:
    enabled: true
    targets:
      - tournament_seed
      - conference_finish
      - player_draft_round

api:
  base_path: "/api/v1/ncaa-mbb"
  version: "1.0"
  rate_limit: 1000  # requests per hour

mcp_tools:
  enabled:
    - query_players
    - query_teams
    - query_games
    - analyze_player
    - compare_players
    - team_statistics
    - predict_tournament
    - calculate_efficiency_rating
    - cluster_players
    - generate_scouting_report
    - calculate_team_four_factors
    - tournament_bracket_analysis
YAML

# Create environment template
cat > .env.ncaa_mbb.example << 'ENV'
# NCAA Men's Basketball Database
NCAA_MBB_DB_HOST=your-ncaa-db.rds.amazonaws.com
NCAA_MBB_DB_USER=your_username
NCAA_MBB_DB_PASSWORD=your_password
NCAA_MBB_DB_PORT=5432

# NCAA Men's Basketball S3
NCAA_MBB_S3_BUCKET=ncaa-basketball-data
NCAA_MBB_AWS_REGION=us-east-1

# API Keys (if needed)
NCAA_MBB_API_KEY=your_api_key

# MCP Settings
SPORT=ncaa_mens_basketball
MCP_PORT=5000
ENV
```

### Task 2.2: Create NCAA Women's Basketball Config (5 min)

```bash
# Copy and modify for women's basketball
cp config/sports/ncaa_mens_basketball.yaml \
   config/sports/ncaa_womens_basketball.yaml

# Update specific fields
sed -i '' 's/Men'"'"'s/Women'"'"'s/g' config/sports/ncaa_womens_basketball.yaml
sed -i '' 's/ncaa_mbb/ncaa_wbb/g' config/sports/ncaa_womens_basketball.yaml
sed -i '' 's/male/female/g' config/sports/ncaa_womens_basketball.yaml

# Women's basketball has different three-point line
sed -i '' 's/22.15/20.75/g' config/sports/ncaa_womens_basketball.yaml

# Create environment template
cp .env.ncaa_mbb.example .env.ncaa_wbb.example
sed -i '' 's/MBB/WBB/g' .env.ncaa_wbb.example
sed -i '' 's/mens/womens/g' .env.ncaa_wbb.example
```

### Task 2.3: Test Both Configurations (30 min)

```bash
# Create test script
cat > scripts/test_sport_config.py << 'PYTHON'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.config_loader import SportConfigLoader

def test_sport(sport_name: str):
    """Test loading a sport configuration."""
    print(f"\nTesting {sport_name}...")

    try:
        loader = SportConfigLoader()
        sport = loader.load_sport(sport_name)

        print(f"✅ Loaded: {sport.name}")
        print(f"   Category: {sport.category}")
        print(f"   Positions: {len(sport.get_positions())}")
        print(f"   Metrics: {len(sport.get_metrics())}")

        # Test PER calculation
        test_stats = {
            'points': 20,
            'rebounds': 8,
            'assists': 5,
            'steals': 2,
            'blocks': 1,
            'turnovers': 3,
            'minutes': 30
        }
        per = sport.calculate_player_efficiency(test_stats)
        print(f"   Test PER: {per:.2f}")

        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    sport_name = sys.argv[1] if len(sys.argv) > 1 else "ncaa_mens_basketball"
    success = test_sport(sport_name)
    sys.exit(0 if success else 1)
PYTHON

# Test both sports
python scripts/test_sport_config.py ncaa_mens_basketball
python scripts/test_sport_config.py ncaa_womens_basketball
```

### Task 2.4: Create MCP Tools for NCAA (60 min)

```bash
# Create NCAA-specific MCP tools
cat > mcp_server/tools/ncaa_tools.py << 'PYTHON'
from fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional, List
import os

# This will be imported by main server
# Tools are dynamically registered based on active sport

class TournamentPredictionParams(BaseModel):
    team_name: str = Field(..., description="Team name")
    wins: int = Field(..., ge=0, le=40)
    losses: int = Field(..., ge=0, le=40)
    rpi: float = Field(..., ge=0, le=1, description="RPI rating")
    strength_of_schedule: float = Field(..., ge=0, le=1)

class ScoutingReportParams(BaseModel):
    player_name: str = Field(..., description="Player name")
    season: str = Field(..., description="Season (e.g., '2023-24')")
    include_comparisons: bool = Field(False)

# Tools will be added to main server
PYTHON
```

---

## 🎯 Day 3: Documentation & Deployment

### Task 3.1: Write Documentation (90 min)

```bash
# Main README
cat > README.md << 'MD'
# Sports MCP Template

Universal MCP server template for sports analytics. Easily adaptable to any sport.

## Quick Start

### Install
```bash
git clone https://github.com/your-org/sports-mcp-template
cd sports-mcp-template
pip install -r requirements.txt
```

### Run NCAA Men's Basketball
```bash
export SPORT=ncaa_mens_basketball
export NCAA_MBB_DB_HOST=your-db-host
python -m mcp_server.server
```

## Supported Sports

- ✅ NCAA Men's Basketball
- ✅ NCAA Women's Basketball
- 🚧 NBA (coming soon)
- 🚧 NFL (coming soon)

## Documentation

- [Template Usage Guide](TEMPLATE_USAGE_GUIDE.md)
- [Adding New Sports](SPORT_SETUP_GUIDE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [API Reference](docs/API_REFERENCE.md)

## Adding a New Sport

See [SPORT_SETUP_GUIDE.md](SPORT_SETUP_GUIDE.md) for step-by-step instructions.

Basically:
1. Copy `config/sports/template.yaml`
2. Fill in sport details
3. Run `python scripts/test_sport_config.py your_sport`
4. Deploy!

## License

MIT
MD

# Create comprehensive guides
# (Copy content from SPORTS_MCP_TEMPLATE_DESIGN.md and SPORTS_TEMPLATE_QUICKSTART.md)
```

### Task 3.2: Create Setup Scripts (45 min)

```bash
# Create CLI tool for new sports
cat > scripts/create_new_sport.py << 'PYTHON'
#!/usr/bin/env python3
"""CLI tool to create a new sport configuration."""

import argparse
import yaml
from pathlib import Path
import shutil

def create_sport(name: str, short_name: str, category: str,
                copy_from: str = None):
    """Create a new sport configuration."""
    config_dir = Path("config/sports")
    template = config_dir / "template.yaml"

    if copy_from:
        source = config_dir / f"{copy_from}.yaml"
        if not source.exists():
            print(f"Error: Source config not found: {copy_from}")
            return False
        template = source

    # Load template
    with open(template) as f:
        config = yaml.safe_load(f)

    # Update config
    config['sport']['name'] = name
    config['sport']['short_name'] = short_name
    config['sport']['category'] = category

    # Write new config
    output = config_dir / f"{short_name}.yaml"
    with open(output, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

    print(f"✅ Created: {output}")
    print(f"\nNext steps:")
    print(f"1. Edit {output} to add sport-specific details")
    print(f"2. Create .env.{short_name}")
    print(f"3. Test: python scripts/test_sport_config.py {short_name}")
    print(f"4. Deploy: export SPORT={short_name} && python -m mcp_server.server")

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create new sport config")
    parser.add_argument("--name", required=True, help="Full sport name")
    parser.add_argument("--short-name", required=True, help="Short name/abbreviation")
    parser.add_argument("--category", required=True,
                       choices=["basketball", "football", "baseball", "hockey", "soccer"])
    parser.add_argument("--copy-from", help="Copy from existing sport config")

    args = parser.parse_args()
    create_sport(args.name, args.short_name, args.category, args.copy_from)
PYTHON

chmod +x scripts/create_new_sport.py
```

### Task 3.3: Deploy NCAA Instances (30 min)

```bash
# Create deployment script
cat > scripts/deploy_sport.py << 'PYTHON'
#!/usr/bin/env python3
"""Deploy a sport-specific MCP server instance."""

import argparse
import os
import subprocess
from pathlib import Path

def deploy(sport: str, port: int = 5000, production: bool = False):
    """Deploy MCP server for specified sport."""

    # Validate sport exists
    config_file = Path(f"config/sports/{sport}.yaml")
    if not config_file.exists():
        print(f"Error: Sport config not found: {sport}")
        return False

    # Set environment
    os.environ['SPORT'] = sport
    os.environ['MCP_PORT'] = str(port)

    # Load sport-specific env vars
    env_file = Path(f".env.{sport}")
    if env_file.exists():
        print(f"Loading environment from {env_file}")
        # Load env vars from file
        # (implement env file loading)

    # Run server
    print(f"🚀 Deploying {sport} on port {port}...")

    if production:
        # Production deployment with gunicorn
        cmd = [
            "gunicorn",
            "mcp_server.server:app",
            "--bind", f"0.0.0.0:{port}",
            "--workers", "4",
            "--timeout", "120"
        ]
    else:
        # Development deployment
        cmd = ["python", "-m", "mcp_server.server"]

    subprocess.run(cmd)

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("sport", help="Sport name (e.g., ncaa_mens_basketball)")
    parser.add_argument("--port", type=int, default=5000, help="Port number")
    parser.add_argument("--production", action="store_true", help="Production mode")

    args = parser.parse_args()
    deploy(args.sport, args.port, args.production)
PYTHON

chmod +x scripts/deploy_sport.py
```

---

## ✅ Validation Checklist

### Day 1 Completion
- [ ] Repository created and initialized
- [ ] Universal components copied from NBA MCP
- [ ] Base sport class created
- [ ] Basketball module extracted and working
- [ ] Configuration system functional
- [ ] Main server runs successfully

### Day 2 Completion
- [ ] NCAA Men's Basketball config created
- [ ] NCAA Women's Basketball config created
- [ ] Both configs load successfully
- [ ] PER calculation works for both
- [ ] Database connection templates created
- [ ] MCP tools accessible

### Day 3 Completion
- [ ] README.md comprehensive
- [ ] TEMPLATE_USAGE_GUIDE.md complete
- [ ] SPORT_SETUP_GUIDE.md written
- [ ] Setup scripts working
- [ ] Test scripts passing
- [ ] Both NCAA instances deployable

---

## 🎯 Success Criteria

### Functional Requirements
- ✅ Template loads any sport config
- ✅ Basketball metrics work for NCAA MBB and WBB
- ✅ Can switch sports by changing environment variable
- ✅ All universal tools (ML, stats) work for both sports
- ✅ Database connectivity functional
- ✅ MCP server responsive

### Code Quality
- ✅ Modular architecture
- ✅ Type hints everywhere
- ✅ Comprehensive error handling
- ✅ Clean separation of concerns
- ✅ Well-documented code

### Documentation
- ✅ Clear README
- ✅ Step-by-step setup guides
- ✅ API documentation
- ✅ Examples for both sports
- ✅ Troubleshooting guide

---

## 📊 Post-Launch (Week 1)

### Tasks
1. Add NBA configuration (reuse basketball module)
2. Create NFL module and configuration
3. Write blog post about template
4. Create demo video
5. Gather community feedback

### Metrics to Track
- Configuration load time
- MCP tool response time
- Code reuse percentage
- Time to add new sport
- Community adoption

---

## 🚀 Ready to Start?

```bash
# Clone this checklist and start
cd ~/repos
mkdir sports-mcp-template
cd sports-mcp-template

# Follow Day 1 tasks above
# Then Day 2, then Day 3

# By end of Day 3, you'll have:
# - Universal template ✅
# - NCAA Men's Basketball ✅
# - NCAA Women's Basketball ✅
# - Ready to add NFL, MLB, NHL ✅
```

**Let's build it! 🏀🏈⚾🏒**


