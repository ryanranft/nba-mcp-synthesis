# Math Book Integration with NBA MCP Server

## Overview

The NBA MCP Server now includes comprehensive book reading capabilities with **math content awareness**. This integration allows LLMs (especially Google Gemini with its large context window) to read technical books containing mathematical formulas and work alongside the **math-mcp** server for accurate computations.

## 🎯 Two-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        LLM (Gemini/Claude)                   │
│                                                               │
│  1. Reads book content with LaTeX preserved                 │
│  2. Understands formulas and mathematical concepts          │
│  3. Orchestrates computation workflow                       │
└───────────────┬─────────────────────────────┬───────────────┘
                │                             │
                ▼                             ▼
┌───────────────────────────┐   ┌──────────────────────────────┐
│      NBA MCP Server       │   │      math-mcp Server         │
│                           │   │                              │
│  Tools:                   │   │  Tools:                      │
│  • list_books             │   │  • add, subtract, multiply   │
│  • read_book (chunked)    │   │  • mean, median, mode        │
│  • search_books           │   │  • sin, cos, tan             │
│                           │   │  • floor, ceiling, round     │
│  Resources:               │   │  • degreesToRadians          │
│  • book://{path}          │   │  • radiansToDegrees          │
│  • book://{path}/chunk/N  │   │  • and 14 more...           │
│                           │   │                              │
│  Prompts:                 │   │                              │
│  • recommend_books        │   │                              │
└───────────────────────────┘   └──────────────────────────────┘
                │                             │
                ▼                             ▼
┌───────────────────────────────────────────────────────────────┐
│                      AWS S3 Bucket                            │
│                                                                │
│  books/                                                       │
│    ├── math/                                                  │
│    │   ├── statistics-intro.txt                              │
│    │   ├── linear-algebra.txt                                │
│    │   └── calculus-guide.txt                                │
│    ├── technical/                                             │
│    │   ├── python-best-practices.txt                         │
│    │   └── machine-learning-basics.txt                       │
│    └── nba-analytics/                                         │
│        ├── advanced-metrics.txt                               │
│        └── player-tracking-data.txt                           │
└───────────────────────────────────────────────────────────────┘
```

## 📚 Book Tools

### 1. `list_books` - Discover Books with Math Detection

Lists all books in S3 with automatic math content detection.

**Parameters:**
- `prefix` (str, default: "books/"): S3 prefix filter
- `max_keys` (int, default: 100): Maximum books to return

**Response:**
```json
{
  "books": [
    {
      "path": "books/math/statistics-intro.txt",
      "size": 524288,
      "last_modified": "2025-10-10T12:00:00Z",
      "format": "txt",
      "has_math": true,
      "math_difficulty": 0.65,
      "recommended_mcp": "math-mcp"
    }
  ],
  "count": 10,
  "prefix": "books/",
  "success": true
}
```

**Math Detection Fields:**
- `has_math` (bool): True if book contains LaTeX or math symbols
- `math_difficulty` (float 0-1): Complexity score based on formula density
- `recommended_mcp` (str): Suggests "math-mcp" if math content detected

### 2. `read_book` - Read Books in Chunks with LaTeX Preservation

Reads books in configurable chunks with full LaTeX preservation.

**Parameters:**
- `book_path` (str): S3 path to book (e.g., "books/math/statistics.txt")
- `chunk_size` (int, default: 50000): Characters per chunk (1k-200k)
- `chunk_number` (int, default: 0): Chunk index (0-based)

**Recommended Chunk Sizes:**
- **50k chars**: Default, works with all LLMs (GPT-4, Claude)
- **100k chars**: For denser content (Gemini, Claude 2.1+)
- **200k chars**: Maximum, for long chapters (Gemini 1.5 Pro only)

**Response:**
```json
{
  "book_path": "books/math/statistics-intro.txt",
  "content": "Chapter 3: Standard Deviation\n\nThe standard deviation measures...\n\n$$\\sigma = \\sqrt{\\frac{\\sum_{i=1}^{n}(x_i - \\mu)^2}{n}}$$\n\nWhere...",
  "chunk_number": 0,
  "chunk_size": 50000,
  "total_chunks": 11,
  "has_more": true,
  "metadata": {
    "total_size": 524288,
    "format": "txt",
    "has_math": true,
    "latex_formulas": 23,
    "math_difficulty": 0.68,
    "recommended_mcp": "math-mcp"
  },
  "success": true
}
```

**LaTeX Preservation:**
- Inline formulas: `$\sigma = \sqrt{...}$`
- Display formulas: `$$\sum_{i=1}^{n} x_i$$`
- Environments: `\begin{equation}...\end{equation}`
- Symbols: `∑ ∫ ∂ ∇ √ ± × ÷ ≤ ≥ α β γ θ λ σ π`

### 3. `search_books` - Full-Text Search Across Library

Searches all books for specific terms or concepts.

**Parameters:**
- `query` (str): Search query
- `book_prefix` (str, default: "books/"): Limit search to prefix
- `max_results` (int, default: 10): Maximum results

**Response:**
```json
{
  "results": [
    {
      "book_path": "books/math/statistics-intro.txt",
      "excerpt": "...standard deviation formula: σ = √(Σ(x-μ)²/n)...",
      "match_count": 7,
      "match_position": 12458,
      "chunk_number": 0,
      "relevance_score": 0.7
    }
  ],
  "count": 5,
  "query": "standard deviation",
  "success": true
}
```

## 🔗 Book Resources

Direct URI access to books without tool calls.

### 1. `book://{path}` - Book Metadata

Get quick metadata without reading full content.

**Example:**
```
URI: book://books/math/statistics.txt

Returns:
{
  "path": "books/math/statistics.txt",
  "size": 524288,
  "total_chunks": 11,
  "has_math": true,
  "math_difficulty": 0.68,
  "latex_formulas": 23,
  "recommended_mcp": "math-mcp",
  "preview": "Chapter 1: Introduction to Statistics..."
}
```

### 2. `book://{path}/chunk/{N}` - Direct Chunk Access

Access specific chunk directly.

**Example:**
```
URI: book://books/math/statistics.txt/chunk/5

Returns: (raw text content of chunk 5)
```

## 💡 Math-Aware Recommendation Prompt

The `recommend_books` prompt guides LLMs to analyze your library and provide personalized reading plans.

**Usage:**
```python
await mcp.call_prompt("recommend_books", {
    "project_goal": "Build NBA player performance prediction system",
    "current_knowledge": "Intermediate",
    "focus_area": "Machine Learning"
})
```

**The prompt instructs the LLM to:**
1. Use `list_books` to discover available books
2. Analyze `has_math` and `math_difficulty` scores
3. Recommend reading order based on skill level
4. Identify where to use math-mcp for computations
5. Provide practical milestones

**Example Output:**
```markdown
# Book Recommendations for: NBA Player Prediction System

## Recommended Books (in order):

1. **Python for Data Science** (books/technical/python-data-science.txt)
   - No math content (math_difficulty: 0.0)
   - Focus: Chapters 3-5 (pandas, numpy basics)
   - Time: 4 hours
   - Milestone: Load and explore NBA dataset

2. **Statistics for Machine Learning** (books/math/ml-statistics.txt)
   - Math content detected (math_difficulty: 0.72)
   - **Use math-mcp for:** mean, median, std deviation calculations
   - Focus: Chapters 1-3, 7 (distributions, hypothesis testing)
   - Time: 8 hours
   - Milestone: Statistical analysis of player performance

3. **NBA Advanced Metrics** (books/nba/advanced-metrics.txt)
   - Moderate math (math_difficulty: 0.45)
   - **Use math-mcp for:** PER, WS, BPM formulas
   - Focus: Chapters 2, 4, 6
   - Time: 6 hours
   - Milestone: Calculate advanced player metrics

## Math-MCP Integration Points:

### Book 2, Chapter 3: Standard Deviation
Formula: σ = √(Σ(x-μ)²/n)

Workflow:
1. Read formula from book
2. Extract player PPG data: [28.5, 31.2, 27.8, 29.4, 30.1]
3. Call math-mcp.mean([28.5, 31.2, 27.8, 29.4, 30.1]) → 29.4
4. Call math-mcp.subtract for each deviation
5. Call math-mcp.sum for Σ
6. Call math-mcp.division for final result
```

## 🧮 Math Detection Algorithm

The `detect_math_content()` function analyzes text for mathematical content:

```python
def detect_math_content(content: str) -> dict:
    """
    Detects:
    - LaTeX inline formulas: $...$
    - LaTeX display formulas: $$...$$
    - LaTeX environments: \begin{equation}, \begin{align}, etc.
    - Math symbols: ∑ ∫ ∂ ∇ √ ± × ÷ ≤ ≥ α β γ θ λ σ π
    - Math functions: sin, cos, tan, log, ln, exp, sqrt, etc.

    Returns:
    {
        "has_math": bool,
        "latex_formulas": int,
        "math_symbols": int,
        "math_functions": int,
        "difficulty_score": float (0-1),
        "recommended_mcp": "math-mcp" | None
    }
    """
```

**Difficulty Score Calculation:**
- `difficulty = min(1.0, latex_count * 0.1 + symbols * 0.01 + functions * 0.05)`
- **0.0-0.3**: Simple (basic arithmetic, occasional formula)
- **0.3-0.6**: Moderate (regular formulas, some complexity)
- **0.6-1.0**: Advanced (dense mathematical content)

## 🔄 Complete Workflow Example

### Scenario: Learning Standard Deviation from Book

**Step 1: Discover Books**
```python
result = await list_books({"prefix": "books/math/"})
# Shows: statistics-intro.txt has_math=true, math_difficulty=0.68
```

**Step 2: Read Book**
```python
chunk = await read_book({
    "book_path": "books/math/statistics-intro.txt",
    "chunk_number": 2  # Chapter 3 on standard deviation
})

# Content includes:
# "Standard deviation: σ = √(Σ(x-μ)²/n)"
# "Example: Calculate std dev of [23, 28, 25, 30, 27]"
```

**Step 3: Extract Values**
LLM reads: `x = [23, 28, 25, 30, 27]`

**Step 4: Use math-mcp for Computation**
```python
# Call math-mcp tools in sequence
μ = await math_mcp.mean([23, 28, 25, 30, 27])  # → 26.6

# Deviations
d1 = await math_mcp.subtract(23, 26.6)  # → -3.6
d2 = await math_mcp.subtract(28, 26.6)  # → 1.4
# ... etc

# Squared deviations
sq1 = await math_mcp.multiply(-3.6, -3.6)  # → 12.96
# ... etc

# Sum
sum_sq = await math_mcp.sum([12.96, 1.96, 2.56, 11.56, 0.16])  # → 29.2

# Average
variance = await math_mcp.division(29.2, 5)  # → 5.84

# Square root (approximate or use calculator)
σ ≈ 2.42
```

**Step 5: Verify Understanding**
LLM explains: "The standard deviation of 2.42 means the data points typically deviate by about 2.42 from the mean of 26.6."

## 🎓 Use Cases

### 1. Learning New Concepts
**Goal**: Understand statistical methods for NBA analytics

**Workflow:**
1. `recommend_books` → Get personalized reading list
2. `read_book` → Read chapters sequentially
3. math-mcp → Compute examples from book
4. `search_books` → Find related concepts

### 2. Reference During Development
**Goal**: Implement PER (Player Efficiency Rating) formula

**Workflow:**
1. `search_books(query="Player Efficiency Rating")` → Find relevant sections
2. `read_book(chunk_number=X)` → Read formula chapter
3. math-mcp → Test formula with sample data
4. Implement in code

### 3. Research & Synthesis
**Goal**: Write whitepaper on NBA prediction models

**Workflow:**
1. `list_books` → Catalog all technical books
2. `search_books` → Find sections on prediction models
3. `read_book` → Read multiple book excerpts
4. Synthesize findings with citations

## 📊 Math-MCP Tools Reference

### Basic Arithmetic
- `add(a, b)` - Addition
- `subtract(a, b)` - Subtraction
- `multiply(a, b)` - Multiplication
- `division(a, b)` - Division
- `modulo(a, b)` - Remainder
- `sum([...])` - Sum array

### Statistics
- `mean([...])` - Arithmetic mean
- `median([...])` - Median value
- `mode([...])` - Most frequent value
- `min([...])` - Minimum value
- `max([...])` - Maximum value

### Trigonometry
- `sin(x)` - Sine (radians)
- `cos(x)` - Cosine (radians)
- `tan(x)` - Tangent (radians)
- `arcsin(x)` - Arcsine
- `arccos(x)` - Arccosine
- `arctan(x)` - Arctangent
- `degreesToRadians(x)` - Convert degrees to radians
- `radiansToDegrees(x)` - Convert radians to degrees

### Rounding
- `floor(x)` - Round down
- `ceiling(x)` - Round up
- `round(x)` - Round to nearest integer

## 🚀 Getting Started

### 1. Upload Books to S3
```bash
aws s3 cp my-stats-book.txt s3://your-bucket/books/math/statistics.txt
```

### 2. Install math-mcp Server
```bash
cd /Users/ryanranft/modelcontextprotocol/math-mcp
npm install
npm run build
```

### 3. Configure Claude Desktop
Add both servers to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "nba-mcp": {
      "command": "python",
      "args": ["-m", "mcp_server.fastmcp_server"]
    },
    "math-mcp": {
      "command": "node",
      "args": ["/path/to/math-mcp/build/index.js"]
    }
  }
}
```

### 4. Test Book Reading
```python
# In Claude Desktop or MCP client
await list_books()
await read_book({"book_path": "books/math/statistics.txt"})
```

### 5. Use Recommendation Prompt
```python
await recommend_books({
    "project_goal": "Learn NBA analytics with machine learning",
    "current_knowledge": "Intermediate",
    "focus_area": "Statistics and ML"
})
```

## 🔒 Security Features

- **Path traversal protection**: No `..` or absolute paths allowed
- **Prefix-based access control**: Books isolated to `books/` prefix
- **Read-only access**: No file modification or deletion
- **S3 IAM permissions**: Control upload access separately
- **Input validation**: All parameters validated with Pydantic

## 📈 Performance Notes

### Chunking Strategy
- **Small chunks (50k)**: More requests, but faster per request
- **Large chunks (200k)**: Fewer requests, but slower per request
- **Recommendation**: Start with 50k, increase for Gemini

### Math Detection
- Scans first 5000 characters for `list_books`
- Scans full chunk content for `read_book`
- Cached in metadata response

### S3 Optimization
- Uses `head_object` for quick metadata
- Streams large files efficiently
- Consider S3 Transfer Acceleration for large libraries

## 🎯 Next Steps

1. **Upload your first book**: Add a math/technical book to S3
2. **Test list_books**: Verify math detection works
3. **Read a chapter**: Try different chunk sizes
4. **Use recommendation prompt**: Get personalized reading plan
5. **Integrate math-mcp**: Follow a formula from book to computation

## 📚 Related Documentation

- [BOOK_INTEGRATION_GUIDE.md](./BOOK_INTEGRATION_GUIDE.md) - Complete book integration guide
- [responses.py:240-273](./mcp_server/responses.py) - Book response models
- [params.py:301-395](./mcp_server/tools/params.py) - Book parameter models
- [fastmcp_server.py:603-962](./mcp_server/fastmcp_server.py) - Book tools implementation
- [math-mcp README](../modelcontextprotocol/math-mcp/README.md) - Math tools reference

---

**Built with ❤️ for NBA analytics and machine learning education**
