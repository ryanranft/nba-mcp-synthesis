# Sports MCP Template - Quick Start Guide

**Goal:** Create NCAA Men's Basketball MCP in < 1 hour using the template

---

## 🎯 What You're Building

A **universal Sports MCP Template** that works for any sport:

```
Today: NCAA Men's Basketball MCP
Tomorrow: NCAA Women's Basketball, NFL, MLB, NHL, etc.

ONE template → INFINITE sports
```

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Create Template Repository (15 min)

```bash
# Create new repository
mkdir sports-mcp-template
cd sports-mcp-template

# Initialize
git init
python -m venv venv
source venv/bin/activate
pip install fastmcp pydantic pyyaml psycopg2-binary boto3 pandas

# Create structure
mkdir -p config/sports config/analytics
mkdir -p mcp_server/{core,sports/{basketball,football,baseball},tools,ml}
mkdir -p scripts tests docs
```

### Step 2: Copy Core from NBA MCP (10 min)

```bash
# Copy reusable components from your NBA MCP
cp ../nba-mcp-synthesis/mcp_server/tools/math_helper.py mcp_server/core/
cp ../nba-mcp-synthesis/mcp_server/tools/stats_helper.py mcp_server/core/
cp ../nba-mcp-synthesis/mcp_server/tools/ml_*.py mcp_server/ml/
cp ../nba-mcp-synthesis/mcp_server/connectors/rds_connector.py mcp_server/core/
cp ../nba-mcp-synthesis/mcp_server/connectors/s3_connector.py mcp_server/core/
```

### Step 3: Create NCAA MBB Config (5 min)

```bash
# Create configuration
cat > config/sports/ncaa_mens_basketball.yaml << 'EOF'
sport:
  name: "NCAA Men's Basketball"
  short_name: "ncaa_mbb"
  category: "basketball"
  league: "NCAA"
  division: "I"
  gender: "male"

data_sources:
  database:
    type: "postgresql"
    host: "${NCAA_MBB_DB_HOST}"
    port: 5432
    database: "ncaa_basketball"
    username: "${NCAA_MBB_DB_USER}"
    password: "${NCAA_MBB_DB_PASSWORD}"

positions:
  - {name: "Point Guard", abbr: "PG", num: 1}
  - {name: "Shooting Guard", abbr: "SG", num: 2}
  - {name: "Small Forward", abbr: "SF", num: 3}
  - {name: "Power Forward", abbr: "PF", num: 4}
  - {name: "Center", abbr: "C", num: 5}

metrics:
  - player_efficiency_rating
  - true_shooting_percentage
  - usage_rate
  - offensive_rating
  - defensive_rating
EOF
```

---

## 📝 Minimum Viable Template (30 min)

### 1. Base Sport Class

```python
# mcp_server/sports/base_sport.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import yaml
import os
from pathlib import Path

class BaseSport(ABC):
    """Base class for all sports."""

    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            config_str = f.read()
            # Replace environment variables
            for key, value in os.environ.items():
                config_str = config_str.replace(f"${{{key}}}", value)
            self.config = yaml.safe_load(config_str)

        self.name = self.config['sport']['name']
        self.short_name = self.config['sport']['short_name']
        self.category = self.config['sport']['category']

    @abstractmethod
    def calculate_player_efficiency(self, stats: Dict[str, float]) -> float:
        """Calculate player efficiency (sport-specific)."""
        pass

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get list of positions."""
        return self.config.get('positions', [])

    def get_metrics(self) -> List[str]:
        """Get list of available metrics."""
        return self.config.get('metrics', [])

    def get_db_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self.config.get('data_sources', {}).get('database', {})
```

### 2. Basketball Module

```python
# mcp_server/sports/basketball/__init__.py

from ..base_sport import BaseSport
from typing import Dict

class Basketball(BaseSport):
    """Basketball-specific implementation."""

    def calculate_player_efficiency(self, stats: Dict[str, float]) -> float:
        """
        PER = (PTS + REB + AST + STL + BLK - TOV) / MIN
        Simplified version for MVP.
        """
        return (
            stats.get('points', 0) +
            stats.get('rebounds', 0) +
            stats.get('assists', 0) +
            stats.get('steals', 0) +
            stats.get('blocks', 0) -
            stats.get('turnovers', 0)
        ) / max(stats.get('minutes', 1), 1)

    def calculate_true_shooting(self, stats: Dict[str, float]) -> float:
        """TS% = PTS / (2 * (FGA + 0.44 * FTA))"""
        pts = stats.get('points', 0)
        fga = stats.get('field_goals_attempted', 0)
        fta = stats.get('free_throws_attempted', 0)

        denominator = 2 * (fga + 0.44 * fta)
        return pts / denominator if denominator > 0 else 0.0
```

### 3. Config Loader

```python
# mcp_server/config_loader.py

from pathlib import Path
from typing import Optional
import yaml

class SportConfigLoader:
    """Load sport configurations."""

    def __init__(self, config_dir: str = "config/sports"):
        self.config_dir = Path(config_dir)
        self.current_sport = None

    def load_sport(self, sport_name: str):
        """Load a sport configuration."""
        config_path = self.config_dir / f"{sport_name}.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Sport config not found: {sport_name}")

        # Determine sport category
        with open(config_path) as f:
            config = yaml.safe_load(f)

        category = config['sport']['category']

        # Import appropriate module
        if category == 'basketball':
            from .sports.basketball import Basketball
            self.current_sport = Basketball(str(config_path))
        elif category == 'football':
            from .sports.football import Football
            self.current_sport = Football(str(config_path))
        else:
            raise ValueError(f"Unsupported sport category: {category}")

        return self.current_sport

    def list_sports(self) -> list:
        """List available sports."""
        return [f.stem for f in self.config_dir.glob("*.yaml")]
```

### 4. Simple MCP Server

```python
# mcp_server/server.py

from fastmcp import FastMCP
from .config_loader import SportConfigLoader
from pydantic import BaseModel, Field
from typing import Optional
import asyncio

# Initialize
mcp = FastMCP("Sports MCP Template")
config_loader = SportConfigLoader()

# Load sport from environment or default
import os
SPORT = os.getenv('SPORT', 'ncaa_mens_basketball')
sport = config_loader.load_sport(SPORT)

# Parameter models
class PlayerQueryParams(BaseModel):
    player_name: Optional[str] = Field(None, description="Player name to search")
    team: Optional[str] = Field(None, description="Team name")
    limit: int = Field(10, description="Max results", ge=1, le=100)

class PlayerStatsParams(BaseModel):
    points: float
    rebounds: float
    assists: float
    steals: float = 0
    blocks: float = 0
    turnovers: float = 0
    minutes: float = 1

# MCP Tools
@mcp.tool()
async def query_players(params: PlayerQueryParams) -> dict:
    """Query players for the current sport."""
    return {
        "sport": sport.name,
        "query": params.player_name,
        "message": "Connect to database to return actual results"
    }

@mcp.tool()
async def calculate_player_efficiency(params: PlayerStatsParams) -> dict:
    """Calculate player efficiency rating."""
    stats = params.dict()
    per = sport.calculate_player_efficiency(stats)

    return {
        "sport": sport.name,
        "player_efficiency_rating": round(per, 2),
        "stats": stats
    }

@mcp.tool()
async def get_sport_info() -> dict:
    """Get information about the current sport."""
    return {
        "name": sport.name,
        "short_name": sport.short_name,
        "category": sport.category,
        "positions": sport.get_positions(),
        "available_metrics": sport.get_metrics()
    }

if __name__ == "__main__":
    mcp.run()
```

---

## 🧪 Test It (5 min)

```bash
# Set environment
export SPORT=ncaa_mens_basketball
export NCAA_MBB_DB_HOST=localhost
export NCAA_MBB_DB_USER=postgres
export NCAA_MBB_DB_PASSWORD=password

# Run server
python -m mcp_server.server

# Test in another terminal
python -c "
from mcp_server.config_loader import SportConfigLoader

loader = SportConfigLoader()
sport = loader.load_sport('ncaa_mens_basketball')

# Test PER calculation
stats = {
    'points': 25,
    'rebounds': 10,
    'assists': 8,
    'steals': 2,
    'blocks': 1,
    'turnovers': 3,
    'minutes': 35
}

per = sport.calculate_player_efficiency(stats)
print(f'PER: {per:.2f}')
"
```

---

## 🎯 Add Another Sport (5 min)

### NCAA Women's Basketball

```bash
# Copy men's config
cp config/sports/ncaa_mens_basketball.yaml \
   config/sports/ncaa_womens_basketball.yaml

# Edit one field
sed -i '' 's/male/female/' config/sports/ncaa_womens_basketball.yaml
sed -i '' 's/ncaa_mbb/ncaa_wbb/' config/sports/ncaa_womens_basketball.yaml

# Done! Now you can:
export SPORT=ncaa_womens_basketball
python -m mcp_server.server
```

### NFL (15 min - need football module)

```python
# mcp_server/sports/football/__init__.py

from ..base_sport import BaseSport
from typing import Dict

class Football(BaseSport):
    """Football-specific implementation."""

    def calculate_player_efficiency(self, stats: Dict[str, float]) -> float:
        """
        QB Rating formula (simplified).
        For other positions, use position-specific formulas.
        """
        position = stats.get('position', 'QB')

        if position == 'QB':
            return self._calculate_qb_rating(stats)
        elif position in ['RB', 'WR', 'TE']:
            return self._calculate_skill_rating(stats)
        else:
            return 0.0  # Define for other positions

    def _calculate_qb_rating(self, stats: Dict[str, float]) -> float:
        """Passer rating formula."""
        attempts = stats.get('pass_attempts', 1)
        completions = stats.get('completions', 0)
        yards = stats.get('pass_yards', 0)
        tds = stats.get('pass_tds', 0)
        ints = stats.get('interceptions', 0)

        # Simplified passer rating
        if attempts == 0:
            return 0.0

        comp_pct = (completions / attempts - 0.3) * 5
        yards_per_att = (yards / attempts - 3) * 0.25
        td_pct = (tds / attempts) * 20
        int_pct = 2.375 - (ints / attempts * 25)

        rating = ((comp_pct + yards_per_att + td_pct + int_pct) / 6) * 100
        return max(0, min(158.3, rating))  # Cap at 0-158.3

    def _calculate_skill_rating(self, stats: Dict[str, float]) -> float:
        """Rating for RB/WR/TE."""
        touches = stats.get('rush_attempts', 0) + stats.get('receptions', 0)
        total_yards = stats.get('rush_yards', 0) + stats.get('rec_yards', 0)
        tds = stats.get('rush_tds', 0) + stats.get('rec_tds', 0)

        if touches == 0:
            return 0.0

        return (total_yards + (tds * 60)) / touches
```

```yaml
# config/sports/nfl.yaml

sport:
  name: "NFL"
  short_name: "nfl"
  category: "football"
  league: "NFL"

positions:
  - {name: "Quarterback", abbr: "QB"}
  - {name: "Running Back", abbr: "RB"}
  - {name: "Wide Receiver", abbr: "WR"}
  - {name: "Tight End", abbr: "TE"}
  - {name: "Offensive Line", abbr: "OL"}
  - {name: "Defensive Line", abbr: "DL"}
  - {name: "Linebacker", abbr: "LB"}
  - {name: "Cornerback", abbr: "CB"}
  - {name: "Safety", abbr: "S"}

metrics:
  - passer_rating
  - yards_per_carry
  - yards_per_reception
  - sacks
  - tackles
```

---

## 📊 Comparison: Before vs After

### Before (Separate Projects)

```
nba-mcp-synthesis/          (90 tools, 3 months)
ncaa-basketball-mcp/        (90 tools, 3 months)
nfl-mcp/                    (90 tools, 3 months)
mlb-mcp/                    (90 tools, 3 months)

Total: 4 projects, 12 months, lots of duplication
```

### After (Template Approach)

```
sports-mcp-template/        (Core: 2 weeks)
├── NCAA MBB (config)       (30 minutes)
├── NCAA WBB (config)       (5 minutes)
├── NBA (config)            (30 minutes)
├── NFL (module + config)   (1 day)
└── MLB (module + config)   (1 day)

Total: 1 project, 3 weeks, 80% code reuse
```

---

## 🎯 Next Steps

### Immediate (Today)
1. ✅ Create `sports-mcp-template` repository
2. ✅ Copy structure from NBA MCP
3. ✅ Create NCAA Men's Basketball config
4. ✅ Test basic functionality

### Short Term (This Week)
1. Add database connectivity
2. Implement all basketball metrics
3. Create NCAA Women's Basketball
4. Write documentation

### Medium Term (This Month)
1. Add NFL module
2. Add MLB module
3. Add NHL module
4. Community templates

---

## 💡 Pro Tips

### Reuse Strategy

**From NBA MCP, reuse 100%:**
- All ML tools (clustering, classification, etc.)
- All statistical tools (mean, variance, correlation)
- All database tools (query, list tables, etc.)
- All S3 tools (file operations)
- Book reading tools

**Sport-specific (10-20% new code):**
- Metrics calculations (PER, passer rating, etc.)
- Position definitions
- Rule validations
- Database schema mappings

### Development Workflow

```bash
# 1. Start with configuration
vim config/sports/new_sport.yaml

# 2. Test loading
python -c "from mcp_server.config_loader import SportConfigLoader; \
           SportConfigLoader().load_sport('new_sport')"

# 3. Add sport-specific metrics (if needed)
vim mcp_server/sports/new_sport/metrics.py

# 4. Run server
export SPORT=new_sport
python -m mcp_server.server

# 5. Test with MCP client
python scripts/test_mcp_client.py
```

---

## 📦 Repository Structure (Final)

```
sports-mcp-template/
├── README.md                          "Universal Sports MCP Template"
├── TEMPLATE_USAGE_GUIDE.md            How to use template
├── SPORT_SETUP_GUIDE.md               Adding new sports
├── config/
│   └── sports/
│       ├── ncaa_mens_basketball.yaml  ✅ Example
│       ├── ncaa_womens_basketball.yaml ✅ Example
│       ├── nba.yaml                    ✅ Example
│       ├── nfl.yaml                    🚧 Template
│       ├── mlb.yaml                    🚧 Template
│       └── template.yaml               📝 Blank template
├── mcp_server/
│   ├── server.py                      Main server
│   ├── config_loader.py               Config loader
│   ├── core/                          Universal components (from NBA MCP)
│   ├── sports/
│   │   ├── base_sport.py              Base class
│   │   ├── basketball/                Basketball module
│   │   ├── football/                  Football module
│   │   └── baseball/                  Baseball module
│   ├── tools/                         Generic MCP tools
│   └── ml/                            ML tools (from NBA MCP)
└── scripts/
    ├── create_new_sport.py            CLI to create sport
    ├── test_sport.py                  Test configuration
    └── deploy_sport.py                Deploy instance
```

---

## 🎉 Success Metrics

### Template Success
- ✅ Works for 3+ sports categories
- ✅ 80%+ code reuse
- ✅ < 1 hour to add new sport (config only)
- ✅ < 1 day to add new sport (with module)

### NCAA MBB Success
- ✅ All basketball metrics working
- ✅ Database connectivity
- ✅ MCP tools functional
- ✅ Claude Desktop integration

---

**Ready to build?**

Start with the 3-step setup above, and you'll have NCAA Men's Basketball MCP running in < 1 hour! 🏀🚀


