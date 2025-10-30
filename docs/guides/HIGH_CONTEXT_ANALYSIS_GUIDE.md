# High-Context Book Analysis System - Technical Reference Guide

**Version:** 1.0
**Last Updated:** October 29, 2025
**Status:** Production Ready

---

## Table of Contents

- [A. Overview & Architecture](#a-overview--architecture)
- [B. Technical Details](#b-technical-details)
- [C. Usage Instructions](#c-usage-instructions)
- [D. Cost Analysis](#d-cost-analysis)
- [E. Features](#e-features)
- [F. Troubleshooting](#f-troubleshooting)
- [G. Advanced Topics](#g-advanced-topics)
- [H. Output & Results](#h-output--results)
- [I. Testing & Validation](#i-testing--validation)
- [J. References](#j-references)

---

## A. Overview & Architecture

### What is the High-Context Book Analyzer?

The High-Context Book Analyzer is an advanced AI-powered system designed to analyze entire technical books (up to 1 million characters or ~250,000 tokens) using state-of-the-art large language models with extended context windows. Unlike traditional approaches that split books into chunks, this system can process entire books in a single pass, maintaining full context and understanding complex interconnections throughout the text.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                High-Context Book Analyzer                        │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Input Processing                              │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                │  │
│  │  │   PDF    │  │   TXT    │  │   S3     │                │  │
│  │  │ Extractor│  │  Reader  │  │  Reader  │                │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘                │  │
│  │       └─────────────┴─────────────┘                       │  │
│  │                     │                                       │  │
│  │                     ▼                                       │  │
│  │          ┌──────────────────────┐                          │  │
│  │          │  Content Truncation  │                          │  │
│  │          │  (up to 1M chars)    │                          │  │
│  │          └──────────┬───────────┘                          │  │
│  └──────────────────────┼───────────────────────────────────┘  │
│                         │                                       │
│  ┌───────────────────────▼───────────────────────────────────┐  │
│  │            Project Context Integration                     │  │
│  │  ┌──────────────────────────────────────────────────┐    │  │
│  │  │  workflow_config.yaml (projects, readmes, etc)   │    │  │
│  │  └──────────────────────────────────────────────────┘    │  │
│  └────────────────────────┬──────────────────────────────────┘  │
│                           │                                      │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │              Dual-Model Analysis                          │  │
│  │  ┌──────────────────────┐  ┌───────────────────────────┐ │  │
│  │  │   Gemini 1.5 Pro     │  │   Claude Sonnet 4         │ │  │
│  │  │   (2M token context) │  │   (1M token context)      │ │  │
│  │  │   Tiered Pricing     │  │   Flat Pricing            │ │  │
│  │  └──────────┬───────────┘  └───────────┬───────────────┘ │  │
│  │             │                           │                  │  │
│  │             ▼                           ▼                  │  │
│  │  ┌──────────────────────┐  ┌───────────────────────────┐ │  │
│  │  │  Recommendations     │  │  Recommendations          │ │  │
│  │  │  (30-60 items)       │  │  (30-60 items)            │ │  │
│  │  └──────────┬───────────┘  └───────────┬───────────────┘ │  │
│  └─────────────┼──────────────────────────┼──────────────────┘  │
│                │                           │                     │
│  ┌─────────────▼───────────────────────────▼──────────────────┐ │
│  │              Consensus Synthesis                           │ │
│  │  ┌────────────────────────────────────────────────────┐   │ │
│  │  │  • Jaccard Similarity (70% threshold)              │   │ │
│  │  │  • Merge overlapping recommendations               │   │ │
│  │  │  • Prioritize by agreement + confidence            │   │ │
│  │  │  • Classify: critical | important | nice-to-have   │   │ │
│  │  └────────────────────────────────────────────────────┘   │ │
│  └────────────────────────┬───────────────────────────────────┘ │
│                           │                                      │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │              Output Generation                            │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐         │  │
│  │  │   JSON     │  │  Markdown  │  │   Cache    │         │  │
│  │  │  Results   │  │   Report   │  │  Storage   │         │  │
│  │  └────────────┘  └────────────┘  └────────────┘         │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Comparison with Standard 4-Model System

| Feature | High-Context (2 Models) | Standard (4 Models) |
|---------|------------------------|---------------------|
| **Models** | Gemini 1.5 Pro + Claude Sonnet 4 | GPT-4o, Gemini 1.5 Pro, Claude Sonnet 3.5, Ollama |
| **Context Window** | 1-2M tokens per model | 8-128k tokens per model |
| **Processing** | Single pass, full book | 4-step iterative convergence |
| **Cost per Book** | $0.60-0.70 | $2.50-4.00 |
| **Time per Book** | 60-120 seconds | 8-15 minutes |
| **Accuracy** | Very High (full context) | High (convergent synthesis) |
| **Best For** | Single comprehensive pass | Iterative refinement |
| **Bulk Cost (45 books)** | $27-32 | $112-180 |

### When to Use High-Context vs Standard

**Use High-Context When:**
- ✅ Budget allows ($0.60-0.70 per book)
- ✅ Speed is important (60-120s vs 8-15 min)
- ✅ Full-book comprehension critical
- ✅ Books are technical/complex with interconnected concepts
- ✅ Analyzing < 100 books

**Use Standard When:**
- ✅ Budget is very tight (4x more expensive)
- ✅ Need multi-model consensus validation
- ✅ Want iterative convergence
- ✅ Analyzing > 100 books (cost becomes prohibitive)
- ✅ Ollama local model sufficient

---

## B. Technical Details

### Model Specifications

#### Gemini 1.5 Pro

**Model ID:** `gemini-2.0-flash-exp` (Flash experimental)

**Context Window:**
- Maximum: 2,097,152 tokens (2M)
- Recommended: 1,000,000 tokens (1M) for reliability
- Effective: ~250,000 tokens for full books

**Pricing (Tiered):**
- **<128k tokens:** $0.075 per 1M input tokens, $0.30 per 1M output tokens
- **>128k tokens:** $0.15 per 1M input tokens, $0.60 per 1M output tokens
- **Threshold Detection:** Automatic based on input token count

**Performance:**
- Typical response time: 30-60 seconds
- Output token limit: 8,192 tokens
- Temperature: 0.7 (configurable)

**Strengths:**
- Excellent for technical content
- Strong pattern recognition
- Cost-effective for <128k tokens
- Fast response times

**Limitations:**
- Tiered pricing can be confusing
- Output token limit relatively low
- Experimental model (may change)

#### Claude Sonnet 4

**Model ID:** `claude-3-7-sonnet-20250219`

**Context Window:**
- Advertised: 200,000 tokens
- Actual: 1,000,000 tokens (undocumented)
- Effective: ~250,000 tokens for full books

**Pricing (Flat):**
- Input: $3.00 per 1M tokens
- Output: $15.00 per 1M tokens
- **No tiered pricing** (simple, predictable)

**Performance:**
- Typical response time: 40-80 seconds
- Output token limit: 4,096 tokens (configurable to 8,192)
- Temperature: 0.7 (configurable)

**Strengths:**
- Excellent reasoning and analysis
- Strong at following complex instructions
- Flat pricing (no surprises)
- Reliable for technical books

**Limitations:**
- Higher base cost than Gemini
- Slower response times
- Lower output token limit

### Token Limits and Content Truncation

**Character to Token Ratio:**
- Average: 4 characters ≈ 1 token
- Technical text: 4.5 characters ≈ 1 token
- Code: 3.5 characters ≈ 1 token

**Max Content Limits:**
- Default: 1,000,000 characters (~250,000 tokens)
- Safe limit: 900,000 characters (~225,000 tokens)
- Absolute max: 2,000,000 characters (Gemini only)

**Truncation Strategy:**
```python
if len(content) > max_chars:
    content = content[:max_chars]
    logger.warning(f"⚠️  Content truncated to {max_chars:,} chars")
```

**Token Counting:**
```python
# Approximate token count
def estimate_tokens(text: str) -> int:
    return len(text) // 4

# Precise token counting (requires model-specific tokenizer)
# Not used in production due to overhead
```

### Consensus Algorithm

**Similarity Threshold:** 70% (Jaccard similarity)

**Algorithm Steps:**

1. **Normalize Recommendations:**
   ```python
   # Convert to lowercase, remove special chars
   title_normalized = normalize_text(recommendation['title'])
   ```

2. **Calculate Jaccard Similarity:**
   ```python
   def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
       intersection = len(set1 & set2)
       union = len(set1 | set2)
       return intersection / union if union > 0 else 0.0
   ```

3. **Match Recommendations:**
   ```python
   # For each recommendation from model A
   for rec_a in model_a_recs:
       # Find best match in model B
       best_match = None
       best_score = 0.0

       for rec_b in model_b_recs:
           score = jaccard_similarity(
               set(rec_a['title'].split()),
               set(rec_b['title'].split())
           )

           if score >= 0.7 and score > best_score:
               best_match = rec_b
               best_score = score
   ```

4. **Merge Overlapping:**
   ```python
   # If match found (>70% similar)
   if best_match:
       merged = {
           'title': rec_a['title'],  # Use first model's title
           'description': merge_descriptions(rec_a, best_match),
           'confidence': (rec_a['confidence'] + best_match['confidence']) / 2,
           'source': 'both',
           'agreement_score': best_score
       }
   else:
       # Keep as single-model recommendation
       merged = {**rec_a, 'source': 'gemini_only'}
   ```

5. **Prioritize:**
   ```python
   # Critical: Both agree + high confidence
   # Important: Single model + high confidence, or both agree + medium confidence
   # Nice-to-have: Single model + medium confidence, or both agree + low confidence
   ```

### Cost Calculation Formulas

**Gemini 1.5 Pro:**
```python
def calculate_gemini_cost(input_tokens: int, output_tokens: int) -> float:
    if input_tokens < 128_000:
        # Low tier
        input_cost = input_tokens * 0.000075
        output_cost = output_tokens * 0.000300
    else:
        # High tier
        input_cost = input_tokens * 0.00015
        output_cost = output_tokens * 0.00060

    return input_cost + output_cost
```

**Claude Sonnet 4:**
```python
def calculate_claude_cost(input_tokens: int, output_tokens: int) -> float:
    input_cost = input_tokens * 0.003
    output_cost = output_tokens * 0.015

    return input_cost + output_cost
```

**Total Cost:**
```python
total_cost = gemini_cost + claude_cost
```

### Pricing Tier Detection Logic

```python
def detect_pricing_tier(input_tokens: int) -> str:
    """
    Detect which pricing tier applies.

    Returns:
        'low' if < 128k tokens (cheaper)
        'high' if >= 128k tokens (more expensive)
    """
    GEMINI_TIER_THRESHOLD = 128_000

    if input_tokens < GEMINI_TIER_THRESHOLD:
        return 'low'
    else:
        return 'high'
```

**Example:**
- 54,268 tokens → 'low' tier
- 130,000 tokens → 'high' tier

---

## C. Usage Instructions

### Prerequisites

1. **Python Environment:**
   ```bash
   python >= 3.10
   ```

2. **Required Packages:**
   ```bash
   google-generativeai >= 0.8.3
   anthropic >= 0.39.0
   boto3 >= 1.35.0
   pyyaml >= 6.0
   pymupdf >= 1.25.2  # For PDF extraction
   ```

3. **API Keys:**
   - Google AI API key (for Gemini)
   - Anthropic API key (for Claude)
   - AWS credentials (for S3 access)

### API Key Setup

**Method 1: Environment Variables**
```bash
export GOOGLE_AI_API_KEY="your-google-api-key"
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export AWS_ACCESS_KEY_ID="your-aws-access-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
```

**Method 2: Unified Secrets Manager**

1. Edit `secrets/secrets.yaml`:
   ```yaml
   global:
     GOOGLE_AI_API_KEY: "your-google-api-key"
     ANTHROPIC_API_KEY: "your-anthropic-api-key"

   projects:
     nba-mcp-synthesis:
       AWS_ACCESS_KEY_ID: "your-aws-access-key"
       AWS_SECRET_ACCESS_KEY: "your-aws-secret-key"
   ```

2. The analyzer will automatically load from secrets manager

**Method 3: AWS Secrets Manager**
```bash
# Store in AWS Secrets Manager
aws secretsmanager create-secret \
  --name nba-mcp-synthesis/google-ai-key \
  --secret-string "your-google-api-key"
```

### Command-Line Usage

#### Basic Analysis (Single Book from S3)

```bash
python3 scripts/high_context_book_analyzer.py \
  --book-key "books/ML_Textbook.pdf" \
  --book-title "Machine Learning Textbook" \
  --book-author "John Doe"
```

#### Analysis with Custom Output

```bash
python3 scripts/high_context_book_analyzer.py \
  --book-key "books/ML_Textbook.pdf" \
  --book-title "Machine Learning Textbook" \
  --output-dir "custom_results/"
```

#### Analysis with Content Limit

```bash
python3 scripts/high_context_book_analyzer.py \
  --book-key "books/Very_Long_Book.pdf" \
  --max-content 500000  # 500k chars instead of 1M
```

#### Disable Caching (Force Fresh Analysis)

```bash
python3 scripts/high_context_book_analyzer.py \
  --book-key "books/ML_Textbook.pdf" \
  --no-cache
```

#### Analysis with Project Context

```bash
python3 scripts/high_context_book_analyzer.py \
  --book-key "books/ML_Textbook.pdf" \
  --project-aware  # Automatically loads from workflow_config.yaml
```

### Programmatic Usage

```python
from scripts.high_context_book_analyzer import HighContextBookAnalyzer

# Initialize analyzer
analyzer = HighContextBookAnalyzer(
    max_content_chars=1_000_000,
    output_dir="analysis_results",
    cache_enabled=True,
    project_aware=True
)

# Analyze a book
result = await analyzer.analyze_book(
    book_title="Machine Learning Textbook",
    book_author="John Doe",
    book_s3_key="books/ML_Textbook.pdf"
)

# Access results
print(f"Total cost: ${result['cost']['total']:.4f}")
print(f"Recommendations: {len(result['recommendations'])}")
print(f"Consensus: {result['consensus_level']}")

# Get recommendations by priority
critical = [r for r in result['recommendations'] if r['priority'] == 'critical']
important = [r for r in result['recommendations'] if r['priority'] == 'important']
```

### Integration with recursive_book_analysis.py

The high-context analyzer is integrated into the recursive book analysis workflow:

```bash
# Use high-context mode for all books
python3 scripts/recursive_book_analysis.py --high-context

# Combine with other options
python3 scripts/recursive_book_analysis.py \
  --high-context \
  --max-iterations 1 \
  --similarity-threshold 0.85 \
  --books books/ML_Textbook.pdf books/DL_Textbook.pdf
```

**Integration Point (line 1722):**
```python
if args.high_context:
    logger.info("🚀 Using High-Context Book Analyzer")
    from scripts.high_context_book_analyzer import HighContextBookAnalyzer

    analyzer = HighContextBookAnalyzer(
        max_content_chars=1_000_000,
        cache_enabled=not args.no_cache,
        project_aware=True
    )

    result = await analyzer.analyze_book(
        book_title=book['title'],
        book_author=book['author'],
        book_s3_key=book['s3_key']
    )
```

### Project-Aware Analysis Mode

**Purpose:** Provide AI models with context about your projects to generate more relevant recommendations.

**Configuration (workflow_config.yaml):**
```yaml
projects:
  - name: "nba-mcp-synthesis"
    path: "/Users/user/nba-mcp-synthesis"
    description: "NBA analytics MCP server with advanced econometrics"
    readme_path: "README.md"
    key_technologies:
      - Python
      - FastAPI
      - MLflow
      - PostgreSQL

  - name: "nba-simulator-aws"
    path: "/Users/user/nba-simulator-aws"
    description: "Full-stack NBA game simulator with real-time predictions"
    readme_path: "README.md"
    key_technologies:
      - React
      - TypeScript
      - AWS Lambda
      - DynamoDB
```

**How It Works:**
1. Analyzer loads project metadata from `workflow_config.yaml`
2. Scans each project directory for README files and technology stacks
3. Builds context string with project details
4. Includes context in AI prompt: "Given these projects: [context]"
5. AI generates recommendations tailored to your tech stack

**Benefits:**
- More relevant recommendations (e.g., "Add Bayesian methods to your econometric suite")
- Better integration suggestions (e.g., "Connect simulator to your PostgreSQL analytics DB")
- Avoids recommending tech you're not using

---

## D. Cost Analysis

### Detailed Pricing Breakdown

#### Per-Book Cost Estimates

**Typical Book (200k characters = 50k tokens):**

| Model | Pricing Tier | Input Tokens | Output Tokens | Cost |
|-------|-------------|--------------|---------------|------|
| Gemini 1.5 Pro | Low (<128k) | 50,000 | 2,000 | $0.00375 + $0.00060 = **$0.00435** |
| Claude Sonnet 4 | Flat | 50,000 | 2,000 | $0.15000 + $0.03000 = **$0.18000** |
| **Total** | | | | **$0.18435** |

**Large Book (400k characters = 100k tokens):**

| Model | Pricing Tier | Input Tokens | Output Tokens | Cost |
|-------|-------------|--------------|---------------|------|
| Gemini 1.5 Pro | Low (<128k) | 100,000 | 3,000 | $0.0075 + $0.0009 = **$0.00840** |
| Claude Sonnet 4 | Flat | 100,000 | 3,000 | $0.30000 + $0.04500 = **$0.34500** |
| **Total** | | | | **$0.35340** |

**Very Large Book (800k characters = 200k tokens):**

| Model | Pricing Tier | Input Tokens | Output Tokens | Cost |
|-------|-------------|--------------|---------------|------|
| Gemini 1.5 Pro | High (>128k) | 200,000 | 4,000 | $0.03000 + $0.00240 = **$0.03240** |
| Claude Sonnet 4 | Flat | 200,000 | 4,000 | $0.60000 + $0.06000 = **$0.66000** |
| **Total** | | | | **$0.69240** |

### Bulk Analysis Projections

#### 45 Books (Mixed Sizes)

**Assumptions:**
- 15 small books (150k chars avg)
- 20 medium books (300k chars avg)
- 10 large books (600k chars avg)

**Cost Breakdown:**
| Category | Books | Avg Cost | Total |
|----------|-------|----------|-------|
| Small (150k chars) | 15 | $0.15 | $2.25 |
| Medium (300k chars) | 20 | $0.30 | $6.00 |
| Large (600k chars) | 10 | $0.65 | $6.50 |
| **Grand Total** | **45** | **$0.33 avg** | **$14.75** |

**With 10% Overhead (re-runs, API errors):**
- Total: **$16.23**

**Compared to Standard 4-Model System:**
- Standard cost for 45 books: $112-180
- High-context cost: $16.23
- **Savings: $96-164 (86-91% less)**

### Cost Optimization Strategies

#### 1. Use Caching Aggressively

```python
analyzer = HighContextBookAnalyzer(cache_enabled=True)

# First run: Full cost (~$0.35)
result1 = await analyzer.analyze_book(...)

# Second run: FREE (cached)
result2 = await analyzer.analyze_book(...)
```

**Savings:** 100% on repeat analyses

#### 2. Pre-filter Books

```python
# Only analyze books relevant to your project
relevant_books = [
    book for book in all_books
    if any(keyword in book['title'].lower()
           for keyword in ['machine learning', 'statistics', 'python'])
]

# Analyze only relevant subset
for book in relevant_books:
    await analyzer.analyze_book(...)
```

**Savings:** 30-50% by skipping irrelevant books

#### 3. Adjust Content Limit

```python
# For quick scans, use lower limit
analyzer = HighContextBookAnalyzer(max_content_chars=500_000)
```

**Savings:** 40-50% for shorter books

#### 4. Batch Processing with Rate Limiting

```python
import asyncio

# Process in batches to avoid rate limits and spread cost
async def batch_analyze(books, batch_size=5, delay=60):
    for i in range(0, len(books), batch_size):
        batch = books[i:i+batch_size]

        # Process batch concurrently
        tasks = [analyzer.analyze_book(**book) for book in batch]
        await asyncio.gather(*tasks)

        # Wait before next batch
        if i + batch_size < len(books):
            await asyncio.sleep(delay)
```

**Savings:** Avoids API errors and retry costs

### Comparison Tables

#### High-Context vs Standard (Single Book)

| Metric | High-Context | Standard 4-Model | Difference |
|--------|-------------|------------------|------------|
| **Cost** | $0.30-0.70 | $2.50-4.00 | -73% to -88% |
| **Time** | 60-120s | 480-900s | -75% to -87% |
| **API Calls** | 2 | 16-20 | -90% |
| **Iterations** | 1 | 4 | -75% |
| **Context Window** | 1-2M tokens | 8-128k tokens | +10x to +250x |
| **Recommendations** | 30-60 | 40-80 | Similar |

#### Cost by Book Size

| Book Size | Characters | Tokens | High-Context | Standard | Savings |
|-----------|-----------|--------|--------------|----------|---------|
| Small | 150k | 37k | $0.15 | $2.00 | 92% |
| Medium | 300k | 75k | $0.30 | $2.75 | 89% |
| Large | 600k | 150k | $0.60 | $3.50 | 83% |
| Very Large | 1M | 250k | $0.70 | $4.00 | 82% |

#### Cost by Use Case

| Use Case | Books | High-Context | Standard | Savings |
|----------|-------|--------------|----------|---------|
| Single book analysis | 1 | $0.35 | $3.00 | $2.65 |
| Small library | 10 | $3.50 | $30.00 | $26.50 |
| Medium library | 45 | $16.00 | $135.00 | $119.00 |
| Large library | 100 | $35.00 | $300.00 | $265.00 |
| Enterprise | 500 | $175.00 | $1,500.00 | $1,325.00 |

---

## E. Features

### 1. Full Book Comprehension (up to 250k tokens)

**What It Does:**
- Processes entire books in a single pass
- Maintains full context across all chapters
- Understands interconnections between concepts
- No context window splitting or chunking

**How It Works:**
```python
# Load entire book
content = load_book_from_s3(s3_key)

# Truncate if needed (rare for most books)
if len(content) > 1_000_000:
    content = content[:1_000_000]
    logger.warning("Content truncated")

# Send to model in single request
prompt = f"""Analyze this entire technical book:

{content}

Provide comprehensive recommendations..."""

response = await model.generate(prompt)
```

**Benefits:**
- No loss of context between chunks
- Better understanding of overall structure
- Can identify book-wide themes and patterns
- More accurate recommendations

**Limitations:**
- Books > 1M chars must be truncated
- Some very large books may need special handling
- Cost scales with book size

### 2. Dual-Model Validation

**What It Does:**
- Runs analysis with both Gemini 1.5 Pro and Claude Sonnet 4
- Compares recommendations for agreement
- Merges overlapping recommendations
- Flags disagreements for review

**Consensus Levels:**
```python
'both'          # Both models agree (>70% similarity)
'gemini_only'   # Only Gemini provided this recommendation
'claude_only'   # Only Claude provided this recommendation
'conflict'      # Models disagree significantly
```

**Example Output:**
```json
{
  "title": "Add Bayesian Methods",
  "description": "Implement Bayesian inference for player projections",
  "priority": "critical",
  "confidence": 0.95,
  "source": "both",
  "agreement_score": 0.87
}
```

**Benefits:**
- Higher confidence in recommendations
- Catches model hallucinations
- Balanced perspective (Google + Anthropic)
- Validates critical recommendations

### 3. Project Context Integration

**What It Does:**
- Loads your project metadata
- Includes README files and tech stacks
- Tailors recommendations to your projects
- Suggests integrations between projects

**Example Context:**
```
You are analyzing technical books for these projects:

PROJECT: nba-mcp-synthesis
- Description: NBA analytics MCP server with advanced econometrics
- Tech Stack: Python, FastAPI, MLflow, PostgreSQL
- README: [23,437 characters]

PROJECT: nba-simulator-aws
- Description: Full-stack NBA game simulator
- Tech Stack: React, TypeScript, AWS Lambda, DynamoDB
- README: [46,855 characters]

Focus on recommendations that:
1. Enhance existing capabilities
2. Integrate well with current tech stack
3. Add value to both projects
```

**Benefits:**
- More relevant recommendations
- Better integration suggestions
- Avoids suggesting incompatible technologies
- Understands your existing capabilities

### 4. Result Caching

**What It Does:**
- Caches analysis results by book + content hash
- Automatically returns cached results for repeat analyses
- Tracks cache hits and hit count
- Saves 100% of cost on cached analyses

**Cache Storage:**
```
cache/
└── book_analysis/
    └── 5b24c48bbe64a6ba.json  # Hash of book content
```

**Cache Entry:**
```json
{
  "cache_key": "5b24c48bbe64a6ba",
  "book_title": "Machine Learning Textbook",
  "cached_at": "2025-10-25T22:34:29.829038",
  "hit_count": 5,
  "result": {
    "recommendations": [...],
    "cost": {...},
    "tokens": {...}
  }
}
```

**Cache Hit Example:**
```
💾 Cache HIT: book_analysis (5b24c48bbe64a6ba)
   Cached at: 2025-10-25T22:34:29.829038
   Hit count: 5
💾 Using cached analysis result!
```

**Benefits:**
- FREE repeat analyses
- Instant results (<1s)
- Consistent results
- Reduces API load

### 5. Local Filesystem Support

**What It Does:**
- Supports S3 bucket sources
- Supports local file paths
- Handles PDF and TXT formats
- Automatic format detection

**Usage:**
```python
# From S3
result = await analyzer.analyze_book(
    book_s3_key="books/ML_Textbook.pdf"
)

# From local filesystem
result = await analyzer.analyze_book(
    book_local_path="/path/to/ML_Textbook.pdf"
)

# From text content directly
result = await analyzer.analyze_book(
    book_content="Full text content here..."
)
```

**Supported Formats:**
- PDF (.pdf) - Extracted with PyMuPDF
- Plain text (.txt)
- Markdown (.md)
- Raw string content

### 6. Recommendation Validation & Prioritization

**What It Does:**
- Validates all recommendations for completeness
- Scores confidence based on agreement
- Prioritizes into 3 tiers
- Filters out low-quality recommendations

**Validation Checks:**
```python
def validate_recommendation(rec):
    """Ensure recommendation has all required fields."""
    required = ['title', 'description', 'priority', 'confidence']

    for field in required:
        if field not in rec:
            return False

    # Check title length
    if len(rec['title']) < 10 or len(rec['title']) > 200:
        return False

    # Check description length
    if len(rec['description']) < 30:
        return False

    # Check confidence range
    if rec['confidence'] < 0 or rec['confidence'] > 1:
        return False

    return True
```

**Priority Classification:**
```python
def classify_priority(rec, agreement_score):
    """Classify recommendation priority."""

    # Both models agree + high confidence
    if rec['source'] == 'both' and rec['confidence'] >= 0.8:
        return 'critical'

    # Single model + very high confidence
    elif rec['confidence'] >= 0.9:
        return 'critical'

    # Both models agree OR single model + high confidence
    elif rec['source'] == 'both' or rec['confidence'] >= 0.7:
        return 'important'

    # Everything else
    else:
        return 'nice_to_have'
```

**Priority Tiers:**
- **Critical (3-10):** Highest impact, both models agree, high confidence
- **Important (10-25):** High impact, one or both models, medium-high confidence
- **Nice-to-have (5-15):** Lower impact, single model, medium confidence

---

## F. Troubleshooting

### Common Errors and Solutions

#### 1. ModuleNotFoundError: No module named 'scripts'

**Error:**
```
ModuleNotFoundError: No module named 'scripts'
```

**Cause:** Python path not set correctly

**Solution:**
```python
# Add to top of script
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
```

Or run from project root:
```bash
cd /path/to/nba-mcp-synthesis
python3 scripts/high_context_book_analyzer.py ...
```

#### 2. API Key Issues

**Error:**
```
google.api_core.exceptions.Unauthenticated: 401 API key not valid
```

**Cause:** Missing or invalid API key

**Solution:**
```bash
# Check if key is set
echo $GOOGLE_AI_API_KEY

# Set key if missing
export GOOGLE_AI_API_KEY="your-key-here"

# Or add to secrets/secrets.yaml
global:
  GOOGLE_AI_API_KEY: "your-key-here"
```

**Error:**
```
anthropic.AuthenticationError: API key invalid
```

**Solution:**
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

#### 3. Timeout Handling

**Error:**
```
asyncio.exceptions.TimeoutError: Request timed out after 300s
```

**Cause:** Model taking too long (large book or slow API)

**Solution:**
```python
# Increase timeout
analyzer = HighContextBookAnalyzer(
    timeout=600  # 10 minutes instead of 5
)

# Or process with retries
async def analyze_with_retry(book, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await analyzer.analyze_book(**book)
        except asyncio.TimeoutError:
            if attempt < max_retries - 1:
                logger.warning(f"Timeout, retry {attempt + 1}/{max_retries}")
                await asyncio.sleep(60)  # Wait 1 min
            else:
                raise
```

#### 4. Memory Constraints

**Error:**
```
MemoryError: Unable to allocate array
```

**Cause:** Book too large for available memory

**Solution:**
```python
# Reduce max content limit
analyzer = HighContextBookAnalyzer(
    max_content_chars=500_000  # 500k instead of 1M
)

# Or process in chunks (not recommended, loses full-context benefit)
def chunk_book(content, chunk_size=500_000):
    return [content[i:i+chunk_size]
            for i in range(0, len(content), chunk_size)]
```

#### 5. S3 Access Problems

**Error:**
```
botocore.exceptions.NoCredentialsError: Unable to locate credentials
```

**Cause:** AWS credentials not configured

**Solution:**
```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

**Error:**
```
botocore.exceptions.ClientError: Access Denied
```

**Cause:** S3 bucket permissions

**Solution:**
```bash
# Check bucket policy
aws s3api get-bucket-policy --bucket your-bucket-name

# Grant read access
aws s3api put-bucket-policy --bucket your-bucket-name --policy file://policy.json
```

#### 6. Model Initialization Failures

**Error:**
```
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded
```

**Cause:** API rate limit exceeded

**Solution:**
```python
# Add rate limiting
import time

async def analyze_with_rate_limit(books, requests_per_minute=10):
    delay = 60 / requests_per_minute

    for book in books:
        result = await analyzer.analyze_book(**book)
        await asyncio.sleep(delay)
        yield result
```

**Error:**
```
anthropic.RateLimitError: Rate limit exceeded
```

**Solution:**
```python
# Implement exponential backoff
async def analyze_with_backoff(book, max_retries=5):
    for attempt in range(max_retries):
        try:
            return await analyzer.analyze_book(**book)
        except anthropic.RateLimitError:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Rate limit, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
            else:
                raise
```

---

## G. Advanced Topics

### 1. Project-Aware Analysis with Codebase Context

**Full Configuration Example:**
```yaml
# workflow_config.yaml
projects:
  - name: "nba-mcp-synthesis"
    path: "/Users/user/nba-mcp-synthesis"
    description: "NBA analytics MCP server with econometric methods"
    readme_path: "README.md"
    key_technologies:
      - Python 3.10+
      - FastAPI
      - MLflow
      - PostgreSQL
      - Docker

    key_capabilities:
      - "Advanced time series analysis (ARIMAX, VARMAX, VECM)"
      - "Panel data methods (Fixed Effects, Random Effects, GMM)"
      - "Survival analysis (Cox, Fine-Gray, Frailty)"
      - "Causal inference (PSM, IPW, DiD)"
      - "Machine learning (Random Forest, XGBoost, Neural Nets)"

    integration_points:
      - "FastAPI endpoints for all methods"
      - "MCP server protocol"
      - "PostgreSQL for data storage"
      - "MLflow for experiment tracking"
```

**Advanced Context Loading:**
```python
def load_advanced_context(project_config):
    """Load comprehensive project context."""
    context = {
        'name': project_config['name'],
        'description': project_config['description'],
        'technologies': project_config['key_technologies'],
        'capabilities': project_config['key_capabilities'],
        'integration_points': project_config['integration_points']
    }

    # Load README
    readme_path = Path(project_config['path']) / project_config['readme_path']
    if readme_path.exists():
        context['readme'] = readme_path.read_text()[:50_000]  # Limit to 50k chars

    # Scan for key files
    project_path = Path(project_config['path'])
    context['file_structure'] = {
        'python_files': count_files(project_path, '*.py'),
        'test_files': count_files(project_path / 'tests', '*.py'),
        'docs': count_files(project_path / 'docs', '*.md'),
        'configs': count_files(project_path, '*.yaml')
    }

    return context
```

### 2. Custom Content Limits

**Dynamic Limit Based on Book Type:**
```python
def get_content_limit(book_metadata):
    """Determine optimal content limit for book."""

    # Technical/academic books: Full context
    if book_metadata.get('category') in ['technical', 'academic']:
        return 1_000_000

    # Business/strategy books: Medium context
    elif book_metadata.get('category') in ['business', 'strategy']:
        return 600_000

    # General books: Lower context
    else:
        return 400_000

# Use dynamic limit
limit = get_content_limit(book)
analyzer = HighContextBookAnalyzer(max_content_chars=limit)
```

**Page-Based Limits:**
```python
def estimate_chars_from_pages(num_pages, chars_per_page=2000):
    """Estimate character count from page count."""
    return num_pages * chars_per_page

# Limit by page count
max_pages = 400
max_chars = estimate_chars_from_pages(max_pages)
analyzer = HighContextBookAnalyzer(max_content_chars=max_chars)
```

### 3. Extending to Additional Models

**Add GPT-4o:**
```python
from synthesis.models.openai_model_v2 import OpenAIModelV2

class ExtendedHighContextAnalyzer(HighContextBookAnalyzer):
    """Extended analyzer with GPT-4o support."""

    def __init__(self, *args, use_gpt4=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_gpt4 = use_gpt4

        if use_gpt4:
            self.gpt4_model = OpenAIModelV2(
                model_name="gpt-4o",
                max_tokens=8192
            )

    async def analyze_book(self, *args, **kwargs):
        """Analyze with 3 models if GPT-4 enabled."""
        result = await super().analyze_book(*args, **kwargs)

        if self.use_gpt4:
            # Add GPT-4 analysis
            gpt4_recs = await self.gpt4_model.analyze(...)
            result = self.merge_three_models(result, gpt4_recs)

        return result
```

### 4. Performance Tuning

**Parallel Analysis:**
```python
async def analyze_books_parallel(books, max_concurrent=5):
    """Analyze multiple books in parallel."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def analyze_with_semaphore(book):
        async with semaphore:
            return await analyzer.analyze_book(**book)

    tasks = [analyze_with_semaphore(book) for book in books]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out errors
    successful = [r for r in results if not isinstance(r, Exception)]
    errors = [r for r in results if isinstance(r, Exception)]

    return successful, errors

# Use it
results, errors = await analyze_books_parallel(books, max_concurrent=3)
```

**Memory Optimization:**
```python
async def analyze_books_streaming(books):
    """Analyze books one at a time to minimize memory."""
    for book in books:
        result = await analyzer.analyze_book(**book)

        # Save immediately
        save_result(result)

        # Clear memory
        del result
        gc.collect()

        yield  # Allow other tasks to run
```

### 5. Batch Processing Strategies

**Strategy 1: Size-Based Batching**
```python
def batch_by_size(books, size_threshold=500_000):
    """Batch books by estimated size."""
    small_books = []
    large_books = []

    for book in books:
        est_size = estimate_book_size(book)
        if est_size < size_threshold:
            small_books.append(book)
        else:
            large_books.append(book)

    # Process small books first (faster, cheaper)
    return small_books + large_books
```

**Strategy 2: Priority-Based Batching**
```python
def batch_by_priority(books, priority_order):
    """Batch books by importance."""
    return sorted(books, key=lambda b: priority_order.get(b['category'], 999))

# Process critical books first
priority = {'machine_learning': 1, 'statistics': 2, 'general': 3}
ordered_books = batch_by_priority(books, priority)
```

**Strategy 3: Adaptive Batching**
```python
async def adaptive_batch_processing(books):
    """Adjust batch size based on performance."""
    batch_size = 5
    success_rate = 1.0

    for i in range(0, len(books), batch_size):
        batch = books[i:i+batch_size]

        # Process batch
        results, errors = await analyze_batch(batch)
        success_rate = len(results) / len(batch)

        # Adjust batch size
        if success_rate < 0.7:
            batch_size = max(1, batch_size - 1)  # Reduce
        elif success_rate == 1.0:
            batch_size = min(10, batch_size + 1)  # Increase

        logger.info(f"Batch size: {batch_size}, Success rate: {success_rate:.0%}")
```

---

## H. Output & Results

### Result Format and Structure

**Top-Level Result:**
```json
{
  "book_title": "Machine Learning for Absolute Beginners",
  "book_author": "Oliver Theobald",
  "book_s3_key": "books/0812_Machine-Learning-for-Absolute-Beginners.pdf",
  "analyzed_at": "2025-10-29T19:22:18.859Z",
  "analysis_duration_seconds": 41.4,

  "content": {
    "characters": 217072,
    "estimated_tokens": 54268,
    "pages": 179,
    "format": "pdf"
  },

  "models": {
    "gemini": {
      "model_id": "gemini-2.0-flash-exp",
      "status": "success",
      "tokens": {
        "input": 54268,
        "output": 2145
      },
      "cost": 0.0185,
      "duration_seconds": 35.2
    },
    "claude": {
      "model_id": "claude-3-7-sonnet-20250219",
      "status": "cached",
      "tokens": {
        "input": 0,
        "output": 0
      },
      "cost": 0.0000,
      "duration_seconds": 0.0
    }
  },

  "cost": {
    "gemini": 0.0185,
    "claude": 0.0000,
    "total": 0.0185,
    "pricing_tier": "low"
  },

  "tokens": {
    "gemini": 7973,
    "claude": 0,
    "total": 7973
  },

  "consensus": {
    "level": "gemini_only",
    "agreement_rate": null,
    "gemini_recommendations": 21,
    "claude_recommendations": 0,
    "both_agree": 0
  },

  "recommendations": [
    {
      "title": "Implement Bayesian Methods for Player Projections",
      "description": "Add Bayesian inference capabilities...",
      "priority": "critical",
      "confidence": 0.95,
      "source": "both",
      "agreement_score": 0.87,
      "implementation_effort": "high",
      "expected_impact": "high"
    },
    ...
  ],

  "cached": true,
  "cache_hit_count": 5
}
```

### Consensus Metadata

**Full Agreement (both):**
```json
{
  "consensus": {
    "level": "both",
    "agreement_rate": 0.73,
    "gemini_recommendations": 42,
    "claude_recommendations": 38,
    "both_agree": 28
  }
}
```

**Partial Agreement:**
```json
{
  "consensus": {
    "level": "both",
    "agreement_rate": 0.45,
    "gemini_recommendations": 35,
    "claude_recommendations": 32,
    "both_agree": 15
  }
}
```

**Single Model (Gemini Only):**
```json
{
  "consensus": {
    "level": "gemini_only",
    "agreement_rate": null,
    "gemini_recommendations": 21,
    "claude_recommendations": 0,
    "both_agree": 0
  }
}
```

### Validation Scores

**Recommendation Validation:**
```json
{
  "title": "Add Neural Network Models",
  "validation": {
    "has_title": true,
    "has_description": true,
    "has_priority": true,
    "has_confidence": true,
    "title_length_ok": true,
    "description_length_ok": true,
    "confidence_in_range": true,
    "overall_valid": true
  }
}
```

### Priority Classifications

**Priority Distribution:**
```json
{
  "priority_distribution": {
    "critical": 3,
    "important": 15,
    "nice_to_have": 3
  },
  "priority_breakdown": {
    "critical": [
      "Implement Bayesian Methods",
      "Add Panel Data GMM",
      "Enhance Time Series"
    ],
    "important": [
      "Add Random Forest Models",
      "Implement Cross-Validation",
      ...
    ],
    "nice_to_have": [
      "Add Visualization Tools",
      "Create Dashboard",
      "Add Export Features"
    ]
  }
}
```

### Integration with Downstream Tools

**Export to Phase 3 Synthesis:**
```python
def export_for_phase3(result):
    """Convert to Phase 3 synthesis format."""
    return {
        'recommendations': [
            {
                'title': rec['title'],
                'description': rec['description'],
                'priority': rec['priority'],
                'source_book': result['book_title'],
                'confidence': rec['confidence']
            }
            for rec in result['recommendations']
        ]
    }
```

**Export to MLflow:**
```python
import mlflow

def log_to_mlflow(result):
    """Log analysis results to MLflow."""
    with mlflow.start_run():
        # Log parameters
        mlflow.log_param("book_title", result['book_title'])
        mlflow.log_param("consensus_level", result['consensus']['level'])

        # Log metrics
        mlflow.log_metric("total_cost", result['cost']['total'])
        mlflow.log_metric("num_recommendations", len(result['recommendations']))
        mlflow.log_metric("duration_seconds", result['analysis_duration_seconds'])

        # Log artifacts
        mlflow.log_dict(result, "analysis_result.json")
```

---

## I. Testing & Validation

### Running the Test Suite

**Integration Test:**
```bash
cd /Users/ryanranft/nba-mcp-synthesis
python3 tests/integration/test_high_context_analyzer.py
```

**Expected Output:**
```
================================================================================
HIGH-CONTEXT BOOK ANALYZER TEST
================================================================================

📖 Test Book: Machine Learning for Absolute Beginners
👤 Author: Oliver Theobald
📂 S3 Key: books/0812_Machine-Learning-for-Absolute-Beginners.pdf

🚀 Initializing High-Context Book Analyzer...
✅ Gemini 1.5 Pro initialized
✅ Claude Sonnet 4 initialized
✅ High-Context Analyzer ready with 2 models

📊 Starting analysis...
⏱️  This will take 60-120 seconds...

================================================================================
ANALYSIS RESULTS
================================================================================

✅ Analysis successful!

💰 COST BREAKDOWN:
   Total:        $0.0185
   Gemini 1.5 Pro:  $0.0185
   Claude Sonnet 4: $0.0000
   Pricing Tier:    low

📊 TOKEN USAGE:
   Total:    7,973
   Gemini:   7,973
   Claude:   0

📄 CONTENT:
   Characters analyzed: 217,072
   Estimated tokens:    ~54,268

⏱️  PERFORMANCE:
   Total time:   41.4s
   Consensus:    gemini_only

📋 RECOMMENDATIONS:
   Total: 21
   Critical:     3
   Important:    15
   Nice-to-Have: 3

🎯 CONSENSUS:
   From Gemini:  21
   From Claude:  0
   Both agree:   0
```

### Interpreting Test Results

**Success Indicators:**
- ✅ Both models initialize successfully
- ✅ Book loaded from S3 without errors
- ✅ Analysis completes in < 120 seconds
- ✅ Cost within expected range ($0.15-0.70)
- ✅ Recommendations generated (20-60 expected)
- ✅ All recommendations have required fields

**Warning Signs:**
- ⚠️ Only one model succeeds (check API keys)
- ⚠️ Cost > $1.00 (check pricing tier)
- ⚠️ Time > 180 seconds (check network/API)
- ⚠️ < 10 recommendations (check prompt quality)
- ⚠️ Consensus level "none" (models disagree completely)

**Failure Modes:**
- ❌ Model initialization fails → Check API keys
- ❌ S3 access fails → Check AWS credentials
- ❌ Timeout → Increase timeout or reduce content
- ❌ Memory error → Reduce max_content_chars
- ❌ No recommendations → Check prompt/model

### Comparing Outputs Between Systems

**High-Context vs Standard:**
```python
def compare_systems(high_context_result, standard_result):
    """Compare outputs from both systems."""

    comparison = {
        'recommendations': {
            'high_context': len(high_context_result['recommendations']),
            'standard': len(standard_result['recommendations']),
            'overlap': calculate_overlap(
                high_context_result['recommendations'],
                standard_result['recommendations']
            )
        },
        'cost': {
            'high_context': high_context_result['cost']['total'],
            'standard': standard_result['cost']['total'],
            'savings': standard_result['cost']['total'] - high_context_result['cost']['total']
        },
        'time': {
            'high_context': high_context_result['analysis_duration_seconds'],
            'standard': standard_result['analysis_duration_seconds'],
            'speedup': standard_result['analysis_duration_seconds'] / high_context_result['analysis_duration_seconds']
        }
    }

    return comparison
```

### Quality Assessment Criteria

**Recommendation Quality Score:**
```python
def calculate_quality_score(recommendations):
    """Calculate quality score for recommendations."""

    scores = {
        'completeness': 0,
        'specificity': 0,
        'actionability': 0,
        'relevance': 0
    }

    for rec in recommendations:
        # Completeness: All required fields present
        if all(field in rec for field in ['title', 'description', 'priority', 'confidence']):
            scores['completeness'] += 1

        # Specificity: Description > 100 chars
        if len(rec['description']) > 100:
            scores['specificity'] += 1

        # Actionability: Has implementation guidance
        if 'implementation_effort' in rec or 'steps' in rec:
            scores['actionability'] += 1

        # Relevance: High confidence
        if rec['confidence'] >= 0.7:
            scores['relevance'] += 1

    # Normalize by recommendation count
    total = len(recommendations)
    return {k: v / total for k, v in scores.items()}
```

**Expected Quality Scores:**
- Completeness: > 0.95 (95%+ have all fields)
- Specificity: > 0.80 (80%+ have detailed descriptions)
- Actionability: > 0.60 (60%+ have implementation guidance)
- Relevance: > 0.75 (75%+ have high confidence)

---

## J. References

### Related Files and Their Purposes

**Core Implementation:**
- `scripts/high_context_book_analyzer.py` (1,033 lines)
  - Main analyzer implementation
  - Model integration (Gemini + Claude)
  - Consensus synthesis
  - Result formatting

- `synthesis/models/google_model_v2.py` (486 lines)
  - Gemini 1.5 Pro integration
  - Tiered pricing calculation
  - Token counting

- `synthesis/models/claude_model_v2.py` (398 lines)
  - Claude Sonnet 4 integration
  - Flat pricing calculation
  - Response parsing

**Integration Points:**
- `scripts/recursive_book_analysis.py` (line 1722)
  - `--high-context` flag integration
  - Fallback to standard system
  - Result aggregation

- `scripts/result_cache.py` (273 lines)
  - Cache management
  - Hit/miss tracking
  - Cache invalidation

**Configuration:**
- `workflow_config.yaml`
  - Project definitions
  - Technology stacks
  - README paths

- `secrets/secrets.yaml`
  - API keys (Gemini, Claude, AWS)
  - Project-specific secrets
  - Environment configs

**Testing:**
- `tests/integration/test_high_context_analyzer.py` (197 lines)
  - Integration test
  - End-to-end validation
  - Cost/time verification

- `tests/integration/test_high_context_local.py`
  - Local filesystem testing
  - PDF extraction testing
  - Error handling tests

**Documentation:**
- `docs/guides/HIGH_CONTEXT_QUICK_START.md` (364 lines)
  - Quick start guide (5 minutes)
  - Basic usage examples
  - Common pitfalls

- `docs/guides/HIGH_CONTEXT_ANALYSIS_GUIDE.md` (this file)
  - Comprehensive reference
  - Technical details
  - Advanced topics

- `high-context-book-analyzer.plan.md`
  - Original implementation plan
  - Architecture decisions
  - Development timeline

### API Documentation Links

**Google Gemini:**
- API Docs: https://ai.google.dev/docs
- Pricing: https://ai.google.dev/pricing
- Python Client: https://github.com/google/generative-ai-python

**Anthropic Claude:**
- API Docs: https://docs.anthropic.com/
- Pricing: https://www.anthropic.com/pricing
- Python SDK: https://github.com/anthropics/anthropic-sdk-python

**AWS S3:**
- boto3 Docs: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html
- S3 API Reference: https://docs.aws.amazon.com/s3/

### Configuration File Locations

**API Keys:**
```
secrets/secrets.yaml
  ├── global:
  │   ├── GOOGLE_AI_API_KEY
  │   └── ANTHROPIC_API_KEY
  └── projects:
      └── nba-mcp-synthesis:
          ├── AWS_ACCESS_KEY_ID
          └── AWS_SECRET_ACCESS_KEY
```

**Project Config:**
```
workflow_config.yaml
  └── projects:
      ├── name
      ├── path
      ├── description
      ├── readme_path
      └── key_technologies
```

**Cache Storage:**
```
cache/
  └── book_analysis/
      └── <hash>.json
```

### Existing Documentation Cross-References

**Quick Start Guide:**
- Location: `docs/guides/HIGH_CONTEXT_QUICK_START.md`
- Purpose: Get started in 5 minutes
- Audience: New users
- Content: Basic setup, simple examples, quick wins

**Analysis Guide (This Document):**
- Location: `docs/guides/HIGH_CONTEXT_ANALYSIS_GUIDE.md`
- Purpose: Comprehensive technical reference
- Audience: Advanced users, developers
- Content: Full architecture, troubleshooting, advanced topics

**Implementation Plan:**
- Location: `high-context-book-analyzer.plan.md`
- Purpose: Development roadmap
- Audience: Developers, project managers
- Content: Architecture decisions, timeline, acceptance criteria

**Related Guides:**
- `docs/guides/BOOK_DISCOVERY.md` - Finding and cataloging books
- `docs/guides/RECURSIVE_ANALYSIS.md` - Standard 4-model system
- `docs/guides/SYNTHESIS_WORKFLOW.md` - Phase 3 synthesis integration
- `docs/guides/PROJECT_AWARE_ANALYSIS.md` - Project context integration

---

## Appendix: Quick Reference

### Most Common Commands

```bash
# Basic analysis
python3 scripts/high_context_book_analyzer.py \
  --book-key "books/ML_Book.pdf" \
  --book-title "ML Book"

# With project context
python3 scripts/high_context_book_analyzer.py \
  --book-key "books/ML_Book.pdf" \
  --project-aware

# Integrated workflow
python3 scripts/recursive_book_analysis.py --high-context

# Run test
python3 tests/integration/test_high_context_analyzer.py
```

### Cost Quick Reference

| Book Size | Estimated Cost |
|-----------|---------------|
| Small (150k chars) | $0.15 |
| Medium (300k chars) | $0.30 |
| Large (600k chars) | $0.60 |
| Max (1M chars) | $0.70 |

### Troubleshooting Checklist

- ☐ API keys set correctly?
- ☐ AWS credentials configured?
- ☐ Running from project root?
- ☐ Python >= 3.10?
- ☐ All packages installed?
- ☐ S3 bucket accessible?
- ☐ Sufficient memory available?
- ☐ Network connection stable?

---

**Document Version:** 1.0
**Last Updated:** October 29, 2025
**Maintainer:** NBA MCP Synthesis Team
**Status:** ✅ Production Ready
