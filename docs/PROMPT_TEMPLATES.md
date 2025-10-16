# Claude/Gemini Prompt Templates for NBA MCP Server

## Overview

This document provides ready-to-use prompt templates for Claude Desktop, Gemini, and other AI assistants to effectively utilize the NBA MCP server's algebraic equation manipulation tools with sports analytics books.

---

## Core Prompt Templates

### 1. Formula Analysis from Books

**Template**: Analyze Sports Analytics Formula
```
I need you to analyze a sports analytics formula from a basketball book using the NBA MCP server. Here's what I want you to do:

1. **Read the Formula**: Use the MCP tool `read_pdf_page_range` to extract the formula from [BOOK_NAME] pages [PAGE_RANGE]
2. **Parse the Formula**: Use `algebra_simplify_expression` to clean and standardize the formula
3. **Apply to Real Data**: Use `algebra_sports_formula` with [FORMULA_NAME] and these player statistics: [STATS]
4. **Analyze Components**: Use `algebra_differentiate` to find the marginal contribution of [VARIABLE]
5. **Document Results**: Use `algebra_render_latex` to format the formula for documentation

Please provide:
- The extracted formula
- The calculated result
- Analysis of each component's impact
- LaTeX formatted equation
- Any insights about the formula's effectiveness
```

**Example Usage**:
```
Analyze the PER formula from "Basketball on Paper" pages 45-55 using LeBron James' 2012-13 stats: FGM=765, STL=103, 3PM=103, FTM=403, BLK=56, OREB=85, AST=551, DREB=610, PF=112, FTA=456, FGA=1354, TOV=280, MP=2877. Find the marginal contribution of FGM.
```

### 2. Multi-Source Formula Comparison

**Template**: Compare Formula Definitions
```
I want to compare how different basketball analytics books define the same metric. Please:

1. **Extract from Multiple Sources**:
   - Read [FORMULA_NAME] from "Basketball on Paper" pages [PAGES]
   - Read [FORMULA_NAME] from "Sports Analytics" pages [PAGES]
   - Read [FORMULA_NAME] from "The Midrange Theory" pages [PAGES]

2. **Standardize Notation**: Use `algebra_simplify_expression` on each formula
3. **Compare Structures**: Analyze differences in variable definitions and coefficients
4. **Test Consistency**: Apply each version to the same player data: [STATS]
5. **Recommend Best Version**: Suggest which formula to use and why

Provide a detailed comparison table and recommendations.
```

**Example Usage**:
```
Compare True Shooting Percentage definitions from "Basketball on Paper" pages 120-130, "Sports Analytics" pages 45-55, and "The Midrange Theory" pages 80-90. Test with Stephen Curry's 2015-16 stats: PTS=2375, FGA=1598, FTA=400.
```

### 3. Formula Derivation and Verification

**Template**: Derive and Verify Formula
```
Help me derive and verify a sports analytics formula step-by-step:

1. **Read Source Material**: Extract the formula derivation from [BOOK_NAME] pages [PAGES]
2. **Show Each Step**: Use `algebra_simplify_expression` to show each algebraic step
3. **Verify Logic**: Use `algebra_solve_equation` to verify the derivation
4. **Test with Data**: Apply to known player statistics: [STATS]
5. **Cross-Reference**: Compare with Basketball Reference or NBA.com results
6. **Document Process**: Use `algebra_render_latex` for each step

Please show the complete mathematical derivation with explanations.
```

**Example Usage**:
```
Derive the True Shooting Percentage formula from "Basketball on Paper" pages 120-130. Show each algebraic step, verify the logic, and test with LeBron James' career averages: PTS=27.1, FGA=19.4, FTA=7.4 per game.
```

### 4. Optimization Analysis

**Template**: Optimize Player Performance
```
I want to optimize a player's performance using mathematical analysis:

1. **Current Performance**: Calculate current [METRIC] using `algebra_sports_formula`
2. **Sensitivity Analysis**: Use `algebra_differentiate` to find which variables have the biggest impact
3. **Optimization**: Use `algebra_solve_equation` to find optimal values for key variables
4. **Scenario Planning**: Test different improvement scenarios
5. **Recommendations**: Provide specific, actionable advice

Player: [PLAYER_NAME]
Current Stats: [STATS]
Target: Improve [METRIC] by [PERCENTAGE]%

Please provide mathematical analysis and practical recommendations.
```

**Example Usage**:
```
Optimize LeBron James' PER performance. Current stats: FGM=8, STL=2, 3PM=3, FTM=4, BLK=1, OREB=2, AST=5, DREB=6, PF=3, FTA=5, FGA=15, TOV=2, MP=35. Target: Improve PER by 10%.
```

### 5. Team Strategy Analysis

**Template**: Analyze Team Strategy Mathematically
```
Help me analyze team strategy using mathematical models:

1. **Team Metrics**: Calculate team efficiency using `algebra_sports_formula` with [TEAM_STATS]
2. **Player Contributions**: Analyze each player's impact using `algebra_differentiate`
3. **Lineup Optimization**: Use `algebra_solve_system` to find optimal player combinations
4. **Scenario Analysis**: Test different strategic approaches
5. **Recommendations**: Provide data-driven strategic advice

Team: [TEAM_NAME]
Current Roster: [PLAYER_LIST]
Strategy Focus: [FOCUS_AREA] (e.g., shooting, defense, pace)

Please provide mathematical analysis and strategic recommendations.
```

**Example Usage**:
```
Analyze the Golden State Warriors' 2015-16 strategy mathematically. Focus on shooting efficiency. Current team stats: PTS=114.9, FGA=87.2, FTA=24.1, 3PM=13.1, Pace=99.3. Key players: Curry, Thompson, Green, Barnes, Bogut.
```

---

## Advanced Prompt Templates

### 6. Historical Analysis

**Template**: Historical Performance Analysis
```
Conduct a historical analysis of basketball performance metrics:

1. **Era Comparison**: Compare [METRIC] across different NBA eras
2. **Statistical Significance**: Use `algebra_solve_equation` to test for significant differences
3. **Trend Analysis**: Analyze how [METRIC] has evolved over time
4. **Context Adjustment**: Adjust for era-specific factors (pace, rules, etc.)
5. **Predictions**: Use mathematical models to predict future trends

Metrics to Analyze: [METRIC_LIST]
Time Periods: [ERA_LIST]
Key Players: [PLAYER_LIST]

Please provide comprehensive historical analysis with mathematical backing.
```

### 7. Custom Formula Development

**Template**: Develop Custom Analytics Formula
```
Help me develop a custom basketball analytics formula:

1. **Problem Definition**: Define what we're trying to measure
2. **Literature Review**: Extract relevant formulas from [BOOK_LIST]
3. **Mathematical Framework**: Use `algebra_solve_equation` to derive the formula
4. **Validation**: Test against known results using `algebra_sports_formula`
5. **Documentation**: Use `algebra_render_latex` to document the formula

Goal: [ANALYTICS_GOAL]
Constraints: [CONSTRAINTS]
Data Available: [DATA_TYPES]

Please develop and validate a new analytics formula.
```

### 8. Machine Learning Integration

**Template**: Integrate Formulas with ML
```
Help me integrate sports analytics formulas with machine learning:

1. **Feature Engineering**: Use `algebra_sports_formula` to create derived features
2. **Model Validation**: Test formula-based features against ML models
3. **Performance Metrics**: Use `algebra_differentiate` to analyze feature importance
4. **Optimization**: Use `algebra_solve_equation` to optimize model parameters
5. **Interpretability**: Explain ML results using basketball analytics

ML Task: [TASK] (e.g., player ranking, team success prediction)
Formulas to Use: [FORMULA_LIST]
Data: [DATASET_DESCRIPTION]

Please provide ML integration analysis with basketball context.
```

---

## Specialized Use Cases

### 9. Draft Analysis

**Template**: Draft Prospect Analysis
```
Analyze NBA draft prospects using advanced metrics:

1. **College Translation**: Use `algebra_sports_formula` to project college stats to NBA
2. **Comparable Players**: Find similar prospects using formula-based comparisons
3. **Upside Analysis**: Use `algebra_differentiate` to identify high-potential variables
4. **Risk Assessment**: Analyze potential failure modes
5. **Draft Recommendations**: Provide ranking and fit analysis

Prospects: [PROSPECT_LIST]
College Stats: [STATS]
NBA Projections: [PROJECTIONS]

Please provide comprehensive draft analysis.
```

### 10. Injury Impact Analysis

**Template**: Analyze Injury Impact
```
Analyze the impact of injuries on team performance:

1. **Baseline Performance**: Calculate team metrics before injury
2. **Injury Impact**: Use `algebra_solve_equation` to quantify performance loss
3. **Replacement Analysis**: Evaluate replacement player contributions
4. **Recovery Projections**: Use `algebra_differentiate` to model recovery curves
5. **Strategic Adjustments**: Recommend tactical changes

Injured Player: [PLAYER_NAME]
Injury Type: [INJURY_TYPE]
Team Context: [TEAM_INFO]

Please provide injury impact analysis and recommendations.
```

---

## Quick Reference Prompts

### Formula Extraction
```
Extract the [FORMULA_NAME] formula from [BOOK_NAME] pages [PAGES] and calculate it for [PLAYER_NAME] with stats: [STATS]
```

### Formula Comparison
```
Compare [FORMULA_NAME] definitions from [BOOK1] and [BOOK2], test with [PLAYER_NAME] stats: [STATS]
```

### Performance Analysis
```
Analyze [PLAYER_NAME]'s [METRIC] performance using [FORMULA_NAME] with stats: [STATS]
```

### Optimization
```
Optimize [PLAYER_NAME]'s [METRIC] by improving [VARIABLE] from [CURRENT] to [TARGET]
```

### Team Analysis
```
Analyze [TEAM_NAME]'s [STRATEGY] using [FORMULA_LIST] with team stats: [STATS]
```

---

## Best Practices

### 1. Always Specify Context
- Include book names and page ranges
- Provide complete player/team statistics
- Specify the analytical goal

### 2. Use Step-by-Step Approach
- Break complex analyses into steps
- Validate each step before proceeding
- Document intermediate results

### 3. Cross-Reference Results
- Compare with known sources (Basketball Reference, NBA.com)
- Validate formula accuracy
- Check for logical consistency

### 4. Provide Actionable Insights
- Translate mathematical results into basketball terms
- Give specific recommendations
- Explain the practical implications

### 5. Document Everything
- Use LaTeX formatting for formulas
- Include all calculations
- Provide clear explanations

---

## Common Variables Reference

### Player Statistics
- **FGM/FGA**: Field Goals Made/Attempted
- **FTM/FTA**: Free Throws Made/Attempted
- **3PM/3PA**: 3-Pointers Made/Attempted
- **PTS**: Points Scored
- **REB**: Rebounds (OREB/DREB)
- **AST**: Assists
- **STL**: Steals
- **BLK**: Blocks
- **TOV**: Turnovers
- **PF**: Personal Fouls
- **MP**: Minutes Played

### Team Statistics
- **TM_**: Team prefix (TM_FGA, TM_PTS, etc.)
- **OPP_**: Opponent prefix (OPP_PTS, OPP_POSS, etc.)
- **PACE**: Team pace
- **POSS**: Possessions
- **ORtg/DRtg**: Offensive/Defensive Rating

### Advanced Metrics
- **PER**: Player Efficiency Rating
- **TS%**: True Shooting Percentage
- **USG%**: Usage Rate
- **BPM**: Box Plus/Minus
- **VORP**: Value Over Replacement Player
- **WS**: Win Shares

---

## Troubleshooting

### Common Issues
1. **Formula Not Found**: Check book name and page range
2. **Missing Variables**: Ensure all required stats are provided
3. **Invalid Results**: Check for data entry errors
4. **Calculation Errors**: Verify formula implementation

### Error Messages
- **"Unknown formula"**: Check formula name spelling
- **"Validation error"**: Check input ranges and types
- **"Parse error"**: Verify formula syntax
- **"Division by zero"**: Check for zero denominators

### Getting Help
1. Check the Algebraic Tools Guide
2. Verify input data accuracy
3. Test with known examples
4. Use simpler formulas first

---

*These templates provide a comprehensive framework for using the NBA MCP server's algebraic tools effectively with sports analytics books.*

*Last updated: October 13, 2025*




