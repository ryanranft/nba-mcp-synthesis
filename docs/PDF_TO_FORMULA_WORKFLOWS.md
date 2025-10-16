# Step-by-Step PDF to Formula Workflows
## NBA MCP Server - Complete PDF Analysis Guide

**Date:** October 13, 2025
**Version:** 1.0
**Status:** Complete PDF Analysis Workflows

---

## 🎯 **Overview**

This guide provides step-by-step workflows for extracting, analyzing, and manipulating formulas from sports analytics PDFs using the NBA MCP Server. Each workflow demonstrates the complete process from PDF reading to formula implementation.

---

## 📚 **Available Books**

### 1. Basketball on Paper (Dean Oliver, 2004)
- **S3 Path**: `books/basketball-on-paper.pdf`
- **Focus**: Foundational basketball analytics
- **Key Chapters**: PER (p.85), Four Factors (p.95), Pace (p.120)

### 2. Sports Analytics (Various Authors, 2020)
- **S3 Path**: `books/sports-analytics.pdf`
- **Focus**: Modern advanced metrics
- **Key Chapters**: Win Shares (p.200), VORP (p.250), BPM (p.300)

### 3. The Midrange Theory (Modern Analytics, 2023)
- **S3 Path**: `books/the-midrange-theory.pdf`
- **Focus**: Contemporary basketball analysis
- **Key Chapters**: Net Rating (p.150), Efficiency (p.180), Clutch (p.220)

---

## 🔧 **Workflow Tools Overview**

### Phase 1: PDF Reading
- `read_pdf_page` - Read specific pages
- `read_pdf_page_range` - Read multiple pages
- `search_pdf` - Search for specific terms
- `get_pdf_metadata` - Get book information

### Phase 2: Formula Extraction
- `formula_extract_from_pdf` - Extract formulas from pages
- `formula_convert_latex` - Convert LaTeX to SymPy
- `formula_analyze_structure` - Analyze formula structure
- `formula_map_variables_extracted` - Map extracted variables

### Phase 3: Formula Analysis
- `formula_analyze` - Analyze formula structure and type
- `formula_suggest_tools` - Get tool recommendations
- `formula_map_variables` - Map variables to sports stats
- `formula_validate_units` - Validate units and dimensions

### Phase 4: Interactive Analysis
- `formula_playground_create_session` - Create analysis session
- `formula_playground_add_formula` - Add formula to session
- `formula_playground_update_variables` - Update with real data
- `formula_playground_calculate` - Calculate results
- `formula_playground_visualize` - Generate visualizations

### Phase 5: Validation & Comparison
- `formula_validate_comprehensive` - Comprehensive validation
- `formula_compare_versions` - Compare across sources
- `formula_get_recommendations` - Get usage recommendations

---

## 🚀 **Workflow 1: PER Analysis from Basketball on Paper**

### Step 1: Read the PER Chapter
```python
# Read page 85 where PER is explained
result = await mcp_nba_mcp_server_read_pdf_page({
    "book_path": "books/basketball-on-paper.pdf",
    "page_number": 85,
    "format": "text"
})

print("PER Chapter Content:")
print(result['content'][:500] + "...")
```

### Step 2: Search for PER Formula
```python
# Search for PER formula specifically
result = await mcp_nba_mcp_server_search_pdf({
    "book_path": "books/basketball-on-paper.pdf",
    "query": "PER formula calculation",
    "context_chars": 200
})

print("PER Formula Search Results:")
for match in result['matches']:
    print(f"Page {match['page']}: {match['context']}")
```

### Step 3: Extract PER Formula
```python
# Extract PER formula from the page
result = await formula_extract_from_pdf({
    "book_path": "books/basketball-on-paper.pdf",
    "page_number": 85,
    "formula_patterns": ["PER", "efficiency", "rating", "calculation"]
})

print("Extracted PER Formula:")
print(f"Formula: {result['formula']}")
print(f"Variables: {result['variables']}")
print(f"Confidence: {result['confidence']}")
```

### Step 4: Analyze Formula Structure
```python
# Analyze the extracted PER formula
result = await formula_analyze({
    "formula": result['formula']
})

print("PER Formula Analysis:")
print(f"Formula Type: {result['formula_type']}")
print(f"Complexity: {result['complexity']}")
print(f"Variables: {result['variables']}")
print(f"Operations: {result['operations']}")
```

### Step 5: Get Tool Recommendations
```python
# Get recommendations for PER analysis
result = await formula_suggest_tools({
    "formula": result['formula'],
    "context": "player efficiency analysis"
})

print("Recommended Tools:")
for tool in result['recommended_tools']:
    print(f"- {tool['tool_name']}: {tool['reason']}")
```

### Step 6: Create Interactive Session
```python
# Create playground session for PER experimentation
result = await formula_playground_create_session({
    "session_name": "PER Analysis - Basketball on Paper",
    "description": "Analyzing Player Efficiency Rating from Dean Oliver's book"
})

session_id = result['session_id']
print(f"Created session: {session_id}")
```

### Step 7: Add PER Formula to Session
```python
# Add PER formula to playground
result = await formula_playground_add_formula({
    "session_id": session_id,
    "formula_name": "PER_Oliver",
    "formula": result['formula'],
    "description": "Original PER formula from Basketball on Paper"
})

print(f"Added formula: {result['formula_id']}")
```

### Step 8: Update with Player Data
```python
# Update variables with actual player data (LeBron James example)
result = await formula_playground_update_variables({
    "session_id": session_id,
    "variables": {
        "FGM": 10.2, "STL": 1.2, "3PM": 2.1, "FTM": 5.8, "BLK": 0.6,
        "OREB": 1.2, "AST": 6.8, "DREB": 6.2, "PF": 1.8, "FTA": 7.1,
        "FGA": 19.4, "TOV": 3.5, "MP": 35.5
    }
})

print("Updated variables with LeBron James 2023-24 stats")
```

### Step 9: Calculate PER
```python
# Calculate PER for the player
result = await formula_playground_calculate({
    "session_id": session_id
})

print("PER Calculation Results:")
for formula_result in result['results']:
    print(f"{formula_result['formula_name']}: {formula_result['result']}")
```

### Step 10: Generate Visualization
```python
# Create visualization of PER components
result = await formula_playground_visualize({
    "session_id": session_id,
    "visualization_type": "bar_chart",
    "title": "PER Component Breakdown - LeBron James",
    "x_label": "Components",
    "y_label": "Value"
})

print(f"Generated visualization: {result['visualization_url']}")
```

### Step 11: Validate Formula
```python
# Validate PER formula against known results
result = await formula_validate_comprehensive({
    "formula": result['formula'],
    "formula_id": "per",
    "test_data": {
        "FGM": 10.2, "STL": 1.2, "3PM": 2.1, "FTM": 5.8, "BLK": 0.6,
        "OREB": 1.2, "AST": 6.8, "DREB": 6.2, "PF": 1.8, "FTA": 7.1,
        "FGA": 19.4, "TOV": 3.5, "MP": 35.5
    },
    "validation_types": ["mathematical", "accuracy", "consistency"]
})

print("PER Validation Results:")
print(f"Mathematical: {result['mathematical_valid']}")
print(f"Accuracy: {result['accuracy_valid']}")
print(f"Consistency: {result['consistency_valid']}")
```

---

## 🚀 **Workflow 2: True Shooting Percentage Comparison**

### Step 1: Extract TS% from Multiple Sources
```python
# Extract TS% from Basketball on Paper
ts_oliver = await formula_extract_from_pdf({
    "book_path": "books/basketball-on-paper.pdf",
    "page_number": 120,
    "formula_patterns": ["true shooting", "TS%", "shooting efficiency"]
})

# Extract TS% from Sports Analytics
ts_modern = await formula_extract_from_pdf({
    "book_path": "books/sports-analytics.pdf",
    "page_number": 150,
    "formula_patterns": ["true shooting", "TS%", "shooting efficiency"]
})

print("TS% Formulas Extracted:")
print(f"Oliver: {ts_oliver['formula']}")
print(f"Modern: {ts_modern['formula']}")
```

### Step 2: Create Comparison Session
```python
# Create session to compare TS% formulas
result = await formula_playground_create_session({
    "session_name": "TS% Formula Comparison",
    "description": "Comparing True Shooting Percentage formulas across sources"
})

session_id = result['session_id']
```

### Step 3: Add Both TS% Versions
```python
# Add Basketball on Paper version
await formula_playground_add_formula({
    "session_id": session_id,
    "formula_name": "TS%_Oliver",
    "formula": ts_oliver['formula'],
    "description": "TS% from Basketball on Paper (Dean Oliver)"
})

# Add Sports Analytics version
await formula_playground_add_formula({
    "session_id": session_id,
    "formula_name": "TS%_Modern",
    "formula": ts_modern['formula'],
    "description": "TS% from Sports Analytics (Modern)"
})
```

### Step 4: Update with Player Data
```python
# Update with Stephen Curry 2023-24 stats
await formula_playground_update_variables({
    "session_id": session_id,
    "variables": {
        "PTS": 26.4, "FGA": 19.4, "FTA": 4.8  # Curry's stats
    }
})
```

### Step 5: Calculate Both Versions
```python
# Calculate both TS% versions
result = await formula_playground_calculate({
    "session_id": session_id
})

print("TS% Comparison Results:")
for formula_result in result['results']:
    print(f"{formula_result['formula_name']}: {formula_result['result']}")
```

### Step 6: Create Comparison Visualization
```python
# Create comparison chart
result = await formula_playground_visualize({
    "session_id": session_id,
    "visualization_type": "comparison_chart",
    "title": "TS% Formula Comparison - Stephen Curry",
    "x_label": "Formula Version",
    "y_label": "TS%"
})
```

---

## 🚀 **Workflow 3: Four Factors Analysis**

### Step 1: Read Four Factors Chapter
```python
# Read Four Factors chapter from Basketball on Paper
result = await mcp_nba_mcp_server_read_pdf_page({
    "book_path": "books/basketball-on-paper.pdf",
    "page_number": 95,
    "format": "text"
})

print("Four Factors Chapter:")
print(result['content'][:800] + "...")
```

### Step 2: Extract All Four Factors
```python
# Extract shooting factor (eFG%)
shooting = await formula_extract_from_pdf({
    "book_path": "books/basketball-on-paper.pdf",
    "page_number": 95,
    "formula_patterns": ["shooting", "eFG%", "effective field goal"]
})

# Extract turnover factor
turnovers = await formula_extract_from_pdf({
    "book_path": "books/basketball-on-paper.pdf",
    "page_number": 95,
    "formula_patterns": ["turnover", "TOV%", "turnovers"]
})

# Extract rebounding factor
rebounding = await formula_extract_from_pdf({
    "book_path": "books/basketball-on-paper.pdf",
    "page_number": 95,
    "formula_patterns": ["rebounding", "OREB%", "offensive rebound"]
})

# Extract free throw factor
free_throws = await formula_extract_from_pdf({
    "book_path": "books/basketball-on-paper.pdf",
    "page_number": 95,
    "formula_patterns": ["free throw", "FTR", "free throw rate"]
})

print("Four Factors Extracted:")
print(f"Shooting: {shooting['formula']}")
print(f"Turnovers: {turnovers['formula']}")
print(f"Rebounding: {rebounding['formula']}")
print(f"Free Throws: {free_throws['formula']}")
```

### Step 3: Create Four Factors Dashboard
```python
# Create comprehensive Four Factors session
result = await formula_playground_create_session({
    "session_name": "Four Factors Dashboard",
    "description": "Complete Four Factors analysis from Basketball on Paper"
})

session_id = result['session_id']
```

### Step 4: Add All Four Factors
```python
# Add all four factors to session
factors = [
    {"name": "Shooting", "formula": shooting['formula'], "desc": "Effective Field Goal Percentage"},
    {"name": "Turnovers", "formula": turnovers['formula'], "desc": "Turnover Percentage"},
    {"name": "Rebounding", "formula": rebounding['formula'], "desc": "Offensive Rebound Percentage"},
    {"name": "Free_Throws", "formula": free_throws['formula'], "desc": "Free Throw Rate"}
]

for factor in factors:
    await formula_playground_add_formula({
        "session_id": session_id,
        "formula_name": factor["name"],
        "formula": factor["formula"],
        "description": factor["desc"]
    })
```

### Step 5: Update with Team Data
```python
# Update with 2023-24 Boston Celtics team data
await formula_playground_update_variables({
    "session_id": session_id,
    "variables": {
        "FGM": 45.2, "3PM": 12.8, "FGA": 90.1,  # Shooting
        "TOV": 12.1, "FTA": 25.3,                # Turnovers
        "OREB": 12.5, "OPP_DREB": 28.2,          # Rebounding
        "FTA": 25.3, "FGA": 90.1                 # Free Throws
    }
})
```

### Step 6: Calculate All Four Factors
```python
# Calculate all four factors
result = await formula_playground_calculate({
    "session_id": session_id
})

print("Four Factors Results:")
for formula_result in result['results']:
    print(f"{formula_result['formula_name']}: {formula_result['result']}")
```

### Step 7: Create Four Factors Visualization
```python
# Create Four Factors radar chart
result = await formula_playground_visualize({
    "session_id": session_id,
    "visualization_type": "radar_chart",
    "title": "Boston Celtics Four Factors Analysis",
    "x_label": "Factors",
    "y_label": "Percentage"
})
```

---

## 🚀 **Workflow 4: Advanced Metrics from Sports Analytics**

### Step 1: Extract Win Shares Formula
```python
# Extract Win Shares from Sports Analytics
result = await formula_extract_from_pdf({
    "book_path": "books/sports-analytics.pdf",
    "page_number": 200,
    "formula_patterns": ["win shares", "WS", "contribution", "wins"]
})

print("Win Shares Formula:")
print(f"Formula: {result['formula']}")
print(f"Variables: {result['variables']}")
```

### Step 2: Extract VORP Formula
```python
# Extract VORP from Sports Analytics
result = await formula_extract_from_pdf({
    "book_path": "books/sports-analytics.pdf",
    "page_number": 250,
    "formula_patterns": ["VORP", "value over replacement", "replacement level"]
})

print("VORP Formula:")
print(f"Formula: {result['formula']}")
print(f"Variables: {result['variables']}")
```

### Step 3: Extract BPM Formula
```python
# Extract BPM from Sports Analytics
result = await formula_extract_from_pdf({
    "book_path": "books/sports-analytics.pdf",
    "page_number": 300,
    "formula_patterns": ["BPM", "box plus minus", "plus minus"]
})

print("BPM Formula:")
print(f"Formula: {result['formula']}")
print(f"Variables: {result['variables']}")
```

### Step 4: Create Advanced Metrics Session
```python
# Create session for advanced metrics
result = await formula_playground_create_session({
    "session_name": "Advanced Metrics Analysis",
    "description": "Win Shares, VORP, and BPM from Sports Analytics"
})

session_id = result['session_id']
```

### Step 5: Add Advanced Metrics
```python
# Add Win Shares
await formula_playground_add_formula({
    "session_id": session_id,
    "formula_name": "Win_Shares",
    "formula": ws_formula,
    "description": "Win Shares from Sports Analytics"
})

# Add VORP
await formula_playground_add_formula({
    "session_id": session_id,
    "formula_name": "VORP",
    "formula": vorp_formula,
    "description": "Value Over Replacement Player"
})

# Add BPM
await formula_playground_add_formula({
    "session_id": session_id,
    "formula_name": "BPM",
    "formula": bpm_formula,
    "description": "Box Plus/Minus"
})
```

### Step 6: Update with Player Data
```python
# Update with Nikola Jokic 2023-24 stats
await formula_playground_update_variables({
    "session_id": session_id,
    "variables": {
        # Win Shares variables
        "OWS": 8.2, "DWS": 4.1,
        # VORP variables
        "BPM": 8.7, "POSS_PCT": 0.28, "TEAM_GAMES": 82,
        # BPM variables
        "Raw_BPM": 8.5, "Pace_Adjustment": 1.01
    }
})
```

### Step 7: Calculate Advanced Metrics
```python
# Calculate all advanced metrics
result = await formula_playground_calculate({
    "session_id": session_id
})

print("Advanced Metrics Results:")
for formula_result in result['results']:
    print(f"{formula_result['formula_name']}: {formula_result['result']}")
```

---

## 🚀 **Workflow 5: Modern Analytics from The Midrange Theory**

### Step 1: Extract Net Rating Formula
```python
# Extract Net Rating from The Midrange Theory
result = await formula_extract_from_pdf({
    "book_path": "books/the-midrange-theory.pdf",
    "page_number": 150,
    "formula_patterns": ["net rating", "ORtg", "DRtg", "offensive rating", "defensive rating"]
})

print("Net Rating Formula:")
print(f"Formula: {result['formula']}")
print(f"Variables: {result['variables']}")
```

### Step 2: Extract Clutch Metrics
```python
# Extract Clutch Performance from The Midrange Theory
result = await formula_extract_from_pdf({
    "book_path": "books/the-midrange-theory.pdf",
    "page_number": 220,
    "formula_patterns": ["clutch", "close games", "late game", "pressure"]
})

print("Clutch Performance Formula:")
print(f"Formula: {result['formula']}")
print(f"Variables: {result['variables']}")
```

### Step 3: Create Modern Analytics Session
```python
# Create session for modern analytics
result = await formula_playground_create_session({
    "session_name": "Modern Analytics Analysis",
    "description": "Net Rating and Clutch Performance from The Midrange Theory"
})

session_id = result['session_id']
```

### Step 4: Add Modern Metrics
```python
# Add Net Rating
await formula_playground_add_formula({
    "session_id": session_id,
    "formula_name": "Net_Rating",
    "formula": net_rating_formula,
    "description": "Net Rating from The Midrange Theory"
})

# Add Clutch Performance
await formula_playground_add_formula({
    "session_id": session_id,
    "formula_name": "Clutch_Performance",
    "formula": clutch_formula,
    "description": "Clutch Performance in Close Games"
})
```

### Step 5: Update with Team Data
```python
# Update with 2023-24 Denver Nuggets team data
await formula_playground_update_variables({
    "session_id": session_id,
    "variables": {
        "ORtg": 116.8, "DRtg": 111.2,  # Net Rating
        "Clutch_PTS": 45, "Clutch_AST": 8, "Clutch_REB": 12, "Clutch_MIN": 25  # Clutch
    }
})
```

### Step 6: Calculate Modern Metrics
```python
# Calculate modern analytics metrics
result = await formula_playground_calculate({
    "session_id": session_id
})

print("Modern Analytics Results:")
for formula_result in result['results']:
    print(f"{formula_result['formula_name']}: {formula_result['result']}")
```

---

## 🔍 **Advanced Workflow: Cross-Book Formula Comparison**

### Step 1: Extract Same Formula from Multiple Books
```python
# Extract PER from Basketball on Paper
per_oliver = await formula_extract_from_pdf({
    "book_path": "books/basketball-on-paper.pdf",
    "page_number": 85,
    "formula_patterns": ["PER", "efficiency", "rating"]
})

# Extract PER from Sports Analytics
per_modern = await formula_extract_from_pdf({
    "book_path": "books/sports-analytics.pdf",
    "page_number": 180,
    "formula_patterns": ["PER", "efficiency", "rating"]
})

print("PER Formulas from Different Sources:")
print(f"Oliver: {per_oliver['formula']}")
print(f"Modern: {per_modern['formula']}")
```

### Step 2: Compare Formula Versions
```python
# Compare PER versions across sources
result = await formula_compare_versions({
    "formula_id": "per",
    "comparison_types": ["structural", "mathematical", "accuracy"],
    "include_historical": True
})

print("PER Version Comparison:")
print(f"Number of versions: {len(result['versions'])}")
print(f"Best version: {result['recommended_version']}")
print(f"Similarity score: {result['similarity_score']}")
```

### Step 3: Get Evolution Analysis
```python
# Get historical evolution of PER formula
result = await formula_get_evolution({
    "formula_id": "per",
    "include_analysis": True
})

print("PER Formula Evolution:")
print(f"Evolution stages: {len(result['evolution_stages'])}")
print(f"Key changes: {result['key_changes']}")
print(f"Recommendations: {result['recommendations']}")
```

---

## 📊 **Best Practices for PDF Analysis**

### 1. Formula Extraction
- **Use specific patterns**: Include relevant keywords like "formula", "calculation", "metric"
- **Check confidence scores**: Only use formulas with confidence > 0.7
- **Validate extracted formulas**: Always validate before using in calculations

### 2. Variable Mapping
- **Map to standard names**: Use consistent variable naming (FGM, FGA, etc.)
- **Check units**: Ensure units are consistent (minutes vs seconds, percentages vs decimals)
- **Validate ranges**: Check that input values are within expected ranges

### 3. Formula Analysis
- **Understand complexity**: Start with simple formulas before complex ones
- **Get tool recommendations**: Use suggested tools for optimal analysis
- **Check dependencies**: Understand which formulas depend on others

### 4. Interactive Sessions
- **Use descriptive names**: Create meaningful session and formula names
- **Group related formulas**: Keep related formulas in the same session
- **Document sources**: Always include source information

### 5. Validation
- **Test with known data**: Use real player/team data for validation
- **Compare across sources**: Validate formulas against multiple sources
- **Check mathematical consistency**: Ensure formulas are mathematically sound

---

## 🎯 **Common Workflow Patterns**

### Pattern 1: Single Formula Analysis
1. Read relevant book pages
2. Extract formula with high confidence
3. Analyze formula structure
4. Create interactive session
5. Add formula and test data
6. Calculate and visualize results
7. Validate against known results

### Pattern 2: Formula Comparison
1. Extract same formula from multiple sources
2. Create comparison session
3. Add all formula versions
4. Update with same test data
5. Calculate all versions
6. Compare results and visualize
7. Get recommendations for best version

### Pattern 3: Comprehensive Analysis
1. Extract multiple related formulas
2. Create comprehensive session
3. Add all formulas with descriptions
4. Update with complete dataset
5. Calculate all metrics
6. Create dashboard visualization
7. Validate entire analysis

### Pattern 4: Historical Analysis
1. Extract formula from multiple time periods
2. Compare versions across sources
3. Analyze evolution and changes
4. Get recommendations for current use
5. Document historical context

---

## 📈 **Performance Tips**

### 1. Efficient PDF Reading
- **Read specific pages**: Don't read entire books unless necessary
- **Use page ranges**: Read multiple pages at once when possible
- **Cache results**: Store frequently accessed content

### 2. Formula Extraction
- **Use targeted patterns**: Specific patterns yield better results
- **Check multiple pages**: Formulas might appear on multiple pages
- **Validate immediately**: Check extracted formulas before proceeding

### 3. Session Management
- **Reuse sessions**: Keep related formulas in the same session
- **Clear unused sessions**: Clean up old sessions to save memory
- **Export results**: Save important results for future reference

### 4. Error Handling
- **Check for errors**: Always check for extraction and calculation errors
- **Use fallbacks**: Have backup formulas ready if extraction fails
- **Validate inputs**: Ensure input data is within expected ranges

---

## 🔗 **Integration with Other Tools**

### 1. Formula Intelligence
- Use `formula_analyze` to understand formula structure
- Get `formula_suggest_tools` for optimal analysis approach
- Apply `formula_map_variables` for proper variable mapping

### 2. Validation System
- Use `formula_validate_comprehensive` for thorough validation
- Add `formula_add_reference` to build formula database
- Compare `formula_compare_validations` across sources

### 3. Visualization
- Use `formula_playground_visualize` for interactive charts
- Apply `visualization_generate` for advanced visualizations
- Export `visualization_export` for presentations

### 4. Comparison System
- Use `formula_compare_versions` for cross-source comparison
- Apply `formula_get_evolution` for historical analysis
- Get `formula_get_recommendations` for best practices

---

## 📚 **Resources and References**

### Books Available
- `books/basketball-on-paper.pdf` - Dean Oliver's foundational work
- `books/sports-analytics.pdf` - Modern advanced metrics compilation
- `books/the-midrange-theory.pdf` - Contemporary basketball analysis

### Formula Libraries
- Pre-built sports formulas in `algebra_helper.py`
- Formula references in validation system
- Multi-source formula database in comparison system

### Documentation
- `COMPREHENSIVE_SPORTS_ANALYTICS_GUIDE.md` - Complete integration guide
- `ALGEBRAIC_TOOLS_GUIDE.md` - Basic algebraic tools
- `PHASE_*_IMPLEMENTATION_COMPLETE.md` - Implementation details

---

## 🎉 **Conclusion**

This step-by-step guide provides comprehensive workflows for extracting, analyzing, and implementing formulas from sports analytics PDFs. The combination of PDF reading, formula extraction, interactive analysis, and validation creates a powerful platform for sports analytics research.

Key benefits:
- **Complete workflow**: From PDF to implementation
- **Multiple sources**: Compare formulas across books
- **Interactive analysis**: Real-time experimentation
- **Comprehensive validation**: Ensure accuracy and consistency
- **Advanced visualization**: Clear presentation of results

---

**Next Steps:**
1. Try the workflows with your own data
2. Explore additional formulas from the books
3. Create custom analysis sessions
4. Share results and visualizations
5. Contribute new formulas to the library

---

*Guide created: October 13, 2025*
*Last updated: October 13, 2025*
*Version: 1.0*




