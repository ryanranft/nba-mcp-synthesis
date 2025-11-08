# NBA Play-by-Play Event Schema Documentation

**Last Updated:** 2025-01-06
**Data Source:** `hoopr_play_by_play` table

---

## Overview

This document defines all event types found in NBA play-by-play data and how to parse them into box score statistics.

## Table Schema

**Table:** `hoopr_play_by_play` (63 columns)

**Key Columns for Box Score Generation:**
- `sequence_number` - Event order within game
- `type_text` - Event type description (e.g., "Jump Shot", "Defensive Rebound")
- `type_id` - Numeric event type ID
- `text` - Full event description with player names and outcomes
- `scoring_play` - Boolean (0/1): whether points were scored
- `shooting_play` - Boolean (0/1): whether a shot was attempted
- `athlete_id_1` - Primary player (shooter, rebounder, turnover committer)
- `athlete_id_2` - Secondary player (assister, blocker, stealer)
- `athlete_id_3` - Tertiary player (rare, for multiple fouls)
- `score_value` - Points scored on this play (0, 1, 2, or 3)
- `away_score` - Away team score after this event
- `home_score` - Home team score after this event
- `period_number` - Quarter/period (1-4 regular, 5+ overtime)
- `clock_display_value` - Game clock (e.g., "7:58")

---

## Event Categories

### 1. SHOT EVENTS (Box Score: FGA, FGM, 3PA, 3PM)

#### Shot Types
| type_text | Description | Box Score Impact |
|-----------|-------------|------------------|
| `Jump Shot` | Standard jump shot | FGA +1, FGM +1 (if makes) |
| `Layup Shot` | Layup | FGA +1, FGM +1 (if makes) |
| `Dunk Shot` | Dunk | FGA +1, FGM +1 (if makes) |
| `Driving Layup Shot` | Driving layup | FGA +1, FGM +1 (if makes) |
| `Driving Dunk Shot` | Driving dunk | FGA +1, FGM +1 (if makes) |
| `Hook Shot` | Hook shot | FGA +1, FGM +1 (if makes) |
| `Floating Jump Shot` | Floater | FGA +1, FGM +1 (if makes) |
| `Step Back Jump Shot` | Step-back jumper | FGA +1, FGM +1 (if makes) |
| `Fade Away Jump Shot` | Fadeaway | FGA +1, FGM +1 (if makes) |
| `Tip Shot` | Tip-in | FGA +1, FGM +1 (if makes) |
| `Alley Oop Dunk Shot` | Alley-oop dunk | FGA +1, FGM +1 (if makes) |
| `Putback Dunk Shot` | Putback dunk | FGA +1, FGM +1 (if makes) |
| `Layup Shot Putback` | Putback layup | FGA +1, FGM +1 (if makes) |
| `Reverse Layup Shot` | Reverse layup | FGA +1, FGM +1 (if makes) |
| `Turnaround Jump Shot` | Turnaround jumper | FGA +1, FGM +1 (if makes) |
| `Turnaround Hook Shot` | Turnaround hook | FGA +1, FGM +1 (if makes) |
| `Driving Hook Shot` | Driving hook | FGA +1, FGM +1 (if makes) |
| `Driving Floating Jump Shot` | Driving floater | FGA +1, FGM +1 (if makes) |
| `Layup Driving Reverse` | Driving reverse layup | FGA +1, FGM +1 (if makes) |

#### Parsing Shot Outcomes
**Text Field Patterns:**
- **Made shot:** `"{Player} makes {distance}-foot {shot type}"`
  - Example: `"E'Twaun Moore makes 22-foot jumper"`
  - Box Score: FGA +1, FGM +1

- **Missed shot:** `"{Player} misses {distance}-foot {shot type}"`
  - Example: `"Chris Copeland misses 24-foot three point jumper"`
  - Box Score: FGA +1 (FGM unchanged)

- **Blocked shot:** `"{Blocker} blocks {Shooter}'s {distance}-foot {shot type}"`
  - Example: `"Carmelo Anthony blocks Glen Davis's 5-foot jumper"`
  - Box Score: Shooter FGA +1, Blocker BLK +1

#### Three-Point Shots
**Identification:**
- Text contains "three point" or "3-point"
- Shot distance typically ≥22 feet (though not always)

**Box Score Impact:**
- FGA +1, 3PA +1
- If makes: FGM +1, 3PM +1, PTS +3
- If misses: No FGM/3PM, no points

#### Assists
**Pattern:** Made shots with `"({Assister} assists)"` in text

**Example:** `"J.R. Smith makes driving layup (Tyson Chandler assists)"`

**Box Score:**
- Shooter: FGM +1, PTS +2
- Assister (`athlete_id_2`): AST +1

---

### 2. FREE THROW EVENTS (Box Score: FTA, FTM)

| type_text | Description | Box Score Impact |
|-----------|-------------|------------------|
| `Free Throw - 1 of 1` | Single free throw | FTA +1, FTM +1 (if makes) |
| `Free Throw - 1 of 2` | First of two free throws | FTA +1, FTM +1 (if makes) |
| `Free Throw - 2 of 2` | Second of two free throws | FTA +1, FTM +1 (if makes) |
| `Free Throw - 1 of 3` | First of three free throws | FTA +1, FTM +1 (if makes) |
| `Free Throw - 2 of 3` | Second of three free throws | FTA +1, FTM +1 (if makes) |
| `Free Throw - 3 of 3` | Third of three free throws | FTA +1, FTM +1 (if makes) |
| `Free Throw - Technical` | Technical foul free throw | FTA +1, FTM +1 (if makes) |

**Text Patterns:**
- **Made:** `"{Player} makes free throw {X} of {Y}"`
- **Missed:** `"{Player} misses free throw {X} of {Y}"`

**Points Scored:**
- Each made free throw: PTS +1

**Important Notes:**
- **Offensive Rebound after missed FT:** Between "1 of 2" and "2 of 2", there's often an "Offensive Rebound" event
  - This is a team rebound, not individual (unless `athlete_id_1` is set)
- **And-1 Situations:** Made field goal + foul = 1 FGA + up to 3 FTA (continuation)
  - Possessiondoes NOT change until free throws complete

---

### 3. REBOUND EVENTS (Box Score: OREB, DREB)

| type_text | Description | Attribution | Box Score Impact |
|-----------|-------------|-------------|------------------|
| `Offensive Rebound` | Offensive rebound | `athlete_id_1` or team | OREB +1 |
| `Defensive Rebound` | Defensive rebound | `athlete_id_1` or team | DREB +1 |

**Text Patterns:**
- **Player rebound:** `"{Player} offensive/defensive rebound"`
  - Example: `"Nikola Vucevic defensive rebound"`
  - Attribution: `athlete_id_1` (player ID)
  - Box Score: Player DREB +1, Team REB +1

- **Team rebound:** `"{Team} offensive/defensive team rebound"`
  - Example: `"Knicks defensive team rebound"`
  - Attribution: `athlete_id_1 = null`
  - Box Score: Team REB +1 (not attributed to individual)

**Possession Impact:**
- **Defensive Rebound:** NEW POSSESSION for rebounding team
- **Offensive Rebound:** EXTENDS current possession (subtract from possession count)

---

### 4. TURNOVER EVENTS (Box Score: TOV)

| type_text | Description | Attribution | Box Score Impact |
|-----------|-------------|-------------|------------------|
| `Bad Pass\nTurnover` | Bad pass turnover | `athlete_id_1` (turnover), `athlete_id_2` (steal) | TOV +1, STL +1 |
| `Lost Ball Turnover` | Lost ball turnover | `athlete_id_1` (turnover), `athlete_id_2` (steal) | TOV +1, STL +1 |
| `Traveling` | Traveling violation | `athlete_id_1` | TOV +1 |
| `Offensive Foul Turnover` | Offensive foul causing turnover | `athlete_id_1` | TOV +1, PF +1 |
| `Shot Clock Turnover` | Shot clock violation | Team turnover | Team TOV +1 |
| `3-Second Turnover` | 3-second violation | `athlete_id_1` | TOV +1 |
| `Lane Violation Turnover` | Lane violation | `athlete_id_1` | TOV +1 |

**Text Patterns:**
- **With steal:** `"{Player} bad pass ({Stealer} steals)"`
  - Example: `"Amar'e Stoudemire lost ball turnover (E'Twaun Moore steals)"`
  - Box Score: Player 1 TOV +1, Player 2 STL +1

- **Without steal:** `"{Player} traveling"`, `"Shot Clock Turnover"`
  - Box Score: TOV +1 (no steal)

**Possession Impact:**
- All turnovers END current possession
- Defensive team gets NEW POSSESSION

---

### 5. FOUL EVENTS (Box Score: PF)

| type_text | Description | Box Score Impact | Possession Impact |
|-----------|-------------|------------------|-------------------|
| `Personal Foul` | Personal foul | PF +1 | No change |
| `Shooting Foul` | Foul during shot attempt | PF +1 | Free throws follow |
| `Offensive Foul` | Offensive foul | PF +1, TOV +1 | Change possession |
| `Offensive Foul Turnover` | Offensive foul (explicit turnover) | PF +1, TOV +1 | Change possession |
| `Loose Ball Foul` | Loose ball foul | PF +1 | Depends on context |
| `Personal Take Foul` | Intentional foul to stop play | PF +1 | Free throws follow |
| `Technical Foul` | Technical foul | PF +1 | No change (FT but no possession change) |
| `Offensive Charge` | Charging foul | PF +1, TOV +1 | Change possession |

**Text Patterns:**
- `"{Fouler} personal foul ({Fouled} draws the foul)"`
- `"{Fouler} shooting foul ({Fouled} draws the foul)"`

**Attribution:**
- `athlete_id_1`: Player committing the foul (PF +1)
- `athlete_id_2`: Player drawing the foul (no box score impact)

---

### 6. ADMINISTRATIVE EVENTS (No Box Score Impact)

| type_text | Purpose |
|-----------|---------|
| `Substitution` | Player enters/leaves game |
| `Full Timeout` | Team timeout |
| `Short Timeout` | 20-second timeout |
| `Official Time Out` | Official/TV timeout |
| `Jump Ball` | Opening tip or jump ball situation |
| `End Period` | End of quarter |
| `End Game` | End of game |
| `Kicked Ball` | Kicked ball violation |
| `Lane` | Lane violation (context-specific) |

**No box score attribution** - used for game flow tracking

---

## Possession Determination Logic

### Possession-Ending Events
1. **Defensive Rebound** → New possession for rebounding team
2. **Turnover** → New possession for defensive team
3. **Made field goal** (unless and-1) → New possession for defensive team
4. **Made free throw** (final in sequence) → New possession for defensive team
5. **End of Period** → Close current possession

### Possession-Extending Events
1. **Offensive Rebound** → Current team keeps possession
2. **Missed free throw 1 of 2** → Automatic offensive rebound, same possession

### Possession-Neutral Events
1. **Fouls** (non-offensive) → Same team keeps possession, free throws follow
2. **Timeouts** → No change
3. **Substitutions** → No change

---

## Parsing Algorithm Pseudocode

```python
def parse_event_to_box_score(event):
    """Parse single play-by-play event into box score statistics."""

    type_text = event['type_text']
    text = event['text']
    athlete_id_1 = event['athlete_id_1']
    athlete_id_2 = event['athlete_id_2']
    scoring_play = event['scoring_play']

    stats = {}

    # SHOT EVENTS
    if is_shot_event(type_text):
        stats[athlete_id_1] = {'fga': 1}

        if 'makes' in text.lower():
            stats[athlete_id_1]['fgm'] = 1

            # Check for 3-pointer
            if 'three point' in text.lower():
                stats[athlete_id_1]['fg3a'] = 1
                stats[athlete_id_1]['fg3m'] = 1
                stats[athlete_id_1]['pts'] = 3
            else:
                stats[athlete_id_1]['pts'] = 2

            # Check for assist
            if 'assists)' in text and athlete_id_2:
                stats[athlete_id_2] = {'ast': 1}

        elif 'misses' in text.lower():
            # Missed shot
            if 'three point' in text.lower():
                stats[athlete_id_1]['fg3a'] = 1

        elif 'blocks' in text.lower() and athlete_id_2:
            # Blocked shot
            stats[athlete_id_2] = {'blk': 1}

    # FREE THROW EVENTS
    elif 'Free Throw' in type_text:
        stats[athlete_id_1] = {'fta': 1}

        if 'makes' in text.lower():
            stats[athlete_id_1]['ftm'] = 1
            stats[athlete_id_1]['pts'] = 1

    # REBOUND EVENTS
    elif type_text in ['Offensive Rebound', 'Defensive Rebound']:
        if athlete_id_1:  # Player rebound
            reb_type = 'oreb' if 'Offensive' in type_text else 'dreb'
            stats[athlete_id_1] = {reb_type: 1, 'reb': 1}
        # else: team rebound, tracked separately

    # TURNOVER EVENTS
    elif 'Turnover' in type_text or type_text in ['Traveling', '3-Second Turnover']:
        stats[athlete_id_1] = {'tov': 1}

        # Check for steal
        if 'steals)' in text and athlete_id_2:
            stats[athlete_id_2] = {'stl': 1}

    # FOUL EVENTS
    elif 'Foul' in type_text:
        stats[athlete_id_1] = {'pf': 1}

        # Offensive fouls are turnovers
        if 'Offensive' in type_text or 'Charge' in type_text:
            stats[athlete_id_1]['tov'] = 1

    return stats
```

---

## Known Edge Cases

### 1. And-1 Situations
**Pattern:** Made shot + Shooting Foul → Free throw(s)
- Shot counts as FGA +1, FGM +1, PTS +2 or +3
- Foul counts as PF +1 for defender
- Free throws count as FTA +1, FTM +1 (if made), PTS +1 (if made)
- **Possession:** Does NOT change until free throws complete

### 2. Team Rebounds
**Pattern:** Rebound with `athlete_id_1 = null`
- Count toward team totals only
- Do NOT attribute to any individual player
- Common after missed free throws (automatic rebound)

### 3. Technical Fouls
- Free throw awarded BUT possession does NOT change
- Shooting team gets 1 FT + keeps possession
- Different from shooting fouls

### 4. Shot Clock Violations
- Team turnover, not individual
- No steal credited
- Rare event

### 5. Goaltending / Basket Interference
- **Not visible in current event types** - may be embedded in "Lane" events
- Needs investigation

---

## Statistics Formulas

### From Box Score Events:
```python
# Points
PTS = (FGM - 3PM) * 2 + 3PM * 3 + FTM

# Total Rebounds
REB = OREB + DREB

# Field Goal Percentage
FG% = FGM / FGA

# Three-Point Percentage
3P% = 3PM / 3PA

# Free Throw Percentage
FT% = FTM / FTA
```

### Advanced Metrics:
```python
# True Shooting %
TS% = PTS / (2 * (FGA + 0.44 * FTA))

# Effective Field Goal %
eFG% = (FGM + 0.5 * 3PM) / FGA

# Possessions (Team)
POSS = FGA + 0.44 * FTA - OREB + TOV
```

---

## Validation Checklist

When comparing computed stats vs Hoopr box scores:

- [ ] **Exact match required:** FGA, FGM, 3PA, 3PM, FTA, FTM, PTS
- [ ] **Allow ±1:** Rebounds (attribution can vary)
- [ ] **Allow ±2:** Assists (subjective)
- [ ] **Investigate:** Turnovers, steals, blocks (should match)

---

**End of Schema Documentation**
