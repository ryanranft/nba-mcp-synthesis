# NBA MCP Synthesis - Future Work Roadmap

**Created:** 2025-11-07
**Status:** Planning / Ready for Implementation
**Database:** Local PostgreSQL (after migration from RDS)

---

## Overview

This document tracks deferred analytics and modeling work to be implemented after completing the local PostgreSQL database migration. All items are organized by priority and estimated complexity.

---

## Current Status (As of 2025-11-07)

### Completed
- ✅ Shot zone classification (100% coverage, 6.16M shots)
- ✅ Spatial analytics infrastructure
- ✅ Play-by-play data backfill
- ✅ Database schema design (RDS)

### In Progress
- 🟡 Local PostgreSQL database setup
- 🟡 RDS → Local migration
- 🟡 Historical data import (1993-2025)

### Planned
- All items in this roadmap

---

## Priority 1: Shot Zone Analytics Integration (3-5 weeks)

### Context
Shot zone data is fully classified and ready for use, but **not yet integrated into betting models**. This represents the highest-value opportunity for immediate ROI improvement.

### Phase 1A: Basic Zone Features (1 week)
**Status:** Ready to implement
**Complexity:** Low
**Impact:** High (+3-5% accuracy, +2-3% ROI)

**Deliverables:**
1. `ShotZoneFeatureExtractor` class
   - Zone efficiency by team (FG% by zone for L10 games)
   - Shot distribution (% of attempts by zone)
   - Expected value by zone
   - Defensive zone ratings (opponent FG% by zone)

2. Integration with `FeatureExtractor`
   - Add zone features to betting model pipeline
   - Follow existing pattern (rest, player features)
   - Prefix: `zone__home_fg_pct_restricted_area_l10`

3. Model retraining
   - Regenerate features for 2021-2025 seasons
   - Train new ensemble (LR + RF + XGBoost)
   - A/B test old vs new model

**Expected Results:**
- +30 new features
- Query time: <200ms per game
- Accuracy improvement: +3-5%
- Edge detection: +25% more profitable bets

**Files to Create:**
- `mcp_server/betting/feature_extractors/shot_zone_features.py` (~350 lines)
- `tests/unit/test_shot_zone_features.py` (~200 lines)

**Files to Modify:**
- `mcp_server/betting/feature_extractor.py` (+12 lines)
- `mcp_server/betting/feature_extractors/__init__.py` (+1 line)

### Phase 1B: Advanced Zone Analytics (2 weeks)
**Status:** Dependent on Phase 1A
**Complexity:** Medium
**Impact:** Medium (+1-2% additional accuracy)

**Deliverables:**
1. Shot quality scoring
   - Weighted by zone expected value
   - Compare team shot selection quality
   - High-EV shot % (restricted area + corner 3s)

2. Matchup-specific zone features
   - Paint mismatch score (offense vs defense)
   - Perimeter mismatch score
   - Zone exploitation index

3. Player-level zone integration
   - Impact of star player absence on zone efficiency
   - Lineup-specific zone performance
   - Backup vs starter zone drops

4. Defensive scheme detection
   - Identify zone defense patterns
   - Rim protection metrics
   - Perimeter defense quality

**Expected Results:**
- +15-20 additional features
- Matchup edge detection improved
- Better handling of injuries/lineup changes

### Phase 2: Pre-Computed Zone Stats (2 weeks, optional)
**Status:** Performance optimization
**Complexity:** Medium-High
**Impact:** Performance only (no accuracy gain)

**Deliverables:**
1. `team_zone_stats` aggregation table
2. Daily recomputation script
3. Modified extractor to use pre-computed data

**When to Implement:**
- If Phase 1A feature extraction >500ms per game
- If real-time predictions are needed (<100ms)

**Storage:** ~500MB for 23 seasons

---

## Priority 2: Play-by-Play Feature Engineering (4-6 weeks)

### Context
Play-by-play data contains rich information beyond shooting: assists, turnovers, rebounds, substitutions. Extracting these features can improve game flow understanding and momentum detection.

### 2.1: Assist Networks (1 week)
**Complexity:** Medium
**Impact:** Medium

**Features:**
- Assist rate by player/team
- Passing patterns (who assists whom)
- Unassisted shot rates
- Ball movement metrics

**Use Cases:**
- Detect teams with strong ball movement
- Impact of playmaker injuries
- Lineup synergy analysis

### 2.2: Turnover Analysis (1 week)
**Complexity:** Low
**Impact:** Medium

**Features:**
- Turnover rate by type (bad pass, traveling, offensive foul)
- Pressure-induced turnovers (late shot clock)
- Team turnover forcing ability
- Turnover points allowed/gained

**Use Cases:**
- Identify high-pressure defensive teams
- Detect sloppy offensive teams
- Matchup edges in turnover battles

### 2.3: Rebounding Patterns (1-2 weeks)
**Complexity:** Medium
**Impact:** Medium

**Features:**
- Offensive rebound rate by zone
- Contested vs uncontested rebounds
- Second-chance points
- Rebounding matchup advantages

**Use Cases:**
- Predict possessions per game
- Size mismatch detection
- Pace of play adjustments

### 2.4: Substitution Analysis (1-2 weeks)
**Complexity:** High
**Impact:** Low-Medium

**Features:**
- Lineup net rating
- Bench impact (starter vs backup drops)
- Rotation patterns
- Fatigue indicators

**Use Cases:**
- Lineup-specific predictions
- Back-to-back game adjustments
- Playoff rotation tightening

---

## Priority 3: Real-Time Integration (6-8 weeks)

### Context
Enable live betting by integrating shot zone analytics and play-by-play features into real-time game streams.

### 3.1: Live Data Ingestion (2 weeks)
**Complexity:** High
**Impact:** High (for live betting only)

**Deliverables:**
- ESPN live API integration
- Play-by-play stream parser
- Real-time database updates
- WebSocket server for dashboards

**Challenges:**
- API rate limits
- Data latency (5-10 second delay)
- Error handling for incomplete data

### 3.2: Live Shot Zone Classification (1 week)
**Complexity:** Low
**Impact:** High (for live betting)

**Deliverables:**
- Real-time shot zone classification
- Running zone efficiency updates
- Live matchup score calculation

**Performance Target:** <100ms classification per shot

### 3.3: In-Game Betting Adjustments (2-3 weeks)
**Complexity:** High
**Impact:** High (for live betting)

**Features:**
- Momentum detection (scoring runs)
- Live spread adjustment
- Over/under recalculation
- Injury impact detection

**Challenges:**
- Model retraining for in-game predictions
- Handling partial game state
- Real-time feature extraction

### 3.4: Live Dashboards (2 weeks)
**Complexity:** Medium
**Impact:** Medium

**Deliverables:**
- Real-time shot charts
- Zone efficiency heatmaps
- Live momentum indicators
- Betting edge visualizations

**Tech Stack:** React + WebSocket + D3.js

---

## Priority 4: Model Enhancements (4-6 weeks)

### Context
Expand betting model capabilities beyond game outcome prediction.

### 4.1: Spread Predictions (2 weeks)
**Complexity:** Medium
**Impact:** High

**Deliverables:**
- Point spread prediction model
- Confidence intervals
- Against-the-spread (ATS) tracking
- Value bet detection

**Expected Results:**
- 52-55% ATS accuracy (target: beat market)
- Identify 3-5 value spreads per night

### 4.2: Totals (Over/Under) Predictions (2 weeks)
**Complexity:** Medium
**Impact:** High

**Deliverables:**
- Total points prediction model
- Pace-adjusted scoring
- Zone-based scoring projections
- Over/under value detection

**Features:**
- Team pace metrics
- Defensive zone ratings
- Recent scoring trends
- Venue factors (altitude, arena)

### 4.3: Player Prop Betting (3-4 weeks)
**Complexity:** High
**Impact:** Medium-High

**Deliverables:**
- Player points/rebounds/assists predictions
- Zone-based player modeling
- Matchup-specific projections
- Prop bet value detection

**Challenges:**
- Player-level data sparsity
- Injury uncertainty
- Minutes projection

### 4.4: Deep Learning on Heatmaps (4-6 weeks)
**Complexity:** Very High
**Impact:** Research / Long-term

**Approach:**
- CNN on shot chart heatmaps
- Spatial attention mechanisms
- Transfer learning from computer vision

**Research Questions:**
- Can CNNs detect defensive schemes from heatmaps?
- Spatial feature extraction vs engineered zone features
- Interpretability of learned features

---

## Priority 5: Data Quality & Monitoring (2-3 weeks)

### Context
Ensure data integrity and detect issues early.

### 5.1: Automated Data Quality Checks (1 week)
**Complexity:** Low
**Impact:** Medium

**Deliverables:**
- Daily validation scripts
- Missing game detection
- Coordinate validation (shot locations)
- Foreign key integrity checks
- Anomaly detection (statistical outliers)

**Alerts:**
- Email/SMS on data quality failures
- Slack integration
- Dashboard warnings

### 5.2: Historical Data Validation (1 week)
**Complexity:** Low
**Impact:** Low

**Deliverables:**
- Cross-reference with basketball-reference.com
- Validate box score totals
- Detect scoring discrepancies
- Era-specific data quality reports

**Focus:**
- Pre-2010 data (lower quality)
- Playoff games (higher importance)
- Shot coordinates (ESPN accuracy)

### 5.3: Continuous Monitoring Dashboard (1 week)
**Complexity:** Medium
**Impact:** Medium

**Metrics:**
- Database size growth
- Query performance trends
- Model accuracy over time
- Betting ROI tracking
- Data freshness (last update)

**Tech Stack:** Grafana + PostgreSQL + Prometheus

---

## Priority 6: Advanced Analytics (8-12 weeks)

### Context
Research-oriented analytics for long-term competitive advantage.

### 6.1: Possession-Based Modeling (3-4 weeks)
**Complexity:** High
**Impact:** Medium

**Approach:**
- Parse possession boundaries from PBP
- Model possession outcomes (points per possession)
- Pace-adjusted predictions
- Four factors framework (shooting, turnovers, rebounding, FTs)

### 6.2: Lineup-Specific Predictions (3-4 weeks)
**Complexity:** Very High
**Impact:** Medium

**Approach:**
- 5-man lineup net ratings
- Opponent lineup matchups
- Synergy detection (player combinations)
- Rotation prediction

**Challenges:**
- Sample size (many lineups have <10 possessions)
- Injury substitutions
- Playoff rotation changes

### 6.3: Coaching Impact Analysis (2-3 weeks)
**Complexity:** Medium
**Impact:** Low-Medium

**Research Questions:**
- Coaching adjustments after timeouts
- In-game strategy (zone vs man defense)
- Rotation optimization
- Playoff coaching differences

**Methods:**
- Causal inference (difference-in-differences)
- Before/after timeout analysis
- Coach fixed effects

### 6.4: Referee Bias Detection (1-2 weeks)
**Complexity:** Medium
**Impact:** Low

**Research Questions:**
- Home team foul call advantage
- Referee tendencies (tight vs loose)
- Star player treatment
- Game timing effects (end of close games)

**Methods:**
- Mixed effects models (referee random effects)
- Foul rate analysis by game state
- Historical referee data

---

## Timeline Overview

### Short-Term (Next 3 months)
1. **Month 1:** Local database setup + Shot zone integration (Phase 1A)
2. **Month 2:** Advanced zone analytics (Phase 1B) + Turnover/assist features
3. **Month 3:** Model enhancements (spreads, totals)

### Medium-Term (Months 4-6)
4. **Month 4:** Real-time integration (live data ingestion)
5. **Month 5:** Live betting models + dashboards
6. **Month 6:** Player props + deep learning research

### Long-Term (6-12 months)
7. **Months 7-9:** Advanced analytics (possessions, lineups, coaching)
8. **Months 10-12:** Productionization, optimization, scaling

---

## Dependencies

### Blocker: Local PostgreSQL Setup
**Status:** In progress
**Blocks:** All priorities

**Must complete before starting analytics work:**
- Docker Compose PostgreSQL
- Schema creation (espn + hoopr)
- Data loading (schedule, box scores, PBP)
- RDS migration
- Validation

**ETA:** 3-4 weeks

### Infrastructure Requirements

**For All Priorities:**
- Local PostgreSQL (25-30GB)
- Python 3.11+ with pandas, numpy, scikit-learn
- Git + version control

**For Real-Time Integration (Priority 3):**
- WebSocket server (Socket.IO or similar)
- Redis for caching
- React frontend

**For Deep Learning (Priority 4.4):**
- PyTorch or TensorFlow
- GPU (optional but recommended)
- 16GB+ RAM for training

---

## Success Metrics

### Betting Model Performance
| Metric | Current | Target | Priority 1 | Priority 2 | Priority 3-4 |
|--------|---------|--------|------------|------------|--------------|
| Accuracy (moneyline) | 58-62% | 65%+ | 61-65% | 63-66% | 65-68% |
| ROI (Kelly criterion) | 6-8% | 12%+ | 8-11% | 10-13% | 12-15% |
| Edge detection (5%+) | 8-12% games | 20%+ | 12-15% | 15-18% | 20-25% |
| AUC | 0.68 | 0.75+ | 0.71 | 0.73 | 0.75 |

### Data Quality
| Metric | Target |
|--------|--------|
| Classification coverage | 100% (achieved) |
| Data freshness | <24 hours |
| Query performance | <500ms for features |
| Uptime | 99.5%+ |

### Development Velocity
| Metric | Target |
|--------|--------|
| Time to production (new feature) | <2 weeks |
| Test coverage | 80%+ |
| Documentation | All public APIs |
| Code review turnaround | <24 hours |

---

## Open Questions

1. **Shot quality vs shot outcome:** Should we weight zone efficiency by shot quality (e.g., contested vs open)?
2. **Sample size:** How many games needed for reliable zone statistics? L10? L20?
3. **Opponent adjustment:** Should zone efficiency be opponent-adjusted (vs league average defense)?
4. **Playoff vs regular season:** Different models or adjust features?
5. **Live betting latency:** What's acceptable delay for live predictions? <1 second? <5 seconds?
6. **Deep learning interpretability:** How to explain CNN predictions to build trust?
7. **Player props sample size:** Minimum games played to offer player prop predictions?
8. **Referee data:** Where to source reliable referee assignment and stats?

---

## Resources & References

### Documentation
- Shot zone indexing: `docs/SHOT_ZONE_INDEXING.md`
- Database architecture: `docs/DATABASE_ARCHITECTURE.md` (to be created)
- Calibration guide: `docs/CALIBRATION_TRAINING_GUIDE.md`

### Code Modules
- Shot analytics: `mcp_server/analytics/shot_zones.py`
- Zone classifier: `mcp_server/spatial/zone_classifier.py`
- Feature extraction: `mcp_server/betting/feature_extractor.py`
- Betting models: `mcp_server/betting/models.py`

### External Resources
- NBA Stats API: https://stats.nba.com/
- Basketball Reference: https://www.basketball-reference.com/
- Cleaning the Glass: https://cleaningtheglass.com/
- Second Spectrum (tracking data): https://www.secondspectrum.com/

---

## Notes

- **Prioritization:** Focus on high-impact, low-complexity items first
- **Validation:** Always A/B test new features against baseline
- **Incremental:** Ship small, test, iterate
- **Documentation:** Update this roadmap as priorities shift
- **Cost management:** Monitor AWS/cloud costs as data grows

---

**Last Updated:** 2025-11-07
**Owner:** nba-mcp-synthesis team
**Status:** Living document (update quarterly)
