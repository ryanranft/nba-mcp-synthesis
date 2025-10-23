# Sports MCP Template - Universal Design

**Version:** 1.0
**Created:** October 18, 2025
**Purpose:** Universal MCP template adaptable to any sport

---

## 🎯 Overview

The **Sports MCP Template** is a modular, configurable MCP server that can be adapted to any sport with minimal code changes. Instead of building separate MCP servers for each sport, we create one flexible template that sports-specific configurations plug into.

---

## 🏗️ Architecture

### Core Concept

```
Sports MCP Template (Universal Core)
├── Configurable Sport Definitions
├── Generic Analytics Engine
├── Pluggable Data Connectors
└── Sport-Specific Modules

Examples:
├── NCAA Men's Basketball → Configuration + Basketball Module
├── NCAA Women's Basketball → Same config, different data source
├── NBA → Configuration + NBA Module
├── NFL → Configuration + Football Module
├── MLB → Configuration + Baseball Module
└── NHL → Configuration + Hockey Module
```

### Design Principles

1. **Configuration Over Code**: Define sport characteristics in config files
2. **Plug-and-Play Modules**: Sport-specific logic in separate modules
3. **Shared Analytics**: Common statistical operations across all sports
4. **Flexible Data Sources**: Support multiple database/API backends
5. **Easy Deployment**: One-command setup for new sports

---

## 📁 Template Repository Structure

```
sports-mcp-template/
├── README.md
├── TEMPLATE_USAGE_GUIDE.md
├── SPORT_SETUP_GUIDE.md
├── requirements.txt
├── .env.example
│
├── config/
│   ├── sports/
│   │   ├── ncaa_mens_basketball.yaml      # Example sport config
│   │   ├── ncaa_womens_basketball.yaml
│   │   ├── nba.yaml
│   │   ├── nfl.yaml
│   │   ├── mlb.yaml
│   │   ├── nhl.yaml
│   │   └── template.yaml                   # Empty template
│   │
│   └── analytics/
│       ├── efficiency_metrics.yaml
│       ├── shooting_metrics.yaml
│       ├── defensive_metrics.yaml
│       └── team_metrics.yaml
│
├── mcp_server/
│   ├── __init__.py
│   ├── server.py                          # Main MCP server
│   ├── config_loader.py                   # Load sport configs
│   │
│   ├── core/                              # Universal core
│   │   ├── __init__.py
│   │   ├── base_metrics.py                # Common metrics
│   │   ├── statistical_engine.py          # Stats operations
│   │   ├── data_connector.py              # Generic DB connector
│   │   └── formula_engine.py              # Formula calculations
│   │
│   ├── sports/                            # Sport-specific modules
│   │   ├── __init__.py
│   │   ├── base_sport.py                  # Base sport class
│   │   ├── basketball/
│   │   │   ├── __init__.py
│   │   │   ├── metrics.py                 # Basketball metrics
│   │   │   ├── rules.py                   # Basketball rules
│   │   │   └── positions.py               # Position definitions
│   │   ├── football/
│   │   │   ├── __init__.py
│   │   │   ├── metrics.py
│   │   │   ├── rules.py
│   │   │   └── positions.py
│   │   └── baseball/
│   │       ├── __init__.py
│   │       ├── metrics.py
│   │       ├── rules.py
│   │       └── positions.py
│   │
│   ├── tools/                             # MCP tools
│   │   ├── __init__.py
│   │   ├── query_tools.py                 # Database queries
│   │   ├── analytics_tools.py             # Analytics operations
│   │   ├── player_tools.py                # Player analysis
│   │   ├── team_tools.py                  # Team analysis
│   │   ├── game_tools.py                  # Game analysis
│   │   └── prediction_tools.py            # Predictions
│   │
│   └── ml/                                # Machine Learning
│       ├── __init__.py
│       ├── clustering.py
│       ├── classification.py
│       ├── regression.py
│       └── evaluation.py
│
├── scripts/
│   ├── create_new_sport.py                # CLI to create new sport
│   ├── test_sport_config.py               # Test sport config
│   ├── generate_tools.py                  # Auto-generate MCP tools
│   └── deploy_sport.py                    # Deploy for specific sport
│
├── tests/
│   ├── test_core.py
│   ├── test_basketball.py
│   ├── test_football.py
│   └── test_baseball.py
│
└── docs/
    ├── ARCHITECTURE.md
    ├── ADDING_NEW_SPORT.md
    ├── CONFIGURATION_GUIDE.md
    ├── API_REFERENCE.md
    └── examples/
        ├── ncaa_basketball_example.md
        ├── nfl_example.md
        └── mlb_example.md
```

---

## ⚙️ Sport Configuration Format

### Example: `config/sports/ncaa_mens_basketball.yaml`

```yaml
# Sport Definition
sport:
  name: "NCAA Men's Basketball"
  short_name: "ncaa_mbb"
  category: "basketball"
  league: "NCAA"
  gender: "male"

# Data Sources
data_sources:
  primary:
    type: "postgresql"
    host: "${DB_HOST}"
    database: "ncaa_basketball"
    tables:
      games: "games"
      players: "players"
      teams: "teams"
      stats: "player_game_stats"

  secondary:
    type: "s3"
    bucket: "ncaa-basketball-data"
    region: "us-east-1"

# Sport Rules
rules:
  game_length: 40  # minutes
  periods: 2
  overtime_length: 5
  roster_size: 15
  starting_lineup: 5
  fouls_to_disqualify: 5

# Positions
positions:
  - name: "Point Guard"
    abbreviation: "PG"
    number: 1
  - name: "Shooting Guard"
    abbreviation: "SG"
    number: 2
  - name: "Small Forward"
    abbreviation: "SF"
    number: 3
  - name: "Power Forward"
    abbreviation: "PF"
    number: 4
  - name: "Center"
    abbreviation: "C"
    number: 5

# Statistics Tracked
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
    - usage_rate
    - true_shooting_percentage
    - effective_field_goal_percentage

# Metrics to Calculate
metrics:
  player:
    - player_efficiency_rating
    - true_shooting_percentage
    - usage_rate
    - offensive_rating
    - defensive_rating
    - win_shares
    - box_plus_minus

  team:
    - offensive_efficiency
    - defensive_efficiency
    - pace
    - four_factors
    - net_rating

# Analytics Models
analytics:
  clustering:
    features: ["points_per_game", "rebounds_per_game", "assists_per_game"]
    methods: ["kmeans", "hierarchical"]

  classification:
    target: "all_american_status"
    features: ["points", "rebounds", "assists", "shooting_pct"]

  prediction:
    targets: ["tournament_bid", "conference_champion"]
    features: ["wins", "losses", "strength_of_schedule"]

# API Endpoints
api:
  base_path: "/api/v1/ncaa-mbb"
  rate_limit: 1000  # requests per hour

# MCP Tools to Generate
mcp_tools:
  - query_players
  - query_teams
  - query_games
  - analyze_player_performance
  - compare_players
  - predict_tournament_bid
  - calculate_team_efficiency
  - cluster_players
  - generate_scouting_report
```

---

## 🔧 Core Components

### 1. Base Sport Class (`mcp_server/sports/base_sport.py`)

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import yaml

class BaseSport(ABC):
    """Base class for all sports."""

    def __init__(self, config_path: str):
        """Initialize sport with configuration."""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.name = self.config['sport']['name']
        self.short_name = self.config['sport']['short_name']
        self.positions = self.config['positions']
        self.statistics = self.config['statistics']
        self.rules = self.config['rules']

    @abstractmethod
    def calculate_player_efficiency(self, stats: Dict[str, float]) -> float:
        """Calculate sport-specific player efficiency."""
        pass

    @abstractmethod
    def validate_statistics(self, stats: Dict[str, Any]) -> bool:
        """Validate statistics for this sport."""
        pass

    def get_positions(self) -> List[str]:
        """Get list of positions for this sport."""
        return [p['abbreviation'] for p in self.positions]

    def get_required_stats(self) -> List[str]:
        """Get list of required statistics."""
        return (self.statistics['basic'] +
                self.statistics['shooting'] +
                self.statistics.get('advanced', []))
```

### 2. Basketball Module (`mcp_server/sports/basketball/metrics.py`)

```python
from typing import Dict
from ..base_sport import BaseSport

class Basketball(BaseSport):
    """Basketball-specific implementation."""

    def calculate_player_efficiency(self, stats: Dict[str, float]) -> float:
        """
        Calculate PER (Player Efficiency Rating) for basketball.
        Formula: (PTS + REB + AST + STL + BLK - TOV) / MIN
        """
        pts = stats.get('points', 0)
        reb = stats.get('rebounds', 0)
        ast = stats.get('assists', 0)
        stl = stats.get('steals', 0)
        blk = stats.get('blocks', 0)
        tov = stats.get('turnovers', 0)
        min = stats.get('minutes', 1)

        if min == 0:
            return 0.0

        return (pts + reb + ast + stl + blk - tov) / min

    def calculate_true_shooting(self, stats: Dict[str, float]) -> float:
        """Calculate True Shooting Percentage."""
        pts = stats.get('points', 0)
        fga = stats.get('field_goals_attempted', 0)
        fta = stats.get('free_throws_attempted', 0)

        if fga == 0 and fta == 0:
            return 0.0

        return pts / (2 * (fga + 0.44 * fta))

    def validate_statistics(self, stats: Dict[str, Any]) -> bool:
        """Validate basketball statistics."""
        required = ['points', 'rebounds', 'assists', 'minutes']
        return all(stat in stats for stat in required)
```

### 3. Config Loader (`mcp_server/config_loader.py`)

```python
import yaml
from pathlib import Path
from typing import Dict, Any

class SportConfigLoader:
    """Load and manage sport configurations."""

    def __init__(self, config_dir: str = "config/sports"):
        self.config_dir = Path(config_dir)
        self._configs = {}

    def load_sport(self, sport_name: str) -> Dict[str, Any]:
        """Load configuration for a specific sport."""
        config_file = self.config_dir / f"{sport_name}.yaml"

        if not config_file.exists():
            raise FileNotFoundError(f"Config not found: {config_file}")

        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)

        self._configs[sport_name] = config
        return config

    def list_available_sports(self) -> list:
        """List all available sport configurations."""
        return [f.stem for f in self.config_dir.glob("*.yaml")
                if f.stem != "template"]

    def get_sport_module(self, sport_name: str):
        """Dynamically import sport-specific module."""
        config = self.load_sport(sport_name)
        category = config['sport']['category']

        if category == 'basketball':
            from .sports.basketball.metrics import Basketball
            return Basketball(str(self.config_dir / f"{sport_name}.yaml"))
        elif category == 'football':
            from .sports.football.metrics import Football
            return Football(str(self.config_dir / f"{sport_name}.yaml"))
        elif category == 'baseball':
            from .sports.baseball.metrics import Baseball
            return Baseball(str(self.config_dir / f"{sport_name}.yaml"))
        else:
            raise ValueError(f"Unknown sport category: {category}")
```

---

## 🚀 Creating a New Sport Instance

### Using the CLI Tool

```bash
# Create new sport from template
python scripts/create_new_sport.py \
  --name "NCAA Women's Basketball" \
  --short-name "ncaa_wbb" \
  --category "basketball" \
  --database "ncaa_womens_basketball" \
  --copy-from "ncaa_mens_basketball"

# This generates:
# - config/sports/ncaa_wbb.yaml
# - .env.ncaa_wbb
# - Customized MCP server instance
```

### Manual Setup

```bash
# 1. Copy template config
cp config/sports/template.yaml config/sports/my_sport.yaml

# 2. Edit configuration
vim config/sports/my_sport.yaml

# 3. Set up environment
cp .env.example .env.my_sport
vim .env.my_sport

# 4. Test configuration
python scripts/test_sport_config.py my_sport

# 5. Deploy
python scripts/deploy_sport.py my_sport
```

---

## 🔌 MCP Tools Generation

### Auto-Generated Tools

The template automatically generates MCP tools based on the sport configuration:

```python
# Example: Auto-generated tool for NCAA Men's Basketball

@mcp.tool()
async def ncaa_mbb_query_players(
    params: PlayerQueryParams
) -> QueryResult:
    """Query NCAA Men's Basketball players."""
    sport = config_loader.get_sport_module('ncaa_mens_basketball')

    # Use generic query logic with sport-specific config
    return await generic_query_players(sport, params)

@mcp.tool()
async def ncaa_mbb_calculate_efficiency(
    params: PlayerStatsParams
) -> MetricResult:
    """Calculate player efficiency for NCAA Men's Basketball."""
    sport = config_loader.get_sport_module('ncaa_mens_basketball')

    efficiency = sport.calculate_player_efficiency(params.stats)
    return MetricResult(value=efficiency, metric="PER")
```

---

## 🎨 Customization Levels

### Level 1: Configuration Only (Easy)
- Modify YAML config file
- Change database connection
- Adjust statistics tracked
- **Time:** 30 minutes

### Level 2: Add Sport-Specific Metrics (Medium)
- Create custom metrics module
- Implement sport-specific calculations
- Add new MCP tools
- **Time:** 2-4 hours

### Level 3: Full Custom Module (Advanced)
- Create complete sport module
- Custom ML models
- Advanced analytics
- **Time:** 1-2 days

---

## 📊 Supported Sports Matrix

| Sport | Category | Config File | Module | Status |
|-------|----------|-------------|--------|--------|
| NCAA Men's Basketball | basketball | ncaa_mbb.yaml | ✅ Complete | Example |
| NCAA Women's Basketball | basketball | ncaa_wbb.yaml | ✅ Complete | Ready |
| NBA | basketball | nba.yaml | ✅ Complete | Ready |
| WNBA | basketball | wnba.yaml | ✅ Complete | Ready |
| NCAA Football | football | ncaa_football.yaml | 🚧 Module needed | Template |
| NFL | football | nfl.yaml | 🚧 Module needed | Template |
| MLB | baseball | mlb.yaml | 🚧 Module needed | Template |
| NHL | hockey | nhl.yaml | 🚧 Module needed | Template |
| MLS | soccer | mls.yaml | 🚧 Module needed | Template |

---

## 🧪 Testing Framework

```python
# tests/test_sport_template.py

import pytest
from mcp_server.config_loader import SportConfigLoader

def test_load_ncaa_mbb():
    """Test loading NCAA Men's Basketball config."""
    loader = SportConfigLoader()
    sport = loader.get_sport_module('ncaa_mens_basketball')

    assert sport.name == "NCAA Men's Basketball"
    assert sport.short_name == "ncaa_mbb"
    assert len(sport.positions) == 5

def test_calculate_efficiency():
    """Test PER calculation."""
    loader = SportConfigLoader()
    sport = loader.get_sport_module('ncaa_mens_basketball')

    stats = {
        'points': 20,
        'rebounds': 8,
        'assists': 5,
        'steals': 2,
        'blocks': 1,
        'turnovers': 3,
        'minutes': 30
    }

    per = sport.calculate_player_efficiency(stats)
    assert per > 0
```

---

## 📦 Deployment Options

### Option 1: Single Multi-Sport Server
```bash
# One server handles all sports
python mcp_server/server.py --sports ncaa_mbb,ncaa_wbb,nba
```

### Option 2: Sport-Specific Servers
```bash
# Dedicated server per sport
python mcp_server/server.py --sport ncaa_mbb --port 5000
python mcp_server/server.py --sport nfl --port 5001
```

### Option 3: Docker Deployment
```bash
# Build template image
docker build -t sports-mcp-template .

# Deploy for specific sport
docker run -e SPORT=ncaa_mbb sports-mcp-template
```

---

## 🎯 Example: NCAA Men's Basketball Implementation

### Quick Start

```bash
# 1. Clone template
git clone https://github.com/your-org/sports-mcp-template
cd sports-mcp-template

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure for NCAA Men's Basketball
cp config/sports/ncaa_mens_basketball.yaml config/sports/active_sport.yaml
cp .env.example .env

# 4. Set database credentials
vim .env  # Set NCAA_MBB_DB_HOST, etc.

# 5. Test
python scripts/test_sport_config.py ncaa_mens_basketball

# 6. Run MCP server
python mcp_server/server.py --sport ncaa_mens_basketball
```

### Available Tools

The NCAA Men's Basketball instance provides:

- `ncaa_mbb_query_players` - Query player database
- `ncaa_mbb_query_teams` - Query team database
- `ncaa_mbb_analyze_player` - Player performance analysis
- `ncaa_mbb_compare_players` - Compare multiple players
- `ncaa_mbb_predict_tournament` - Tournament predictions
- `ncaa_mbb_calculate_efficiency` - Calculate PER
- `ncaa_mbb_team_stats` - Team statistics
- `ncaa_mbb_cluster_players` - Player clustering

---

## 🔄 Migration from Existing NBA MCP

### Reuse Components

From the existing NBA MCP, these can be directly reused:

1. **Machine Learning Tools** → `mcp_server/ml/`
2. **Statistical Engine** → `mcp_server/core/statistical_engine.py`
3. **Database Connector** → `mcp_server/core/data_connector.py`
4. **Formula Engine** → `mcp_server/core/formula_engine.py`

### Basketball Module

Extract NBA-specific logic into basketball module:

```python
# mcp_server/sports/basketball/metrics.py
# Contains all basketball metrics (PER, TS%, eFG%, etc.)

# Then configure for different leagues:
# - NCAA Men's Basketball
# - NCAA Women's Basketball
# - NBA
# - WNBA
# - International leagues
```

---

## 📚 Documentation

### For Template Users

- **TEMPLATE_USAGE_GUIDE.md** - How to use the template
- **SPORT_SETUP_GUIDE.md** - Setting up a new sport
- **CONFIGURATION_GUIDE.md** - Config file reference
- **API_REFERENCE.md** - MCP tools API

### For Developers

- **ARCHITECTURE.md** - System architecture
- **ADDING_NEW_SPORT.md** - Developer guide
- **CONTRIBUTING.md** - Contribution guidelines
- **CHANGELOG.md** - Version history

---

## 🚀 Next Steps

### Phase 1: Template Creation (1-2 weeks)
1. Create `sports-mcp-template` repository
2. Build core universal components
3. Implement basketball module (reuse NBA code)
4. Create configuration system
5. Build CLI tools

### Phase 2: NCAA Men's Basketball (1 week)
1. Create NCAA MBB configuration
2. Set up database connection
3. Generate MCP tools
4. Test and validate
5. Document use cases

### Phase 3: Additional Sports (2-4 weeks)
1. NCAA Women's Basketball (1 day - reuse basketball module)
2. NFL (1 week - new football module)
3. MLB (1 week - new baseball module)
4. NHL (1 week - new hockey module)

### Phase 4: Community & Documentation (Ongoing)
1. Create example implementations
2. Write comprehensive guides
3. Build community templates
4. Maintain and update

---

## 💡 Benefits of Template Approach

### For You
- ✅ Reuse 80% of code across all sports
- ✅ Consistent API across sports
- ✅ Easy to maintain and update
- ✅ Rapid deployment of new sports

### For Users
- ✅ Familiar interface across sports
- ✅ Same analytical capabilities everywhere
- ✅ Easy to switch between sports
- ✅ Consistent data quality

### For Community
- ✅ Open source template
- ✅ Community contributions
- ✅ Shared best practices
- ✅ Growing sports coverage

---

## 📞 Getting Started

### Repository Setup

```bash
# Create new template repository
mkdir sports-mcp-template
cd sports-mcp-template
git init

# Copy structure from NBA MCP
# Generalize components
# Create config system
# Build CLI tools

# First sport: NCAA Men's Basketball
python scripts/create_new_sport.py --name "NCAA Men's Basketball"
```

### Questions to Answer

1. **Database Schema**: Consistent across sports?
2. **Hosting**: Separate servers or unified?
3. **API Keys**: Shared or sport-specific?
4. **Documentation**: Centralized or distributed?

---

**Ready to build?** Let me know and I can help you:
1. Set up the template repository structure
2. Migrate NBA MCP code to template
3. Create NCAA Men's Basketball configuration
4. Build additional sport modules

This template approach will make it trivial to add new sports - just configure and deploy! 🚀








