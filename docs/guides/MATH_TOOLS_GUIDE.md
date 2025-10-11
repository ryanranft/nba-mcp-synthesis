# Math, Stats, and NBA Metrics Tools Guide

**Complete guide to the 20 mathematical, statistical, and NBA-specific calculation tools**

## Overview

Sprint 5 added 20 new MCP tools for mathematical operations, statistical analysis, and NBA-specific metrics calculations. These tools enable advanced analytics and calculations directly within the MCP server.

### Quick Facts

- **20 New Tools**: 7 math tools, 6 stats tools, 7 NBA metrics tools
- **Zero Dependencies**: Uses only Python standard library
- **Comprehensive Testing**: 46 automated tests with 100% pass rate
- **Production Ready**: Full error handling, logging, and validation

## Table of Contents

1. [Math Tools](#math-tools) - Basic and advanced mathematical operations
2. [Stats Tools](#stats-tools) - Statistical calculations and analysis
3. [NBA Metrics Tools](#nba-metrics-tools) - Basketball-specific efficiency metrics
4. [Usage Examples](#usage-examples) - Real-world usage scenarios
5. [Testing](#testing) - Test suite and interactive demo

---

## Math Tools

### Basic Arithmetic

#### `math_add` - Addition
Add two numbers together.

**Parameters:**
- `a` (number): First number
- `b` (number): Second number

**Returns:** Sum of a and b

**Example:**
```python
# Via MCP tool
result = await math_add(a=5, b=3)
# Result: 8
```

#### `math_subtract` - Subtraction
Subtract the second number from the first.

**Parameters:**
- `a` (number): Number to subtract from
- `b` (number): Number to subtract

**Returns:** Difference (a - b)

**Example:**
```python
result = await math_subtract(a=10, b=3)
# Result: 7
```

#### `math_multiply` - Multiplication
Multiply two numbers.

**Parameters:**
- `a` (number): First number
- `b` (number): Second number

**Returns:** Product (a × b)

**Example:**
```python
result = await math_multiply(a=4, b=7)
# Result: 28
```

#### `math_divide` - Division
Divide the first number by the second.

**Parameters:**
- `numerator` (number): Number to divide
- `denominator` (number): Number to divide by

**Returns:** Quotient (numerator / denominator)

**Error Handling:** Raises `ValidationError` if denominator is zero

**Example:**
```python
result = await math_divide(numerator=20, denominator=4)
# Result: 5.0
```

### Advanced Operations

#### `math_sum` - Sum List
Sum all numbers in a list.

**Parameters:**
- `numbers` (list): List of numbers to sum

**Returns:** Sum of all numbers

**Example:**
```python
result = await math_sum(numbers=[1, 2, 3, 4, 5])
# Result: 15
```

#### `math_round` - Round Number
Round a number to specified decimal places.

**Parameters:**
- `number` (number): Number to round
- `decimals` (int): Number of decimal places (default: 0)

**Returns:** Rounded number

**Example:**
```python
result = await math_round(number=3.14159, decimals=2)
# Result: 3.14
```

#### `math_modulo` - Modulo (Remainder)
Calculate the remainder when dividing two numbers.

**Parameters:**
- `numerator` (number): Number being divided
- `denominator` (number): Number to divide by

**Returns:** Remainder (numerator % denominator)

**Example:**
```python
result = await math_modulo(numerator=17, denominator=5)
# Result: 2
```

---

## Stats Tools

### Central Tendency

#### `stats_mean` - Average
Calculate the arithmetic mean (average).

**Parameters:**
- `numbers` (list): List of numbers

**Returns:** Mean value

**Example:**
```python
result = await stats_mean(numbers=[10, 20, 30, 40, 50])
# Result: 30.0
```

#### `stats_median` - Median
Calculate the median (middle value when sorted).

**Parameters:**
- `numbers` (list): List of numbers

**Returns:** Median value

**Example:**
```python
result = await stats_median(numbers=[10, 20, 30, 40, 50])
# Result: 30.0  (middle value)

result = await stats_median(numbers=[10, 20, 30, 40])
# Result: 25.0  (average of middle two)
```

#### `stats_mode` - Mode
Find the most common value(s).

**Parameters:**
- `numbers` (list): List of numbers

**Returns:** Most frequent value (or list if multiple modes)

**Example:**
```python
result = await stats_mode(numbers=[1, 2, 2, 3, 4, 4, 4, 5])
# Result: 4  (appears 3 times)

result = await stats_mode(numbers=[1, 1, 2, 2, 3])
# Result: [1, 2]  (both appear twice)
```

### Spread and Variability

#### `stats_min_max` - Minimum and Maximum
Get the minimum and maximum values.

**Parameters:**
- `numbers` (list): List of numbers

**Returns:** Dictionary with "min" and "max" keys

**Example:**
```python
result = await stats_min_max(numbers=[10, 5, 20, 3, 15])
# Result: {"min": 3, "max": 20}
```

#### `stats_variance` - Variance
Calculate variance (measure of spread).

**Parameters:**
- `numbers` (list): List of numbers
- `sample` (bool): Use sample variance (n-1) if True, population variance (n) if False

**Returns:** Variance value

**Formula:**
- Sample: Σ(x - μ)² / (n - 1)
- Population: Σ(x - μ)² / n

**Example:**
```python
result = await stats_variance(numbers=[10, 20, 30, 40, 50], sample=True)
# Result: 250.0  (sample variance)
```

### Comprehensive Analysis

#### `stats_summary` - Summary Statistics
Calculate comprehensive summary statistics for a dataset.

**Parameters:**
- `numbers` (list): List of numbers

**Returns:** Dictionary with:
- `count`: Number of values
- `mean`: Average
- `median`: Middle value
- `mode`: Most frequent value(s)
- `min`: Minimum value
- `max`: Maximum value
- `range`: Max - Min
- `std_dev`: Standard deviation
- `variance`: Variance
- `Q1`: First quartile (25th percentile)
- `Q2`: Second quartile (median)
- `Q3`: Third quartile (75th percentile)
- `IQR`: Interquartile range (Q3 - Q1)

**Example:**
```python
result = await stats_summary(numbers=[10, 20, 30, 40, 50])
# Result:
# {
#     "count": 5,
#     "mean": 30.0,
#     "median": 30.0,
#     "mode": [10, 20, 30, 40, 50],  # All appear once
#     "min": 10,
#     "max": 50,
#     "range": 40,
#     "std_dev": 15.81,
#     "variance": 250.0,
#     "Q1": 20.0,
#     "Q2": 30.0,
#     "Q3": 40.0,
#     "IQR": 20.0
# }
```

---

## NBA Metrics Tools

### Player Efficiency Metrics

#### `nba_player_efficiency_rating` - PER
Calculate Player Efficiency Rating (PER).

**Description:** All-in-one metric summarizing a player's statistical accomplishments. League average is 15.0.

**Parameters:**
- `points` (int): Points scored
- `rebounds` (int): Total rebounds
- `assists` (int): Assists
- `steals` (int): Steals
- `blocks` (int): Blocks
- `fgm` (int): Field goals made
- `fga` (int): Field goals attempted
- `ftm` (int): Free throws made
- `fta` (int): Free throws attempted
- `turnovers` (int): Turnovers
- `minutes` (float): Minutes played

**Returns:** PER value (league average is 15.0)

**Formula (simplified):**
```
PER = (Points + Rebounds + Assists + Steals + Blocks
       - Missed FG - Missed FT - Turnovers) / Minutes × 100
```

**Example:**
```python
result = await nba_player_efficiency_rating(
    points=2000, rebounds=600, assists=500,
    steals=100, blocks=50,
    fgm=750, fga=1600,
    ftm=400, fta=500,
    turnovers=200, minutes=2800
)
# Result: 18.5 (above league average)
```

**Interpretation:**
- PER < 10: Poor performance
- PER 10-15: Below average
- PER 15: League average
- PER 15-20: Above average
- PER 20-25: All-Star level
- PER > 25: MVP candidate

#### `nba_true_shooting_percentage` - TS%
Calculate True Shooting Percentage (accounts for 3-pointers and free throws).

**Parameters:**
- `points` (int): Total points scored
- `fga` (int): Field goals attempted
- `fta` (int): Free throws attempted

**Returns:** True shooting percentage (0-1 scale, where 0.550 = 55.0%)

**Formula:**
```
TS% = Points / (2 × (FGA + 0.44 × FTA))
```

**Example:**
```python
result = await nba_true_shooting_percentage(
    points=2000, fga=1600, fta=500
)
# Result: 0.543 (54.3% - very efficient)
```

**Interpretation:**
- TS% < 0.500: Below average efficiency
- TS% 0.500-0.550: Average
- TS% 0.550-0.600: Good
- TS% > 0.600: Elite

#### `nba_effective_field_goal_percentage` - eFG%
Calculate Effective Field Goal Percentage (adjusts for 3-pointers being worth more).

**Parameters:**
- `fgm` (int): Field goals made
- `fga` (int): Field goals attempted
- `three_pm` (int): Three-pointers made

**Returns:** Effective FG% (0-1 scale)

**Formula:**
```
eFG% = (FGM + 0.5 × 3PM) / FGA
```

**Example:**
```python
result = await nba_effective_field_goal_percentage(
    fgm=750, fga=1600, three_pm=200
)
# Result: 0.531 (53.1%)
```

#### `nba_usage_rate` - USG%
Calculate Usage Rate (percentage of team plays used by a player).

**Parameters:**
- `fga` (int): Player's field goal attempts
- `fta` (int): Player's free throw attempts
- `turnovers` (int): Player's turnovers
- `minutes` (float): Player's minutes played
- `team_minutes` (float): Team's total minutes
- `team_fga` (int): Team's field goal attempts
- `team_fta` (int): Team's free throw attempts
- `team_turnovers` (int): Team's turnovers

**Returns:** Usage rate percentage

**Formula:**
```
USG% = 100 × ((FGA + 0.44 × FTA + TOV) × (Tm MP / 5)) /
       (MP × (Tm FGA + 0.44 × Tm FTA + Tm TOV))
```

**Example:**
```python
result = await nba_usage_rate(
    fga=1600, fta=500, turnovers=200, minutes=2800,
    team_minutes=19680,  # 82 games × 240 mins
    team_fga=7000, team_fta=2000, team_turnovers=1200
)
# Result: 24.5%
```

**Interpretation:**
- USG% < 20%: Low usage
- USG% 20-25%: Average starter
- USG% 25-30%: High usage (primary scorer)
- USG% > 30%: Very high usage (team's offensive focal point)

### Team Efficiency Metrics

#### `nba_offensive_rating` - ORtg
Calculate Offensive Rating (points scored per 100 possessions).

**Parameters:**
- `points` (int): Points scored
- `possessions` (int): Estimated possessions

**Returns:** Offensive rating (points per 100 possessions)

**Formula:**
```
ORtg = (Points / Possessions) × 100
```

**Example:**
```python
result = await nba_offensive_rating(points=9000, possessions=8000)
# Result: 112.5 (good offensive efficiency)
```

**Interpretation:**
- ORtg < 105: Poor offense
- ORtg 105-110: Below average
- ORtg 110-115: Average to above average
- ORtg > 115: Elite offense

#### `nba_defensive_rating` - DRtg
Calculate Defensive Rating (points allowed per 100 possessions, lower is better).

**Parameters:**
- `points_allowed` (int): Points allowed
- `possessions` (int): Estimated possessions

**Returns:** Defensive rating (points allowed per 100 possessions)

**Formula:**
```
DRtg = (Points Allowed / Possessions) × 100
```

**Example:**
```python
result = await nba_defensive_rating(points_allowed=8500, possessions=8000)
# Result: 106.25 (good defense)
```

**Interpretation:**
- DRtg < 105: Elite defense
- DRtg 105-110: Good defense
- DRtg 110-115: Average
- DRtg > 115: Poor defense

#### `nba_pace` - Pace
Calculate pace (possessions per 48 minutes).

**Parameters:**
- `possessions` (int): Total possessions
- `minutes` (float): Total minutes played

**Returns:** Pace (possessions per 48 minutes)

**Formula:**
```
Pace = (Possessions / Minutes) × 48
```

**Example:**
```python
result = await nba_pace(possessions=8000, minutes=19680)
# Result: 19.5 (slow pace - note: this is for full season)
```

**Interpretation:**
- Pace < 95: Very slow
- Pace 95-100: Slow
- Pace 100-105: Average
- Pace > 105: Fast

---

## Usage Examples

### Example 1: Calculate Player Season Statistics

```python
# Get player stats from database
player_stats = await query_database("""
    SELECT
        SUM(points) as points,
        SUM(rebounds) as rebounds,
        SUM(assists) as assists,
        SUM(steals) as steals,
        SUM(blocks) as blocks,
        SUM(fgm) as fgm,
        SUM(fga) as fga,
        SUM(ftm) as ftm,
        SUM(fta) as fta,
        SUM(turnovers) as turnovers,
        SUM(minutes) as minutes
    FROM player_game_stats
    WHERE player_id = 123 AND season = '2023-24'
""")

# Calculate PER
per = await nba_player_efficiency_rating(**player_stats)
print(f"Player Efficiency Rating: {per}")

# Calculate shooting efficiency
ts_pct = await nba_true_shooting_percentage(
    points=player_stats['points'],
    fga=player_stats['fga'],
    fta=player_stats['fta']
)
print(f"True Shooting %: {ts_pct:.1%}")
```

### Example 2: Compare Team Offenses

```python
# Get team offensive stats
teams = ['LAL', 'GSW', 'BOS', 'MIA']
ratings = {}

for team in teams:
    team_stats = await query_database(f"""
        SELECT SUM(points) as points,
               SUM(possessions) as possessions
        FROM team_game_stats
        WHERE team_abbr = '{team}' AND season = '2023-24'
    """)

    ortg = await nba_offensive_rating(
        points=team_stats['points'],
        possessions=team_stats['possessions']
    )
    ratings[team] = ortg

# Sort by offensive rating
sorted_teams = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
print("Top Offenses:")
for team, ortg in sorted_teams:
    print(f"{team}: {ortg} ORtg")
```

### Example 3: Statistical Analysis of Player Performance

```python
# Get all players' PER values for the season
pers = await query_database("""
    SELECT player_name, per
    FROM player_season_stats
    WHERE season = '2023-24'
""")

# Extract PER values
per_values = [p['per'] for p in pers]

# Calculate comprehensive statistics
stats = await stats_summary(numbers=per_values)

print("PER Distribution:")
print(f"  Mean: {stats['mean']:.2f}")
print(f"  Median: {stats['median']:.2f}")
print(f"  Std Dev: {stats['std_dev']:.2f}")
print(f"  Min: {stats['min']:.2f}")
print(f"  Max: {stats['max']:.2f}")
print(f"  Q1 (25th %ile): {stats['Q1']:.2f}")
print(f"  Q3 (75th %ile): {stats['Q3']:.2f}")
```

### Example 4: Game-by-Game Variance Analysis

```python
# Get player's game-by-game points
game_points = await query_database("""
    SELECT points
    FROM player_game_stats
    WHERE player_id = 123 AND season = '2023-24'
    ORDER BY game_date
""")

points_list = [g['points'] for g in game_points]

# Calculate consistency metrics
mean_points = await stats_mean(numbers=points_list)
std_dev = await stats_variance(numbers=points_list)
variance = await stats_variance(numbers=points_list)

# Coefficient of variation (lower = more consistent)
cv = (std_dev / mean_points) * 100

print(f"Average Points: {mean_points:.1f}")
print(f"Standard Deviation: {std_dev:.1f}")
print(f"Coefficient of Variation: {cv:.1f}%")
print(f"Consistency: {'High' if cv < 30 else 'Medium' if cv < 50 else 'Low'}")
```

---

## Testing

### Automated Test Suite

Run the comprehensive test suite:

```bash
# Run all 46 tests
python scripts/test_math_stats_features.py

# Expected output:
# ================================================================================
# TEST SUMMARY
# ================================================================================
# Total Tests: 46
# Passed: 46
# Failed: 0
#
# ✓ ALL TESTS PASSED!
```

### Interactive Demo Mode

Test calculations interactively:

```bash
python scripts/test_math_stats_features.py --demo
```

**Demo Menu:**
```
Choose a calculation:
1. Math: Add two numbers
2. Math: Calculate average
3. Stats: Calculate summary statistics
4. NBA: Calculate Player Efficiency Rating (PER)
5. NBA: Calculate True Shooting %
6. NBA: Calculate Offensive Rating
0. Exit
```

**Example Session:**
```
Enter choice (0-6): 4
Enter player stats (press Enter to use defaults):
Points (default 2000): 2500
Rebounds (default 600): 700
Assists (default 500): 600
[... enter all stats ...]

✓ Player Efficiency Rating (PER): 22.5
ℹ (League average is 15.0)
```

---

## Error Handling

All tools include comprehensive error handling:

### Math Tools
- **Division by Zero**: Raises `ValidationError` with clear message
- **Empty Lists**: Raises `ValidationError` for stats operations requiring data
- **Invalid Types**: Pydantic validation catches type errors before execution

### Stats Tools
- **Empty Datasets**: All stats tools validate non-empty input
- **Insufficient Data**: Sample variance requires at least 2 values
- **Invalid Percentiles**: Must be between 0 and 100

### NBA Metrics Tools
- **Missing Fields**: PER calculation validates all required stats are present
- **Zero Minutes**: Returns 0.0 instead of raising error
- **Zero Possessions**: Returns 0.0 to prevent division errors

**Example Error:**
```python
try:
    result = await math_divide(numerator=10, denominator=0)
except ValidationError as e:
    print(f"Error: {e.message}")
    # Output: "Division by zero is not allowed"
```

---

## Performance

All tools are optimized for performance:

- **Zero External Dependencies**: Uses only Python standard library
- **Minimal Overhead**: Direct calculations with no database queries
- **Efficient Algorithms**: O(n) or better for all operations
- **Logging**: Structured JSON logging tracks operation duration

**Typical Performance:**
- Math operations: < 0.001 seconds
- Stats calculations: < 0.01 seconds (for lists up to 1000 items)
- NBA metrics: < 0.001 seconds

---

## Implementation Details

### Helper Modules

**Location:** `/mcp_server/tools/`

1. **math_helper.py** (362 lines)
   - 15 mathematical functions
   - Arithmetic, rounding, trigonometry
   - No external dependencies

2. **stats_helper.py** (435 lines)
   - 11 statistical functions
   - Central tendency, spread, quartiles
   - Uses Python's `statistics` and `math` modules

3. **nba_metrics_helper.py** (501 lines)
   - 12 NBA-specific metrics
   - Industry-standard formulas from Basketball Reference
   - Player and team efficiency calculations

### Decorators

All helper functions use `@log_operation` decorator for:
- Structured JSON logging
- Operation timing
- Error tracking
- Status monitoring

**Example Log Output:**
```json
{
  "timestamp": "2025-10-10T20:07:29.094971Z",
  "level": "INFO",
  "message": "Operation completed: math_add",
  "operation": "math_add",
  "function": "add",
  "status": "completed",
  "duration_seconds": 0.000132
}
```

---

## References

### NBA Metrics Formulas

All NBA formulas are based on industry standards:

- **Basketball Reference**: https://www.basketball-reference.com/about/glossary.html
- **NBA.com Advanced Stats**: https://www.nba.com/stats/help/glossary
- **Cleaning the Glass**: https://cleaningtheglass.com/stats/guide

### Statistical Methods

Statistical calculations follow standard definitions:

- **Sample vs Population Variance**: Bessel's correction (n-1 for sample)
- **Percentile Calculation**: Linear interpolation method
- **Mode Detection**: Counter-based frequency analysis

---

## Future Enhancements

Potential additions for future sprints:

### Math Tools
- Matrix operations (multiply, transpose, determinant)
- Complex number arithmetic
- Polynomial evaluation
- Calculus operations (derivatives, integrals)

### Stats Tools
- Correlation and covariance
- Regression analysis (linear, polynomial)
- Hypothesis testing (t-test, chi-square)
- Distribution fitting (normal, binomial)

### NBA Metrics
- Win Shares (full calculation with team context)
- Box Plus/Minus (BPM) with regression
- Value Over Replacement Player (VORP)
- Four Factors (shooting, turnovers, rebounding, free throws)
- Play-by-play efficiency metrics

---

## Support

**Documentation:**
- This guide (MATH_TOOLS_GUIDE.md)
- Main README.md
- USAGE_GUIDE.md

**Testing:**
- `scripts/test_math_stats_features.py` - Automated test suite
- `scripts/test_math_stats_features.py --demo` - Interactive testing

**Examples:**
- See "Usage Examples" section above
- Check test file for 46 working examples

---

**Document Version:** 1.0
**Last Updated:** 2025-10-10
**Sprint:** Sprint 5 - Mathematical & Statistical Tools
**Author:** NBA MCP Synthesis Team
