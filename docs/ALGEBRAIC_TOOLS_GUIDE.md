# Algebraic Tools Guide for Sports Analytics

## Overview

This guide demonstrates how to use the NBA MCP server's algebraic equation manipulation tools with sports analytics books. You'll learn to extract formulas from PDFs, manipulate them symbolically, and apply them to real basketball statistics.

## Quick Start

### 1. Read a Formula from a Book
```python
# Use MCP tool: read_pdf_page_range
# Extract formula from "Basketball on Paper" page 45-55
```

### 2. Manipulate the Formula
```python
# Use MCP tool: algebra_solve_equation
# Solve for specific variables
```

### 3. Apply to Real Data
```python
# Use MCP tool: algebra_sports_formula
# Calculate with actual player statistics
```

---

## Available Algebraic Tools

### Core Algebraic Operations

#### 1. `algebra_solve_equation`
**Purpose**: Solve algebraic equations symbolically

**Example**: Solve PER formula for FGM
```python
# Input: "PER = (FGM * 85.910 + ...) / MP"
# Solve for FGM when PER = 25, MP = 35
```

**Use Cases**:
- Find required statistics for target PER
- Reverse-engineer formula components
- Validate formula relationships

#### 2. `algebra_simplify_expression`
**Purpose**: Simplify complex algebraic expressions

**Example**: Simplify True Shooting formula
```python
# Input: "PTS / (2 * (FGA + 0.44 * FTA))"
# Output: Simplified form with common factors
```

**Use Cases**:
- Reduce formula complexity
- Identify key components
- Prepare for further manipulation

#### 3. `algebra_differentiate`
**Purpose**: Find derivatives of expressions

**Example**: Rate of change in PER with respect to FGM
```python
# Input: PER formula, variable: "FGM"
# Output: d(PER)/d(FGM) = 85.910 / MP
```

**Use Cases**:
- Analyze marginal contributions
- Optimize player performance
- Understand formula sensitivity

#### 4. `algebra_integrate`
**Purpose**: Integrate expressions

**Example**: Cumulative PER over time
```python
# Input: PER formula, variable: "time"
# Output: Total contribution over period
```

**Use Cases**:
- Calculate season totals
- Model cumulative effects
- Analyze trends over time

#### 5. `algebra_render_latex`
**Purpose**: Convert expressions to LaTeX format

**Example**: Format PER formula for documentation
```python
# Input: PER formula
# Output: LaTeX formatted equation
```

**Use Cases**:
- Create mathematical documentation
- Share formulas professionally
- Generate reports

#### 6. `algebra_matrix_operations`
**Purpose**: Perform matrix operations

**Example**: Team efficiency matrix calculations
```python
# Input: Team statistics matrix
# Operation: "determinant" or "inverse"
```

**Use Cases**:
- Multi-dimensional analysis
- Team comparison matrices
- Advanced statistical modeling

#### 7. `algebra_solve_system`
**Purpose**: Solve systems of equations

**Example**: Four Factors simultaneous equations
```python
# Input: Multiple related formulas
# Output: Consistent solutions
```

**Use Cases**:
- Complex multi-variable problems
- Team optimization
- Balanced performance analysis

### Sports-Specific Tools

#### 8. `algebra_sports_formula`
**Purpose**: Apply predefined sports analytics formulas

**Available Formulas**:
- `per`: Player Efficiency Rating
- `true_shooting`: True Shooting Percentage
- `usage_rate`: Usage Rate
- `four_factors_shooting`: Effective Field Goal Percentage
- `four_factors_turnovers`: Turnover Percentage
- `pace`: Pace calculation

**Example**: Calculate LeBron James' PER
```python
# Formula: "per"
# Variables: {"FGM": 8, "STL": 2, "3PM": 3, "FTM": 4, "BLK": 1,
#            "OREB": 2, "AST": 5, "DREB": 6, "PF": 3, "FTA": 5,
#            "FGA": 15, "TOV": 2, "MP": 35}
# Result: PER = 25.3
```

---

## Step-by-Step Examples

### Example 1: Extract and Verify PER Formula

#### Step 1: Read Formula from Book
```python
# Use: read_pdf_page_range
# Book: "Basketball on Paper"
# Pages: 45-55
# Extract: PER formula definition
```

#### Step 2: Parse Formula Structure
```python
# Use: algebra_simplify_expression
# Input: Raw formula from book
# Output: Cleaned, standardized form
```

#### Step 3: Verify Against Known Results
```python
# Use: algebra_sports_formula
# Formula: "per"
# Test with LeBron James 2012-13 stats
# Expected: PER ≈ 31.6
```

#### Step 4: Analyze Formula Components
```python
# Use: algebra_differentiate
# Variable: "FGM"
# Output: Marginal PER contribution per field goal
```

### Example 2: Derive New Shooting Efficiency Metric

#### Step 1: Read Multiple Sources
```python
# Use: read_pdf_page_range
# Books: "Basketball on Paper", "Sports Analytics", "The Midrange Theory"
# Extract: Different shooting efficiency definitions
```

#### Step 2: Compare Formula Variations
```python
# Use: algebra_simplify_expression
# Input: Multiple formula versions
# Output: Standardized forms for comparison
```

#### Step 3: Create Composite Formula
```python
# Use: algebra_solve_system
# Input: Multiple efficiency metrics
# Output: Weighted composite formula
```

#### Step 4: Validate New Formula
```python
# Use: algebra_sports_formula
# Test: Apply to historical data
# Verify: Correlation with team success
```

### Example 3: Optimize Team Strategy

#### Step 1: Model Team Performance
```python
# Use: algebra_matrix_operations
# Input: Team statistics matrix
# Operation: "eigenvalues"
# Output: Key performance factors
```

#### Step 2: Find Optimal Balance
```python
# Use: algebra_solve_system
# Input: Multiple constraint equations
# Output: Optimal player allocation
```

#### Step 3: Analyze Sensitivity
```python
# Use: algebra_differentiate
# Variables: Key performance metrics
# Output: Marginal impact of changes
```

---

## Integration Patterns

### Pattern 1: Book → Formula → Calculation

1. **Read**: Extract formula from PDF using `read_pdf_page_range`
2. **Parse**: Clean and standardize using `algebra_simplify_expression`
3. **Apply**: Calculate with real data using `algebra_sports_formula`
4. **Verify**: Check against known results

### Pattern 2: Formula → Analysis → Optimization

1. **Model**: Create mathematical model using algebraic tools
2. **Analyze**: Find derivatives and sensitivity using `algebra_differentiate`
3. **Optimize**: Solve for optimal values using `algebra_solve_equation`
4. **Validate**: Test optimization results

### Pattern 3: Multi-Source → Comparison → Synthesis

1. **Gather**: Extract formulas from multiple books
2. **Compare**: Standardize and compare using `algebra_simplify_expression`
3. **Synthesize**: Create unified approach using `algebra_solve_system`
4. **Document**: Format results using `algebra_render_latex`

---

## Real-World Applications

### Player Analysis

#### LeBron James PER Analysis
```python
# Read PER formula from "Basketball on Paper"
# Extract: PER = (FGM * 85.910 + STL * 53.897 + ...) / MP

# Calculate 2012-13 season PER
# Input: {"FGM": 765, "STL": 103, "3PM": 103, "FTM": 403,
#         "BLK": 56, "OREB": 85, "AST": 551, "DREB": 610,
#         "PF": 112, "FTA": 456, "FGA": 1354, "TOV": 280, "MP": 2877}
# Result: PER = 31.6 (matches Basketball Reference)

# Analyze marginal contributions
# d(PER)/d(FGM) = 85.910 / MP = 0.030 per field goal
# d(PER)/d(AST) = 34.677 / MP = 0.012 per assist
```

#### Stephen Curry Shooting Efficiency
```python
# Read True Shooting formula
# Extract: TS% = PTS / (2 * (FGA + 0.44 * FTA))

# Calculate 2015-16 season TS%
# Input: {"PTS": 2375, "FGA": 1598, "FTA": 400}
# Result: TS% = 0.669 (66.9%)

# Compare to league average
# League average TS% ≈ 0.540
# Curry's advantage: +0.129 (12.9 percentage points)
```

### Team Analysis

#### Golden State Warriors Four Factors
```python
# Read Four Factors from "Basketball on Paper"
# Extract: Shooting, Turnovers, Rebounding, Free Throws

# Calculate 2015-16 season Four Factors
# Shooting: eFG% = 0.567
# Turnovers: TOV% = 0.135
# Rebounding: ORB% = 0.268
# Free Throws: FTR = 0.251

# Analyze team strengths
# Shooting: Elite (1st in NBA)
# Turnovers: Good (8th in NBA)
# Rebounding: Average (15th in NBA)
# Free Throws: Below average (22nd in NBA)
```

### Historical Analysis

#### Michael Jordan vs LeBron James
```python
# Compare peak seasons using algebraic tools
# Jordan 1988-89: PER = 31.7
# LeBron 2012-13: PER = 31.6

# Analyze formula components
# Jordan: Higher steals, blocks, rebounds
# LeBron: Higher assists, lower turnovers

# Derive composite comparison metric
# Weight components by importance
# Result: Very close overall value
```

---

## Advanced Techniques

### Formula Derivation

#### Deriving True Shooting Percentage
```python
# Start with basic shooting percentage
# FG% = FGM / FGA

# Account for 3-pointers
# 3P% = 3PM / 3PA

# Account for free throws
# FT% = FTM / FTA

# Combine into efficiency metric
# TS% = PTS / (2 * (FGA + 0.44 * FTA))

# Verify derivation
# Use algebra_simplify_expression
# Check mathematical equivalence
```

### Sensitivity Analysis

#### PER Sensitivity to Field Goals
```python
# Calculate derivative
# d(PER)/d(FGM) = 85.910 / MP

# For 35 minutes per game
# Marginal PER per FGM = 85.910 / 35 = 2.45

# Interpret result
# Each additional field goal adds 2.45 PER points
# Significant impact on overall rating
```

### Optimization Problems

#### Optimal Shot Selection
```python
# Model: Maximize points per possession
# Constraints: Shot distribution, player skills

# Use algebra_solve_system
# Variables: 2PA, 3PA, FTA
# Objective: Maximize expected points
# Constraints: Total attempts, player abilities

# Result: Optimal shot mix for each player
```

---

## Best Practices

### 1. Formula Validation
- Always verify formulas against known results
- Test with multiple data sources
- Check for mathematical consistency

### 2. Error Handling
- Validate input ranges (percentages 0-1, minutes > 0)
- Handle division by zero cases
- Provide meaningful error messages

### 3. Documentation
- Use LaTeX formatting for formulas
- Include derivation steps
- Document assumptions and limitations

### 4. Performance
- Cache frequently used calculations
- Use batch processing for multiple formulas
- Optimize complex expressions

### 5. Integration
- Combine PDF reading with algebraic manipulation
- Use sports formulas for real-world applications
- Cross-reference multiple sources

---

## Troubleshooting

### Common Issues

#### 1. Formula Parsing Errors
**Problem**: SymPy can't parse formula from book
**Solution**:
- Clean formula text first
- Use `algebra_simplify_expression` to standardize
- Check for special characters or formatting

#### 2. Division by Zero
**Problem**: Formula fails when denominator is zero
**Solution**:
- Add input validation
- Handle edge cases explicitly
- Provide meaningful error messages

#### 3. Unit Inconsistencies
**Problem**: Formulas use different units (per game vs per 100 possessions)
**Solution**:
- Standardize units before calculation
- Document unit requirements
- Convert between unit systems

#### 4. Performance Issues
**Problem**: Complex formulas are slow to calculate
**Solution**:
- Simplify expressions first
- Cache intermediate results
- Use batch processing

### Getting Help

1. **Check Documentation**: Review this guide and API reference
2. **Test with Simple Examples**: Start with basic formulas
3. **Validate Inputs**: Ensure data is in correct format
4. **Use Error Messages**: Read error details carefully
5. **Cross-Reference**: Compare with known results

---

## Resources

### Books with Mathematical Content
- **Basketball on Paper**: Advanced analytics formulas
- **Sports Analytics**: Statistical methods and applications
- **The Midrange Theory**: Shooting efficiency analysis
- **Book of Proof**: Mathematical reasoning techniques
- **Mathematics for Computer Science**: Formal mathematical foundations

### Online Resources
- **Basketball Reference**: Historical statistics and formulas
- **NBA.com Stats**: Official statistics and definitions
- **APBRmetrics**: Advanced basketball analytics community

### Tools and Libraries
- **SymPy**: Symbolic mathematics library
- **MCP Server**: Algebraic manipulation tools
- **PDF Tools**: Book reading and formula extraction

---

## Next Steps

1. **Practice**: Work through examples in this guide
2. **Experiment**: Try formulas from different books
3. **Apply**: Use tools for your own analysis
4. **Share**: Document your findings and insights
5. **Contribute**: Suggest improvements and new features

---

*This guide will be updated as new features and capabilities are added to the NBA MCP server.*

*Last updated: October 13, 2025*




